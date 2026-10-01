"""Phase 2A.4 OBSERVE policy engines. The clock is injected."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from tests.conftest import TEST_GUILD_A, TEST_ROOT

NOW = datetime(2026, 10, 1, 12, 0, tzinfo=timezone.utc)
GUILD = 100000000000000100
OTHER = 100000000000000200
ACTOR = 800000000000000011
BOT = 800000000000000050


def _obs(index, action, **overrides):
    from cls_platform.security.policy_engine import PolicyObservation

    payload = dict(
        id=f"obs-{index}",
        guild_id=GUILD,
        action_class=action,
        audit_entry_id=900000000000000000 + index,
        target_id=700000000000000000 + index,
        actor_id=ACTOR,
        attribution_state="CONFIRMED",
        late=False,
        at=NOW - timedelta(seconds=index),
        permission_tier=None,
        everyone_grant=False,
    )
    payload.update(overrides)
    return PolicyObservation(**payload)


def _run(items, **kwargs):
    from cls_platform.security.policy_engine import Subject, TrustSnapshot, evaluate

    subject = kwargs.pop(
        "subject",
        Subject(guild_id=GUILD, user_id=kwargs.pop("user_id", ACTOR), is_bot=kwargs.pop("is_bot", False),
                is_guild_owner=kwargs.pop("owner", False), is_root=kwargs.pop("root", False)),
    )
    trust = kwargs.pop("trust", TrustSnapshot())
    return evaluate(subject, items, None, trust, kwargs.pop("now", NOW), maintenance_active=kwargs.pop("maintenance", False))


def _by_rule(decisions, rule_id):
    return [item for item in decisions if item.rule_id == rule_id]


def test_thresholds_aggregate_sequence_and_distinct_targets():
    below = _run([_obs(1, "channel.delete"), _obs(2, "channel.delete")])
    assert _by_rule(below, "channel.delete") == []
    at = _run([_obs(1, "channel.delete"), _obs(2, "channel.delete"), _obs(3, "channel.delete")])
    hit = _by_rule(at, "channel.delete")[0]
    assert hit.would_contain is True
    assert hit.replayable is False
    assert hit.effective_mode == "OBSERVE"
    assert "Development proposal" in hit.explanation
    same_target = _run([
        _obs(1, "channel.delete", target_id=1),
        _obs(2, "channel.delete", target_id=1),
        _obs(3, "channel.delete", target_id=1),
    ])
    assert _by_rule(same_target, "channel.delete") == []
    classes = ["channel.delete", "role.delete", "member.ban", "member.kick", "webhook.create", "channel.delete"]
    aggregate = _run([_obs(index, action) for index, action in enumerate(classes, start=1)])
    assert _by_rule(aggregate, "aggregate.destructive")[0].would_contain is True
    sequence = _run([
        _obs(1, "role.permission_escalation", permission_tier="CRITICAL_CONTROL", at=NOW - timedelta(seconds=30)),
        _obs(2, "channel.delete", at=NOW),
    ])
    assert _by_rule(sequence, "sequence.self_escalation")[0].would_contain is True


def test_trust_root_owner_and_revocation():
    from cls_platform.security.policy_engine import TrustSnapshot

    items = [_obs(1, "channel.delete"), _obs(2, "channel.delete"), _obs(3, "channel.delete")]
    trusted = _run(items, trust=TrustSnapshot(trusted=True, scopes=("channel.delete",)))
    assert _by_rule(trusted, "channel.delete")[0].would_contain is False
    assert _by_rule(trusted, "channel.delete")[0].suppression_reason == "trusted"
    revoked = _run(items, trust=TrustSnapshot(trusted=False, scopes=("channel.delete",)))
    assert _by_rule(revoked, "channel.delete")[0].would_contain is True
    assert _by_rule(_run(items, root=True), "channel.delete")[0].suppression_reason == "root"
    assert _by_rule(_run(items, owner=True), "channel.delete")[0].suppression_reason == "guild_owner"


def test_late_probable_ambiguous_and_unattributed_never_contain():
    late = _run([
        _obs(1, "channel.delete"),
        _obs(2, "channel.delete"),
        _obs(3, "channel.delete", late=True),
    ])
    decision = _by_rule(late, "channel.delete")[0]
    assert decision.would_contain is False
    assert decision.late_excluded is True
    for state in ("PROBABLE", "AMBIGUOUS", "UNATTRIBUTED"):
        items = [_obs(index, "channel.delete", attribution_state=state, audit_entry_id=None) for index in range(1, 4)]
        assert all(item.would_contain is False for item in _run(items))


def test_single_action_tiers_and_prune():
    everyone = _run([
        _obs(1, "role.permission_escalation", permission_tier="CRITICAL_CONTROL", everyone_grant=True, target_id=GUILD)
    ])
    assert _by_rule(everyone, "single.everyone_critical_control")[0].would_contain is True
    other_grant = _run([
        _obs(1, "role.permission_escalation", permission_tier="CRITICAL_CONTROL", everyone_grant=False)
    ])
    assert _by_rule(other_grant, "single.critical_control_grant")[0].would_contain is False
    prune = _run([_obs(1, "member.prune")])
    assert _by_rule(prune, "member.prune")[0].would_contain is False
    assert _by_rule(prune, "member.prune")[0].severity == "C"
    elevated = _run([_obs(1, "role.permission_escalation", permission_tier="ELEVATED")])
    assert _by_rule(elevated, "tier.elevated")[0].would_contain is False
    audit_view = _run([_obs(1, "role.permission_escalation", permission_tier="OBSERVABILITY")])
    assert _by_rule(audit_view, "tier.observability")[0].would_contain is False
    assert _by_rule(audit_view, "tier.observability")[0].containment_eligible is False


def test_bot_add_alerts_and_later_destruction_would_contain():
    from cls_platform.security.bot_engine import evaluate_bot
    from cls_platform.security.policy_engine import Subject, TrustSnapshot, executable_decisions

    added = evaluate_bot(
        Subject(guild_id=GUILD, user_id=BOT, is_bot=True),
        [_obs(1, "bot.add", actor_id=ACTOR, target_id=BOT, permission_tier="CRITICAL_CONTROL")],
        TrustSnapshot(),
        NOW,
    )
    assert added[0].rule_id == "bot.add"
    assert added[0].would_contain is False
    assert added[0].severity == "C"
    human = _run([_obs(1, "bot.add", actor_id=ACTOR, target_id=BOT)])
    assert all(item.rule_id != "channel.delete" for item in human)
    destructive = evaluate_bot(
        Subject(guild_id=GUILD, user_id=BOT, is_bot=True),
        [_obs(index, "channel.delete", actor_id=BOT) for index in range(1, 4)],
        TrustSnapshot(),
        NOW,
    )
    hit = _by_rule(destructive, "channel.delete")[0]
    assert hit.would_contain is True
    assert executable_decisions(destructive) == []


def test_two_guilds_do_not_share_counts():
    foreign = [_obs(index, "channel.delete", guild_id=OTHER) for index in range(1, 4)]
    assert _by_rule(_run(foreign), "channel.delete") == []


def test_enforce_mode_is_not_effective_and_maintenance_drops_to_observe():
    from cls_platform.security.policy_engine import effective_mode

    assert effective_mode("ENFORCE", maintenance_active=False) == "OBSERVE"
    assert effective_mode("OBSERVE", maintenance_active=True) == "OBSERVE"
    assert effective_mode("OFF", maintenance_active=True) == "OFF"
    items = [_obs(1, "channel.delete"), _obs(2, "channel.delete"), _obs(3, "channel.delete")]
    assert _by_rule(_run(items, maintenance=True), "channel.delete")[0].would_contain is True
    assert _by_rule(_run(items, maintenance=True), "channel.delete")[0].effective_mode == "OBSERVE"


@pytest.mark.asyncio
async def test_maintenance_window_is_root_only_and_expires(db_reset):
    from cls_platform.security.maintenance import MaintenanceRejected, active_window, start_window

    with pytest.raises(MaintenanceRejected):
        await start_window(
            guild_id=TEST_GUILD_A,
            actor_user_id=800000000000000099,
            reason="cleanup",
            duration_s=600,
            now=NOW,
        )
    with pytest.raises(MaintenanceRejected):
        await start_window(
            guild_id=TEST_GUILD_A,
            actor_user_id=TEST_ROOT,
            reason="too long",
            duration_s=61 * 60,
            now=NOW,
        )
    window = await start_window(
        guild_id=TEST_GUILD_A,
        actor_user_id=TEST_ROOT,
        reason="planned work",
        duration_s=600,
        now=NOW,
    )
    assert await active_window(TEST_GUILD_A, NOW + timedelta(minutes=5)) is not None
    assert await active_window(TEST_GUILD_A, window.expires_at) is None


@pytest.mark.asyncio
async def test_observe_would_contain_row_is_not_executable(db_reset):
    from sqlalchemy import select

    from cls_platform.database import session_scope
    from cls_platform.security.models import SecurityResponseAction

    async with session_scope() as session:
        session.add(
            SecurityResponseAction(
                guild_id=GUILD,
                idempotency_key="observe-decision-1",
                outcome="WOULD_CONTAIN",
                effective_mode="OBSERVE",
                discord_mutation=False,
                rule_id="channel.delete",
                explanation="development proposal",
            )
        )
    async with session_scope() as session:
        executable = (
            await session.execute(
                select(SecurityResponseAction).where(
                    SecurityResponseAction.guild_id == GUILD,
                    SecurityResponseAction.discord_mutation.is_(True),
                    SecurityResponseAction.effective_mode == "ENFORCE",
                )
            )
        ).scalars().all()
    assert executable == []


@pytest.mark.asyncio
async def test_live_path_records_would_contain_without_mutation(db_reset, monkeypatch):
    from sqlalchemy import select

    from cls_platform.database import session_scope
    from cls_platform.security.feed import ObservationFeed
    from cls_platform.security.models import SecurityResponseAction
    from tests.test_security_attribution import Clock, _entry

    import cls_platform.security.feed as feed_mod

    monkeypatch.setattr(feed_mod, "security_guild_eligible", lambda guild_id: int(guild_id) == GUILD)
    from cls_platform.security.owners import remember_guild_owner

    await remember_guild_owner(GUILD, 800000000000000099)
    clock = Clock()
    feed = ObservationFeed(clock=clock, sleep=clock.sleep, monotonic=clock.monotonic)
    feed.guild_owners[GUILD] = 800000000000000099
    for index, target in enumerate((700000000000000001, 700000000000000002, 700000000000000003), start=1):
        clock.now += timedelta(seconds=1)
        await feed.ingest_audit(
            _entry(
                clock,
                audit_entry_id=900000000000000500 + index,
                target_id=target,
                actor_id=ACTOR,
                entry_created_at=clock.now,
            ),
            guild_id=GUILD,
            received_at=clock.now,
        )
    async with session_scope() as session:
        rows = (await session.execute(select(SecurityResponseAction))).scalars().all()
    assert rows
    assert all(row.outcome == "WOULD_CONTAIN" and row.discord_mutation is False for row in rows)
    assert all(row.effective_mode == "OBSERVE" for row in rows)
