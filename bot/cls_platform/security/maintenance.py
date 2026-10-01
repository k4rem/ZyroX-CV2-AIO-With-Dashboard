"""Security maintenance windows. This is not Incident Mode."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from sqlalchemy import select

from cls_platform.database import session_scope
from cls_platform.security.alerts import enqueue_alert
from cls_platform.security.constants import MAINTENANCE_MAX_S
from cls_platform.security.models import SecurityMaintenanceWindow
from cls_platform.services.audit import record_audit
from cls_platform.services.grants import is_root_user


class MaintenanceRejected(PermissionError):
    pass


def _now(moment: datetime | None) -> datetime:
    current = moment or datetime.now(timezone.utc)
    if current.tzinfo is None:
        return current.replace(tzinfo=timezone.utc)
    return current


async def start_window(
    *,
    guild_id: int,
    actor_user_id: int,
    reason: str,
    duration_s: int,
    now: datetime | None = None,
) -> SecurityMaintenanceWindow:
    if not is_root_user(actor_user_id):
        raise MaintenanceRejected("security.maintenance.manage is Root only")
    if not reason.strip():
        raise MaintenanceRejected("a reason is required")
    if duration_s < 1 or duration_s > MAINTENANCE_MAX_S:
        raise MaintenanceRejected("maintenance windows are capped at 60 minutes")
    moment = _now(now)
    async with session_scope() as session:
        active = await _active(session, guild_id, moment)
        if active is not None:
            active.ended_at = moment
            active.end_reason = "replaced"
        row = SecurityMaintenanceWindow(
            guild_id=guild_id,
            started_by=actor_user_id,
            reason=reason.strip(),
            starts_at=moment,
            expires_at=moment + timedelta(seconds=duration_s),
        )
        session.add(row)
        await session.flush()
        window_id = row.id
    await record_audit(
        action="security.maintenance.start",
        actor_user_id=actor_user_id,
        guild_id=guild_id,
        target=str(window_id),
        after_state={"reason": reason.strip(), "duration_s": duration_s, "effective_mode": "OBSERVE"},
    )
    await enqueue_alert(
        guild_id=guild_id,
        incident_id=None,
        kind="maintenance",
        payload={"maintenance_window": True, "reason": reason.strip()},
        now=moment,
        coalesce=False,
    )
    async with session_scope() as session:
        return (
            await session.execute(
                select(SecurityMaintenanceWindow).where(SecurityMaintenanceWindow.id == window_id)
            )
        ).scalar_one()


async def active_window(guild_id: int, now: datetime | None = None) -> SecurityMaintenanceWindow | None:
    moment = _now(now)
    async with session_scope() as session:
        return await _active(session, guild_id, moment)


async def _active(session, guild_id: int, moment: datetime) -> SecurityMaintenanceWindow | None:
    row = (
        await session.execute(
            select(SecurityMaintenanceWindow).where(
                SecurityMaintenanceWindow.guild_id == guild_id,
                SecurityMaintenanceWindow.ended_at.is_(None),
            )
        )
    ).scalar_one_or_none()
    if row is None:
        return None
    if row.expires_at <= moment:
        row.ended_at = row.expires_at
        row.end_reason = "expired"
        return None
    return row
