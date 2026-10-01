"""Phase 2A.4.1 runtime wiring. These tests drive the listener, outbox, and scheduler."""

from __future__ import annotations

import asyncio
import uuid
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

import pytest
from sqlalchemy import select

from tests.conftest import TEST_GUILD_A, TEST_GUILD_B, TEST_ROOT
from tests.test_security_attribution import Clock, _entry

NOW = datetime(2026, 10, 1, 12, 0, tzinfo=timezone.utc)
ACTOR = 800000000000000011
OWNER = 800000000000000077
BOT_ID = 800000000000000050


class _Channel:
    def __init__(self, guild_id: int, channel_id: int):
        self.id = channel_id
        self.guild = SimpleNamespace(id=guild_id)


class _Sender:
    def __init__(self, channel, fail_times: int = 0):
        self.channel = channel
        self.fail_times = fail_times
        self.sent = []
        self.calls = 0

    async def resolve(self):
        return self.channel

    async def send(self, channel, payload, allowed_mentions="none"):
        self.calls += 1
        if self.fail_times:
            self.fail_times -= 1
            raise RuntimeError("discord unavailable")
        await asyncio.sleep(0.01)
        self.sent.append(payload)


def _ops(monkeypatch):
    ops = 100000000000000999
    channel_id = 100000000000000998
    import cls_platform.security.alerts as alerts

    monkeypatch.setattr(alerts, "OPS_GUILD_ID", ops)
    monkeypatch.setattr(alerts, "OPS_SECURITY_ALERT_CHANNEL_ID", channel_id)
    return ops, channel_id


@pytest.mark.asyncio
async def test_startup_seeds_delivery_and_sender_receives_alert(db_reset, monkeypatch):
    from cls_platform.scheduler_bootstrap import ensure_recurring_security_jobs, register_scheduler_handlers
    from cls_platform.security.alerts import enqueue_alert
    from cls_platform.services.scheduler import run_scheduler_tick

    ops, channel_id = _ops(monkeypatch)
    sender = _Sender(_Channel(ops, channel_id))
    register_scheduler_handlers(SimpleNamespace(get_guild=lambda guild_id: None, user=None))
    import cls_platform.security.alerts as alerts

    alerts.configure_alert_sender(sender)
    await ensure_recurring_security_jobs()
    await enqueue_alert(
        guild_id=TEST_GUILD_A,
        incident_id=None,
        kind="open",
        payload={"summary": "opened", "severity": "H"},
        now=datetime.now(timezone.utc) - timedelta(seconds=1),
        coalesce=False,
    )
    assert await run_scheduler_tick() >= 1
    assert sender.sent
    assert sender.sent[0]["summary"] == "opened"


@pytest.mark.asyncio
async def test_failed_send_retries_and_restart_resumes(db_reset, monkeypatch):
    from cls_platform.security.alerts import deliver_due, enqueue_alert

    ops, channel_id = _ops(monkeypatch)
    moment = datetime.now(timezone.utc)
    await enqueue_alert(
        guild_id=TEST_GUILD_A,
        incident_id=None,
        kind="open",
        payload={"summary": "retry-me"},
        now=moment,
        coalesce=False,
    )
    failing = _Sender(_Channel(ops, channel_id), fail_times=1)
    assert await deliver_due(moment, sender=failing) == 0
    assert await deliver_due(moment + timedelta(seconds=5), sender=failing) == 1
    assert failing.sent[0]["summary"] == "retry-me"


@pytest.mark.asyncio
async def test_overlapping_deliverers_send_once(db_reset, monkeypatch):
    from cls_platform.security.alerts import deliver_due, enqueue_alert

    ops, channel_id = _ops(monkeypatch)
    moment = datetime.now(timezone.utc)
    await enqueue_alert(
        guild_id=TEST_GUILD_A,
        incident_id=None,
        kind="open",
        payload={"summary": "once"},
        now=moment,
        coalesce=False,
    )
    sender = _Sender(_Channel(ops, channel_id))
    await asyncio.gather(
        deliver_due(moment, sender=sender),
        deliver_due(moment, sender=sender),
    )
    assert sender.calls == 1


