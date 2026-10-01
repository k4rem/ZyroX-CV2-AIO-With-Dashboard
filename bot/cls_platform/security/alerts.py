"""CLS Ops alert outbox. The destination must belong to OPS_GUILD_ID."""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional

from sqlalchemy import func, select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.orm.attributes import flag_modified

from cls_platform.config import OPS_GUILD_ID, OPS_SECURITY_ALERT_CHANNEL_ID
from cls_platform.database import session_scope
from cls_platform.security.constants import (
    PROPOSED_ALERT_CAP_WINDOW_S,
    PROPOSED_ALERT_COALESCE_S,
    PROPOSED_ALERT_GUILD_CAP,
    AlertStatus,
)
from cls_platform.security.models import SecurityAlertOutbox, SecurityGuildState
from cls_platform.services.audit import _redact
from cls_platform.services.scheduler import backoff_delay

_sender = None
_CLAIM_LEASE = timedelta(seconds=60)
_RETRYABLE = (AlertStatus.PENDING.value, AlertStatus.DEGRADED.value)


class InvalidOpsDestination(RuntimeError):
    pass


def configure_alert_sender(sender) -> None:
    global _sender
    _sender = sender


def destination_is_valid(channel) -> bool:
    """True only when the channel exists inside OPS_GUILD_ID and matches the configured id."""
    if channel is None or OPS_GUILD_ID is None or OPS_SECURITY_ALERT_CHANNEL_ID is None:
        return False
    guild = getattr(channel, "guild", None)
    if guild is None or int(guild.id) != int(OPS_GUILD_ID):
        return False
    if int(channel.id) != int(OPS_SECURITY_ALERT_CHANNEL_ID):
        return False
    return True


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _event(kind: str, body: dict, moment: datetime) -> dict:
    stored = {key: value for key, value in body.items() if key != "events"}
    return {
        "kind": kind,
        "at": moment.isoformat(),
        "incident_id": body.get("incident_id"),
        "guild_id": body.get("guild_id"),
        "subject_id": body.get("subject_id"),
        "attribution_state": body.get("attribution_state"),
        "rule_id": body.get("rule_id"),
        "severity": body.get("severity"),
        "would_contain": body.get("would_contain"),
        "summary": body.get("explanation") or body.get("summary"),
        "payload": stored,
    }


async def enqueue_alert(
    *,
    guild_id: int,
    incident_id: Optional[uuid.UUID],
    kind: str,
    payload: dict,
    now: Optional[datetime] = None,
    coalesce: bool = True,
) -> Optional[uuid.UUID]:
    moment = now or _utcnow()
    body = _redact(dict(payload))
    body.setdefault("allowed_mentions", "none")
    body.setdefault("guild_id", str(guild_id))
    if incident_id is not None:
        body.setdefault("incident_id", str(incident_id))
    async with session_scope() as session:
        if coalesce and incident_id is not None and kind != "open":
            latest = (
                await session.execute(
                    select(SecurityAlertOutbox)
                    .where(
                        SecurityAlertOutbox.incident_id == incident_id,
                        SecurityAlertOutbox.status.in_(_RETRYABLE),
                        SecurityAlertOutbox.created_at >= moment - timedelta(seconds=PROPOSED_ALERT_COALESCE_S),
                    )
                    .order_by(SecurityAlertOutbox.created_at.desc())
                    .with_for_update()
                )
            ).scalars().first()
            if latest is not None:
                merged = dict(latest.payload or {})
                events = list(merged.get("events") or [])
                if not events:
                    events.append(_event(latest.kind, merged, latest.created_at))
                events.append(_event(kind, body, moment))
                merged["events"] = events
                merged["allowed_mentions"] = "none"
                latest.payload = merged
                flag_modified(latest, "payload")
                return latest.id
        recent = (
            await session.execute(
                select(func.count())
                .select_from(SecurityAlertOutbox)
                .where(
                    SecurityAlertOutbox.guild_id == guild_id,
                    SecurityAlertOutbox.created_at >= moment - timedelta(seconds=PROPOSED_ALERT_CAP_WINDOW_S),
                    SecurityAlertOutbox.kind != "digest",
                )
            )
        ).scalar_one()
        if int(recent or 0) >= PROPOSED_ALERT_GUILD_CAP:
            kind = "digest"
            bucket = int(moment.timestamp()) // PROPOSED_ALERT_CAP_WINDOW_S
            dedupe = f"alert:digest:{guild_id}:{bucket}"
            body = _redact(
                {
                    "kind": "digest",
                    "guild_id": str(guild_id),
                    "overflow": True,
                    "allowed_mentions": "none",
                    "events": [_event(str(payload.get("kind") or "overflow"), body, moment)],
                }
            )
        else:
            seq = int(recent or 0) + 1
            dedupe = f"alert:{incident_id}:{kind}:{seq}:{uuid.uuid4()}"
        row_id = uuid.uuid4()
        inserted = (
            await session.execute(
                pg_insert(SecurityAlertOutbox)
                .values(
                    id=row_id,
                    guild_id=guild_id,
                    incident_id=incident_id if kind != "digest" else None,
                    dedupe_key=dedupe,
                    kind=kind,
                    status=AlertStatus.PENDING.value,
                    attempts=0,
                    next_attempt_at=moment,
                    payload=body,
                    created_at=moment,
                )
                .on_conflict_do_nothing(index_elements=["dedupe_key"])
                .returning(SecurityAlertOutbox.id)
            )
        ).scalar_one_or_none()
        if inserted is not None:
            return inserted
        existing = (
            await session.execute(
                select(SecurityAlertOutbox).where(SecurityAlertOutbox.dedupe_key == dedupe).with_for_update()
            )
        ).scalar_one()
        merged = dict(existing.payload or {})
        events = list(merged.get("events") or [])
        events.append(_event(kind, body, moment))
        merged["events"] = events
        existing.payload = merged
        flag_modified(existing, "payload")
        if existing.status == AlertStatus.DELIVERED.value:
            existing.status = AlertStatus.PENDING.value
            existing.next_attempt_at = moment
        return existing.id


