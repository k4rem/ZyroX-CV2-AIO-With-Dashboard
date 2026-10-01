"""CLS Ops alert outbox. The destination must belong to OPS_GUILD_ID."""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional

from sqlalchemy import func, select
from sqlalchemy.dialects.postgresql import insert as pg_insert

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
    async with session_scope() as session:
        if coalesce and incident_id is not None and kind != "open":
            latest = (
                await session.execute(
                    select(func.max(SecurityAlertOutbox.created_at)).where(
                        SecurityAlertOutbox.incident_id == incident_id,
                        SecurityAlertOutbox.status.in_(
                            [AlertStatus.PENDING.value, AlertStatus.DELIVERED.value]
                        ),
                    )
                )
            ).scalar_one_or_none()
            if latest is not None and (moment - latest).total_seconds() < PROPOSED_ALERT_COALESCE_S:
                return None
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
            incident_id = None
            bucket = int(moment.timestamp()) // PROPOSED_ALERT_CAP_WINDOW_S
            dedupe = f"alert:digest:{guild_id}:{bucket}"
            body = _redact({"kind": "digest", "guild_id": str(guild_id), "overflow": True})
        else:
            seq = int(recent or 0) + 1
            dedupe = f"alert:{incident_id}:{kind}:{seq}"
        row_id = uuid.uuid4()
        inserted = (
            await session.execute(
                pg_insert(SecurityAlertOutbox)
                .values(
                    id=row_id,
                    guild_id=guild_id,
                    incident_id=incident_id,
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
        return inserted


async def deliver_due(now: Optional[datetime] = None, *, sender=None) -> int:
    moment = now or _utcnow()
    deliver = sender if sender is not None else _sender
    delivered = 0
    async with session_scope() as session:
        rows = (
            await session.execute(
                select(SecurityAlertOutbox)
                .where(
                    SecurityAlertOutbox.status == AlertStatus.PENDING.value,
                    SecurityAlertOutbox.next_attempt_at <= moment,
                )
                .order_by(SecurityAlertOutbox.created_at.asc())
            )
        ).scalars().all()
        for row in rows:
            channel = None if deliver is None else await deliver.resolve()
            if not destination_is_valid(channel):
                row.status = AlertStatus.UNDELIVERABLE_NO_DESTINATION.value
                row.last_error = "ops security alert destination is missing or not in OPS_GUILD_ID"
                await _set_ops_health(session, int(row.guild_id), False)
                continue
            try:
                await deliver.send(channel, row.payload, allowed_mentions="none")
            except Exception as exc:  # noqa: BLE001
                row.attempts = int(row.attempts or 0) + 1
                row.last_error = str(exc)[:500]
                if row.attempts >= 5:
                    row.status = AlertStatus.FAILED.value
                else:
                    row.status = AlertStatus.PENDING.value
                    row.next_attempt_at = moment + backoff_delay(row.attempts)
                continue
            row.status = AlertStatus.DELIVERED.value
            row.delivered_at = moment
            row.last_error = None
            await _set_ops_health(session, int(row.guild_id), True)
            delivered += 1
    return delivered


async def _set_ops_health(session, guild_id: int, ok: bool) -> None:
    state = (
        await session.execute(select(SecurityGuildState).where(SecurityGuildState.guild_id == guild_id))
    ).scalar_one_or_none()
    if state is not None:
        state.ops_destination_ok = ok
        state.updated_at = datetime.now(timezone.utc)