@pytest.mark.asyncio
async def test_coalesce_keeps_would_contain_payload(db_reset, monkeypatch):
    from cls_platform.database import session_scope
    from cls_platform.security.alerts import enqueue_alert
    from cls_platform.security.models import SecurityAlertOutbox

    _ops(monkeypatch)
    incident = uuid.uuid4()
    from cls_platform.security.models import SecurityIncident

    async with session_scope() as session:
        session.add(
            SecurityIncident(
                id=incident,
                guild_id=TEST_GUILD_A,
                subject_id=ACTOR,
                engine="human",
                status="ACTIVE",
                severity="H",
                opened_at=NOW,
                last_activity_at=NOW,
                tier_map_version="2026-10-01",
            )
        )
    first = await enqueue_alert(
        guild_id=TEST_GUILD_A,
        incident_id=incident,
        kind="would_contain:channel.delete",
        payload={"rule_id": "channel.delete", "would_contain": True, "severity": "H", "subject_id": str(ACTOR)},
        now=NOW,
    )
    second = await enqueue_alert(
        guild_id=TEST_GUILD_A,
        incident_id=incident,
        kind="would_contain:channel.delete",
        payload={"rule_id": "channel.delete", "would_contain": True, "severity": "C", "n": 2},
        now=NOW + timedelta(seconds=5),
    )
    assert second == first
    async with session_scope() as session:
        row = (
            await session.execute(select(SecurityAlertOutbox).where(SecurityAlertOutbox.id == first))
        ).scalar_one()
    assert any(event.get("would_contain") is True for event in row.payload["events"])
    assert any(event.get("severity") == "C" for event in row.payload["events"])


@pytest.mark.asyncio
async def test_listener_permission_diff_and_ignored_rename(db_reset, monkeypatch):
    from cogs.security.protection import SecurityProtection
    from cls_platform.database import session_scope
    from cls_platform.security.models import SecurityObservation
    import cls_platform.security.feed as feed_mod
    import cogs.security.protection as protection_mod

    monkeypatch.setattr(protection_mod, "security_guild_eligible", lambda guild_id: int(guild_id) == TEST_GUILD_A)
    monkeypatch.setattr(feed_mod, "security_guild_eligible", lambda guild_id: int(guild_id) == TEST_GUILD_A)
    cog = SecurityProtection(SimpleNamespace(user=SimpleNamespace(id=1), guilds=[]))

    class Bits:
        def __init__(self, names):
            self.names = names

        def __iter__(self):
            return iter((name, True) for name in self.names)

    guild = SimpleNamespace(id=TEST_GUILD_A, me=None)
    rename = SimpleNamespace(
        guild=guild,
        id=900000000000000701,
        action=SimpleNamespace(name="role_update"),
        user=SimpleNamespace(id=ACTOR, bot=False),
        target=SimpleNamespace(id=700000000000000701, managed=False),
        before=SimpleNamespace(name="old"),
        after=SimpleNamespace(name="new", color=1),
        created_at=NOW,
        reason=None,
    )
    await cog.on_audit_log_entry_create(rename)
    grant = SimpleNamespace(
        guild=guild,
        id=900000000000000702,
        action=SimpleNamespace(name="role_update"),
        user=SimpleNamespace(id=ACTOR, bot=False),
        target=SimpleNamespace(id=TEST_GUILD_A, managed=False),
        before=SimpleNamespace(permissions=Bits([])),
        after=SimpleNamespace(permissions=Bits(["administrator"])),
        created_at=NOW,
        reason=None,
    )
    await cog.on_audit_log_entry_create(grant)
    async with session_scope() as session:
        rows = (await session.execute(select(SecurityObservation))).scalars().all()
    assert len(rows) == 1
    assert rows[0].permission_tier == "CRITICAL_CONTROL"
    assert rows[0].action_class == "role.permission_escalation"
    assert rows[0].target_id == TEST_GUILD_A


