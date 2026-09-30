"""Dashboard grants and capability resolution."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from cls_platform.capabilities import ROOT_ONLY
from cls_platform.config import ROOT_OWNER_ID
from cls_platform.database import session_scope
from cls_platform.models import DashboardGrant, DashboardRole


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def is_root_user(discord_user_id: int) -> bool:
    return ROOT_OWNER_ID is not None and discord_user_id == ROOT_OWNER_ID


async def get_active_grant(guild_id: int, discord_user_id: int) -> Optional[DashboardGrant]:
    async with session_scope() as session:
        result = await session.execute(
            select(DashboardGrant)
            .options(selectinload(DashboardGrant.role))
            .where(
                DashboardGrant.guild_id == guild_id,
                DashboardGrant.discord_user_id == discord_user_id,
                DashboardGrant.revoked_at.is_(None),
            )
            .order_by(DashboardGrant.created_at.desc())
        )
        return result.scalars().first()


async def list_grants_for_guild(guild_id: int) -> list[DashboardGrant]:
    async with session_scope() as session:
        result = await session.execute(
            select(DashboardGrant)
            .options(selectinload(DashboardGrant.role))
            .where(DashboardGrant.guild_id == guild_id, DashboardGrant.revoked_at.is_(None))
        )
        return list(result.scalars().all())


async def list_grants_for_user(discord_user_id: int) -> list[DashboardGrant]:
    async with session_scope() as session:
        result = await session.execute(
            select(DashboardGrant)
            .options(selectinload(DashboardGrant.role))
            .where(
                DashboardGrant.discord_user_id == discord_user_id,
                DashboardGrant.revoked_at.is_(None),
            )
        )
        return list(result.scalars().all())


async def user_capabilities(guild_id: int, discord_user_id: int) -> set[str]:
    if is_root_user(discord_user_id):
        return {c for c in _all_assignable_caps()}
    grant = await get_active_grant(guild_id, discord_user_id)
    if not grant or not grant.role:
        return set()
    return set(grant.role.capabilities or [])


def _all_assignable_caps() -> set[str]:
    from cls_platform.capabilities import ALL_CAPABILITIES

    return {c for c in ALL_CAPABILITIES if c not in ROOT_ONLY} | {"rbac.manage"}


async def user_has_capability(guild_id: int, discord_user_id: int, capability: str) -> bool:
    if capability in ROOT_ONLY and not is_root_user(discord_user_id):
        return False
    caps = await user_capabilities(guild_id, discord_user_id)
    if is_root_user(discord_user_id):
        return True
    return capability in caps


async def create_grant(
    guild_id: int,
    discord_user_id: int,
    role_id: uuid.UUID,
) -> DashboardGrant:
    async with session_scope() as session:
        grant = DashboardGrant(
            guild_id=guild_id,
            discord_user_id=discord_user_id,
            role_id=role_id,
        )
        session.add(grant)
        await session.flush()
        await session.refresh(grant, attribute_names=["role"])
        return grant


async def revoke_grant(grant_id: uuid.UUID) -> bool:
    async with session_scope() as session:
        result = await session.execute(select(DashboardGrant).where(DashboardGrant.id == grant_id))
        row = result.scalar_one_or_none()
        if not row or row.revoked_at:
            return False
        row.revoked_at = _utcnow()
        return True


async def get_role_by_template(template_key: str) -> Optional[DashboardRole]:
    async with session_scope() as session:
        result = await session.execute(
            select(DashboardRole).where(DashboardRole.template_key == template_key)
        )
        return result.scalar_one_or_none()


async def list_roles() -> list[DashboardRole]:
    async with session_scope() as session:
        result = await session.execute(select(DashboardRole).order_by(DashboardRole.name))
        return list(result.scalars().all())
