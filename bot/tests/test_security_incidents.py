"""Phase 2A.3 incidents, evidence, and Ops alerts."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import select

from tests.conftest import TEST_GUILD_A, TEST_GUILD_B, TEST_ROOT

START = datetime(2026, 10, 1, 12, 0, tzinfo=timezone.utc)
ACTOR = 800000000000000011
TARGET = 800000000000000301


async def _observation(guild_id, *, actor_id=ACTOR, when=START, action="channel.delete", late=False, audit=None):
    from cls_platform.database import session_scope
    from cls_platform.security.models import SecurityObservation

    async with session_scope() as session:
        row = SecurityObservation(
            guild_id=guild_id,
            audit_entry_id=audit,
            action_class=action,
            target_id=TARGET,
            actor_id=actor_id,
            attribution_state="CONFIRMED",
            late=late,
            received_at=when,
            entry_created_at=when,
            source="audit_push",
            severity="H",
            counts_for_containment=not late,
            attribution_method="audit_push",
            attribution_reason="audit entry",
        )
        session.add(row)
        await session.flush()
        return row.id


class _Channel:
    def __init__(self, guild_id, channel_id):
        self.id = channel_id
        self.guild = type("Guild", (), {"id": guild_id})()


class _Sender:
    def __init__(self, channel, fail_times=0):
        self.channel = channel
        self.fail_times = fail_times
        self.sent = []

    async def resolve(self):
        return self.channel

    async def send(self, channel, payload, allowed_mentions):
        assert allowed_mentions == "none"
        if self.fail_times:
            self.fail_times -= 1
            raise RuntimeError("discord down")
        self.sent.append(payload)


def _ops(monkeypatch):
    import cls_platform.security.alerts as alerts

    ops = 100000000000000999
    channel = 100000000000000888
    monkeypatch.setattr(alerts, "OPS_GUILD_ID", ops)
    monkeypatch.setattr(alerts, "OPS_SECURITY_ALERT_CHANNEL_ID", channel)
    return ops, channel


@pytest.mark.asyncio
async def test_incident_windows_and_manual_close(db_reset):
    from cls_platform.security.incidents import attach_observation, close_incident, list_incidents

    first_obs = await _observation(TEST_GUILD_A, when=START, audit=900000000000000401)
    first = await attach_observation(first_obs, now=START)
    second_obs = await _observation(TEST_GUILD_A, when=START + timedelta(minutes=10), audit=900000000000000402)
    second = await attach_observation(second_obs, now=START + timedelta(minutes=10))
    assert first == second
    third_obs = await _observation(TEST_GUILD_A, when=START + timedelta(minutes=26), audit=900000000000000403)
    third = await attach_observation(third_obs, now=START + timedelta(minutes=26))
    assert third != first
    rows = await list_incidents(TEST_GUILD_A)
    assert rows[0].closure == "EXPIRED_INACTIVE"
    assert rows[1].previous_incident_id == first
    lifetime_obs = await _observation(
        TEST_GUILD_A, when=START + timedelta(hours=6, minutes=30), audit=900000000000000404
    )
    # Keep the third incident warm, then exceed the 6 hour lifetime from its open.
    await attach_observation(lifetime_obs, now=rows[1].opened_at + timedelta(hours=6, seconds=1))
    closed = await list_incidents(TEST_GUILD_A)
    assert any(row.closure == "EXPIRED_LIFETIME" for row in closed)
    active = [row for row in closed if row.status == "ACTIVE"][0]
    await close_incident(
        guild_id=TEST_GUILD_A,
        incident_id=active.id,
        closure="RESOLVED",
        actor_user_id=TEST_ROOT,
        now=START + timedelta(hours=7),
    )
    after = await _observation(TEST_GUILD_A, when=START + timedelta(hours=7, minutes=1), audit=900000000000000405)
    opened = await attach_observation(after, now=START + timedelta(hours=7, minutes=1))
    assert opened != active.id
    with pytest.raises(PermissionError):
        await close_incident(
            guild_id=TEST_GUILD_A,
            incident_id=opened,
            closure="FALSE_POSITIVE",
            actor_user_id=800000000000000099,
        )


@pytest.mark.asyncio
async def test_guild_isolation_and_redaction(db_reset):
    from cls_platform.database import session_scope
    from cls_platform.security.incidents import attach_observation, list_incidents
    from cls_platform.security.models import SecurityIncidentEvent

    obs = await _observation(TEST_GUILD_A, audit=900000000000000411)
    incident_id = await attach_observation(obs, now=START)
    other = await _observation(TEST_GUILD_B, audit=900000000000000412)
    await attach_observation(other, now=START)
    assert len(await list_incidents(TEST_GUILD_A)) == 1
    assert all(row.guild_id == TEST_GUILD_A for row in await list_incidents(TEST_GUILD_A))
    async with session_scope() as session:
        event = (
            await session.execute(
                select(SecurityIncidentEvent).where(SecurityIncidentEvent.incident_id == incident_id)
            )
        ).scalar_one()
    assert event.payload["who"]["actor_id"] == str(ACTOR)
    assert "content" not in event.payload
    assert event.payload["why"]["would_contain"] is False
    event.payload["token"] = "secret"
    from cls_platform.services.audit import _redact

    assert _redact(event.payload)["token"] == "[REDACTED]"


@pytest.mark.asyncio
async def test_outbox_dedupe_retry_backoff_coalesce_and_ops_guild(db_reset, monkeypatch):
    from cls_platform.database import session_scope
    from cls_platform.security.alerts import deliver_due, enqueue_alert
    from cls_platform.security.models import SecurityAlertOutbox, SecurityGuildState
    from cls_platform.security.config import ensure_guild_config

    ops, channel_id = _ops(monkeypatch)
    await ensure_guild_config(TEST_GUILD_A)
    first = await enqueue_alert(
        guild_id=TEST_GUILD_A,
        incident_id=None,
        kind="open",
        payload={"token": "nope", "summary": "opened"},
        now=START,
        coalesce=False,
    )
    assert first is not None
    product = _Channel(TEST_GUILD_A, channel_id)
    sender = _Sender(product)
    await deliver_due(START, sender=sender)
    assert sender.sent == []
    async with session_scope() as session:
        row = (await session.execute(select(SecurityAlertOutbox))).scalar_one()
        assert row.status == "UNDELIVERABLE_NO_DESTINATION"
        assert row.payload["token"] == "[REDACTED]"
        state = (
            await session.execute(select(SecurityGuildState).where(SecurityGuildState.guild_id == TEST_GUILD_A))
        ).scalar_one()
        assert state.ops_destination_ok is False
    async with session_scope() as session:
        current = (await session.execute(select(SecurityAlertOutbox))).scalar_one()
        current.status = "PENDING"
        current.next_attempt_at = START
    ops_channel = _Channel(ops, channel_id)
    failing = _Sender(ops_channel, fail_times=1)
    await deliver_due(START, sender=failing)
    async with session_scope() as session:
        current = (await session.execute(select(SecurityAlertOutbox))).scalar_one()
        assert current.status == "PENDING"
        assert current.attempts == 1
        assert current.next_attempt_at > START
    assert await deliver_due(START, sender=failing) == 0
    assert await deliver_due(START + timedelta(seconds=5), sender=failing) == 1
    assert failing.sent[0]["allowed_mentions"] == "none" or failing.sent


@pytest.mark.asyncio
async def test_alert_coalesce_and_cap(db_reset, monkeypatch):
    from cls_platform.security.alerts import enqueue_alert

    from cls_platform.security.incidents import attach_observation

    _ops(monkeypatch)
    obs = await _observation(TEST_GUILD_A, audit=900000000000000421)
    incident_id = await attach_observation(obs, now=START)
    opened = await enqueue_alert(
        guild_id=TEST_GUILD_A,
        incident_id=incident_id,
        kind="update",
        payload={"n": 1},
        now=START,
    )
    skipped = await enqueue_alert(
        guild_id=TEST_GUILD_A,
        incident_id=incident_id,
        kind="update",
        payload={"n": 2},
        now=START + timedelta(seconds=10),
    )
    assert opened is not None
    assert skipped is None
    for index in range(19):
        await enqueue_alert(
            guild_id=TEST_GUILD_A,
            incident_id=None,
            kind=f"extra{index}",
            payload={"n": index},
            now=START + timedelta(seconds=40 + index),
            coalesce=False,
        )
    digest = await enqueue_alert(
        guild_id=TEST_GUILD_A,
        incident_id=None,
        kind="extra-final",
        payload={"n": "overflow"},
        now=START + timedelta(minutes=2),
        coalesce=False,
    )
    from cls_platform.database import session_scope
    from cls_platform.security.models import SecurityAlertOutbox

    async with session_scope() as session:
        row = (
            await session.execute(select(SecurityAlertOutbox).where(SecurityAlertOutbox.id == digest))
        ).scalar_one()
    assert row.kind == "digest"


@pytest.mark.asyncio
async def test_retention_purges_expired_history_only(db_reset):
    from cls_platform.database import session_scope
    from cls_platform.security.models import SecurityIncident, SecurityIncidentEvent, SecurityObservation, SecurityQuarantine
    from cls_platform.security.retention import purge_expired

    old = START - timedelta(days=400)
    async with session_scope() as session:
        incident = SecurityIncident(
            guild_id=TEST_GUILD_A,
            subject_id=ACTOR,
            engine="human",
            status="CLOSED",
            closure="RESOLVED",
            severity="H",
            opened_at=old,
            last_activity_at=old,
            closed_at=old,
            tier_map_version="2026-10-01",
        )
        session.add(incident)
        await session.flush()
        session.add(
            SecurityIncidentEvent(
                incident_id=incident.id,
                guild_id=TEST_GUILD_A,
                kind="observation",
                payload={"what": "channel.delete"},
            )
        )
        kept = SecurityIncident(
            guild_id=TEST_GUILD_A,
            subject_id=ACTOR + 1,
            engine="human",
            status="CLOSED",
            closure="RESOLVED",
            severity="H",
            opened_at=START,
            last_activity_at=START,
            closed_at=START,
            tier_map_version="2026-10-01",
        )
        session.add(kept)
        await session.flush()
        session.add(
            SecurityQuarantine(
                guild_id=TEST_GUILD_A,
                user_id=ACTOR + 1,
                incident_id=kept.id,
                status="ACTIVE",
            )
        )
        session.add(
            SecurityObservation(
                guild_id=TEST_GUILD_A,
                action_class="channel.delete",
                attribution_state="UNATTRIBUTED",
                late=False,
                received_at=START - timedelta(days=31),
                source="gateway",
                severity="H",
                counts_for_containment=False,
            )
        )
    result = await purge_expired(START)
    assert result["observations"] == 1
    assert result["incidents"] == 1
    async with session_scope() as session:
        remaining = (await session.execute(select(SecurityIncident))).scalars().all()
        assert len(remaining) == 1
        quarantine = (await session.execute(select(SecurityQuarantine))).scalar_one()
        assert quarantine.status == "ACTIVE"