@pytest.mark.asyncio
async def test_targetless_push_watermark_and_mixed_age(db_reset, monkeypatch):
    from cls_platform.security.constants import PROPOSED_T_ATTR_S
    from cls_platform.security.feed import FetchPage, ObservationFeed
    from cls_platform.security.models import SecurityGatewaySignal, SecurityGuildState, SecurityObservation
    from cls_platform.database import session_scope
    import cls_platform.security.feed as feed_mod

    monkeypatch.setattr(feed_mod, "security_guild_eligible", lambda guild_id: True)
    clock = Clock()
    feed = ObservationFeed(clock=clock, sleep=clock.sleep, monotonic=clock.monotonic)
    await feed.ingest_audit(
        _entry(clock, action_class="member.prune", discord_action="member_prune", target_id=None, audit_entry_id=900000000000000801),
        guild_id=TEST_GUILD_A,
        source="audit_push",
    )
    async with session_scope() as session:
        prune = (await session.execute(select(SecurityObservation))).scalar_one()
    assert prune.attribution_state == "CONFIRMED"
    assert prune.counts_for_containment is False
    assert prune.actor_id == 800000000000000011
    old = clock.now - timedelta(seconds=PROPOSED_T_ATTR_S + 5)
    await feed.record_gateway_signal(
        guild_id=TEST_GUILD_A,
        action_class="channel.delete",
        target_id=700000000000000811,
        change_digest="old",
        discord_action="channel_delete",
        seen_at=old,
        schedule=False,
    )
    await feed.record_gateway_signal(
        guild_id=TEST_GUILD_A,
        action_class="channel.delete",
        target_id=700000000000000812,
        change_digest="new",
        discord_action="channel_delete",
        seen_at=clock.now,
        schedule=False,
    )
    from cls_platform.security.attribution import snowflake_from_time

    newer_audit = snowflake_from_time(clock.now) + 10_000
    await feed.ingest_audit(
        _entry(clock, audit_entry_id=newer_audit, target_id=700000000000000890),
        guild_id=TEST_GUILD_A,
        source="audit_push",
    )

    class Source:
        def __init__(self):
            self.calls = []

        async def fetch(self, guild_id, discord_action, *, after_id, limit):
            self.calls.append(after_id)
            return FetchPage(entries=[])

    source = Source()
    feed.source = source
    await feed.run_fallback(TEST_GUILD_A, "channel_delete")
    async with session_scope() as session:
        watermark = (
            await session.execute(select(SecurityGuildState.last_audit_entry_id).where(SecurityGuildState.guild_id == TEST_GUILD_A))
        ).scalar_one()
    assert int(watermark) == newer_audit
    expected_floor = snowflake_from_time(old - timedelta(seconds=15))
    assert source.calls
    assert all(after_id == expected_floor for after_id in source.calls)
    await feed.expire_pending(TEST_GUILD_A, "channel_delete", respect_age=True)
    async with session_scope() as session:
        signals = (await session.execute(select(SecurityGatewaySignal))).scalars().all()
    by_digest = {row.change_digest: row.state for row in signals}
    assert by_digest["old"] == "EXPIRED_UNATTRIBUTED"
    assert by_digest["new"] == "PENDING"
    await feed.resume_pending_after_restart()
    assert feed._tasks
    feed.cancel_tasks()
    assert not any(not task.done() for task in feed._tasks.values())


