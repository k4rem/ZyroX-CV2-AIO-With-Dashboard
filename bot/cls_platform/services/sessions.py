"""Dashboard session persistence."""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional

from sqlalchemy import select, update

from cls_platform.database import session_scope
from cls_platform.models import DashboardSession


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


async def create_session(discord_user_id: int, ttl_hours: int = 168) -> uuid.UUID:
    now = _utcnow()
    expires = now + timedelta(hours=ttl_hours)
    row = DashboardSession(
        discord_user_id=discord_user_id,
        auth_time=now,
        last_seen_at=now,
        expires_at=expires,
    )
    async with session_scope() as session:
        session.add(row)
        await session.flush()
        return row.id


async def get_session(session_id: uuid.UUID) -> Optional[DashboardSession]:
    from cls_platform.database import get_session_factory

    factory = get_session_factory()
    async with factory() as session:
        result = await session.execute(
            select(DashboardSession).where(DashboardSession.id == session_id)
        )
        return result.scalar_one_or_none()


async def touch_session(session_id: uuid.UUID) -> None:
    async with session_scope() as session:
        await session.execute(
            update(DashboardSession)
            .where(DashboardSession.id == session_id)
            .values(last_seen_at=_utcnow())
        )


async def revoke_session(session_id: uuid.UUID, reason: str = "revoked") -> bool:
    async with session_scope() as session:
        result = await session.execute(
            select(DashboardSession).where(DashboardSession.id == session_id)
        )
        row = result.scalar_one_or_none()
        if not row or row.revoked_at:
            return False
        row.revoked_at = _utcnow()
        row.revoked_reason = reason[:255]
        return True


async def revoke_all_for_user(discord_user_id: int, reason: str = "logout") -> int:
    now = _utcnow()
    async with session_scope() as session:
        result = await session.execute(
            select(DashboardSession).where(
                DashboardSession.discord_user_id == discord_user_id,
                DashboardSession.revoked_at.is_(None),
            )
        )
        rows = list(result.scalars().all())
        for row in rows:
            row.revoked_at = now
            row.revoked_reason = reason[:255]
        return len(rows)


def session_is_valid(row: DashboardSession) -> bool:
    now = _utcnow()
    if row.revoked_at is not None:
        return False
    exp = row.expires_at
    if exp.tzinfo is None:
        exp = exp.replace(tzinfo=timezone.utc)
    return exp > now