async def deliver_due(now: Optional[datetime] = None, *, sender=None) -> int:
    """Claim due rows, commit, then send. A second worker cannot send the same row."""
    moment = now or _utcnow()
    deliver = sender if sender is not None else _sender
    claimed: list[tuple[uuid.UUID, int, int]] = []
    async with session_scope() as session:
        rows = (
            await session.execute(
                select(SecurityAlertOutbox)
                .where(
                    SecurityAlertOutbox.status.in_(_RETRYABLE + (AlertStatus.CLAIMED.value,)),
                    SecurityAlertOutbox.next_attempt_at <= moment,
                )
                .order_by(SecurityAlertOutbox.created_at.asc())
                .with_for_update(skip_locked=True)
            )
        ).scalars().all()
        for row in rows:
            row.status = AlertStatus.CLAIMED.value
            row.next_attempt_at = moment + _CLAIM_LEASE
            claimed.append((row.id, int(row.guild_id), int(row.attempts or 0)))
    delivered = 0
    for row_id, guild_id, attempts in claimed:
        outcome = "degraded"
        error = "ops security alert destination is missing or not in OPS_GUILD_ID"
        try:
            channel = None if deliver is None else await deliver.resolve()
            if destination_is_valid(channel):
                async with session_scope() as session:
                    payload = (
                        await session.execute(
                            select(SecurityAlertOutbox.payload).where(SecurityAlertOutbox.id == row_id)
                        )
                    ).scalar_one()
                await deliver.send(channel, payload, allowed_mentions="none")
                outcome = "delivered"
                error = None
        except Exception as exc:  # noqa: BLE001
            outcome = "retry"
            error = str(exc)[:500]
        async with session_scope() as session:
            row = (
                await session.execute(
                    select(SecurityAlertOutbox).where(SecurityAlertOutbox.id == row_id).with_for_update()
                )
            ).scalar_one()
            if outcome == "delivered":
                row.status = AlertStatus.DELIVERED.value
                row.delivered_at = moment
                row.last_error = None
                await _set_ops_health(session, guild_id, True)
                delivered += 1
                continue
            if outcome == "degraded":
                row.status = AlertStatus.DEGRADED.value
                row.last_error = error
                row.next_attempt_at = moment + backoff_delay(1)
                await _set_ops_health(session, guild_id, False)
                continue
            row.attempts = attempts + 1
            row.last_error = error
            if row.attempts >= 5:
                row.status = AlertStatus.FAILED.value
            else:
                row.status = AlertStatus.PENDING.value
                row.next_attempt_at = moment + backoff_delay(row.attempts)
    return delivered


async def _set_ops_health(session, guild_id: int, ok: bool) -> None:
    state = (
        await session.execute(select(SecurityGuildState).where(SecurityGuildState.guild_id == guild_id))
    ).scalar_one_or_none()
    if state is not None:
        state.ops_destination_ok = ok
        state.updated_at = datetime.now(timezone.utc)