@pytest.mark.asyncio
async def test_owner_unknown_trust_and_bot_subject(db_reset, monkeypatch):
    from cls_platform.security.policy_engine import PolicyObservation, Subject, TrustSnapshot, evaluate, trust_covers
    from cls_platform.security.trust import TrustRejected, grant_trust

    items = [
        PolicyObservation(
            id=f"o{index}",
            guild_id=TEST_GUILD_A,
            action_class="channel.delete",
            audit_entry_id=900000000000000900 + index,
            target_id=700000000000000900 + index,
            actor_id=ACTOR,
            attribution_state="CONFIRMED",
            late=False,
            at=NOW,
        )
        for index in range(3)
    ]
    unknown = evaluate(
        Subject(guild_id=TEST_GUILD_A, user_id=ACTOR, owner_known=False),
        items,
        None,
        TrustSnapshot(),
        NOW,
    )
    assert unknown
    assert all(item.would_contain is False and item.suppression_reason == "owner_unknown" for item in unknown)
    assert trust_covers(("channel.delete",), "channel.delete") is True
    assert trust_covers(("channel.delete",), "aggregate.destructive") is False
    assert trust_covers(("*",), "aggregate.destructive") is True
    assert trust_covers((), "channel.delete") is False
    with pytest.raises(TrustRejected):
        await grant_trust(
            guild_id=TEST_GUILD_A,
            subject_id=ACTOR,
            kind="human",
            scopes=[],
            actor_user_id=TEST_ROOT,
        )
    from cls_platform.security.feed import ObservationFeed
    from cls_platform.security.models import SecurityIncident
    from cls_platform.database import session_scope
    import cls_platform.security.feed as feed_mod

    monkeypatch.setattr(feed_mod, "security_guild_eligible", lambda guild_id: True)
    feed = ObservationFeed(clock=Clock(), sleep=Clock().sleep, monotonic=lambda: 0)
    await feed.ingest_audit(
        _entry(
            Clock(),
            action_class="bot.add",
            discord_action="bot_add",
            actor_id=ACTOR,
            target_id=BOT_ID,
            audit_entry_id=900000000000000950,
        ),
        guild_id=TEST_GUILD_A,
        source="audit_push",
    )
    async with session_scope() as session:
        incident = (await session.execute(select(SecurityIncident))).scalars().all()
    bot_incidents = [row for row in incident if row.engine == "bot"]
    assert bot_incidents
    assert bot_incidents[0].subject_id == BOT_ID


@pytest.mark.asyncio
async def test_off_mode_does_not_store_would_contain_and_observe_does(db_reset, monkeypatch):
    from cls_platform.database import session_scope
    from cls_platform.security.config import ensure_guild_config, set_subsystem_mode
    from cls_platform.security.feed import ObservationFeed
    from cls_platform.security.models import SecurityResponseAction
    from cls_platform.security.owners import remember_guild_owner
    import cls_platform.security.feed as feed_mod

    monkeypatch.setattr(feed_mod, "security_guild_eligible", lambda guild_id: int(guild_id) == TEST_GUILD_A)
    await remember_guild_owner(TEST_GUILD_A, OWNER)
    config = await ensure_guild_config(TEST_GUILD_A)
    await set_subsystem_mode(guild_id=TEST_GUILD_A, subsystem="human", mode="OFF", expected_version=config.version)
    clock = Clock()
    feed = ObservationFeed(clock=clock, sleep=clock.sleep, monotonic=clock.monotonic)
    feed.guild_owners[TEST_GUILD_A] = OWNER
    for index in range(3):
        clock.now += timedelta(seconds=1)
        await feed.ingest_audit(
            _entry(clock, audit_entry_id=900000000000000960 + index, target_id=700000000000000960 + index, entry_created_at=clock.now),
            guild_id=TEST_GUILD_A,
            received_at=clock.now,
        )
    async with session_scope() as session:
        assert (await session.execute(select(SecurityResponseAction))).scalars().all() == []
    from cls_platform.security.models import SecurityGuildConfig

    async with session_scope() as session:
        version = (
            await session.execute(
                select(SecurityGuildConfig.version).where(SecurityGuildConfig.guild_id == TEST_GUILD_A)
            )
        ).scalar_one()
    await set_subsystem_mode(guild_id=TEST_GUILD_A, subsystem="human", mode="OBSERVE", expected_version=int(version))
    for index in range(3, 6):
        clock.now += timedelta(seconds=1)
        await feed.ingest_audit(
            _entry(clock, audit_entry_id=900000000000000960 + index, target_id=700000000000000960 + index, entry_created_at=clock.now),
            guild_id=TEST_GUILD_A,
            received_at=clock.now,
        )
    async with session_scope() as session:
        rows = (await session.execute(select(SecurityResponseAction))).scalars().all()
    assert rows
    assert all(row.outcome == "WOULD_CONTAIN" and row.discord_mutation is False for row in rows)


@pytest.mark.asyncio
async def test_concurrent_incident_attach_and_self_ignores_would_contain(db_reset, monkeypatch):
    from cls_platform.database import session_scope
    from cls_platform.security.feed import ObservationFeed
    from cls_platform.security.models import SecurityIncident, SecurityObservation, SecurityResponseAction
    import cls_platform.security.feed as feed_mod

    monkeypatch.setattr(feed_mod, "security_guild_eligible", lambda guild_id: True)
    clock = Clock()
    feed = ObservationFeed(clock=clock, sleep=clock.sleep, monotonic=clock.monotonic)
    feed.cls_user_id = ACTOR
    async with session_scope() as session:
        session.add(
            SecurityResponseAction(
                guild_id=TEST_GUILD_A,
                incident_id=None,
                subject_id=700000000000000971,
                idempotency_key="would-not-self",
                outcome="WOULD_CONTAIN",
                effective_mode="OBSERVE",
                discord_mutation=False,
                reason_token="CLS-SEC abc",
                ledger_action_class="channel.delete",
                rule_id="channel.delete",
            )
        )
    obs = await feed.ingest_audit(
        _entry(
            clock,
            actor_id=ACTOR,
            target_id=700000000000000971,
            audit_entry_id=900000000000000971,
            reason_token="CLS-SEC abc",
        ),
        guild_id=TEST_GUILD_A,
        source="audit_push",
    )
    async with session_scope() as session:
        row = (
            await session.execute(select(SecurityObservation).where(SecurityObservation.id == obs))
        ).scalar_one()
    assert row.attribution_state == "CLS_PROXIED"
    ids = []
    for index in range(2):
        ids.append(
            await feed.ingest_audit(
                _entry(
                    clock,
                    actor_id=800000000000000033,
                    audit_entry_id=900000000000000980 + index,
                    target_id=700000000000000980 + index,
                ),
                guild_id=TEST_GUILD_B,
                source="audit_push",
            )
        )
    from cls_platform.security.incidents import attach_observation

    async with session_scope() as session:
        for obs_id in ids:
            current = (
                await session.execute(select(SecurityObservation).where(SecurityObservation.id == obs_id))
            ).scalar_one()
            current.incident_id = None
    await asyncio.gather(*(attach_observation(obs_id, now=clock.now) for obs_id in ids))
    async with session_scope() as session:
        linked = (
            await session.execute(
                select(SecurityObservation.incident_id).where(SecurityObservation.id.in_(ids))
            )
        ).scalars().all()
        incidents = (await session.execute(select(SecurityIncident).where(SecurityIncident.guild_id == TEST_GUILD_B))).scalars().all()
    assert all(item is not None for item in linked)
    assert len({item for item in linked}) == 1
    assert len(incidents) == 1


def test_malformed_allowlist_does_not_leave(monkeypatch):
    from cls_platform.security import allowlist_sweep as sweep

    class Guild:
        def __init__(self):
            self.id = 100000000000000777
            self.left = False

        async def leave(self):
            self.left = True

    guild = Guild()

    class Bot:
        guilds = [guild]

    monkeypatch.setenv("ALLOWED_GUILD_IDS", "not-a-snowflake")
    monkeypatch.setenv("ALLOW_EMPTY_GUILD_ALLOWLIST", "false")
    previous = sweep.ALLOWLIST_ENFORCED
    sweep.ALLOWLIST_ENFORCED = True
    try:
        left = asyncio.run(sweep.sweep_non_allowlisted_guilds(Bot()))
    finally:
        sweep.ALLOWLIST_ENFORCED = previous
    assert left == []
    assert guild.left is False
