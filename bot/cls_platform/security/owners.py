"""Guild owner identity for policy suppression. Unknown never means eligible."""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import select

from cls_platform.database import session_scope
from cls_platform.security.models import SecurityGuildState


async def remember_guild_owner(guild_id: int, owner_id: int | None) -> None:
    if owner_id is None:
        return
    async with session_scope() as session:
        state = (
            await session.execute(select(SecurityGuildState).where(SecurityGuildState.guild_id == guild_id))
        ).scalar_one_or_none()
        if state is None:
            session.add(
                SecurityGuildState(
                    guild_id=guild_id,
                    trust_version=0,
                    ops_destination_ok=False,
                    guild_owner_id=int(owner_id),
                )
            )
            return
        state.guild_owner_id = int(owner_id)
        state.updated_at = datetime.now(timezone.utc)


async def resolve_owner(guild_id: int, live_owner_id: int | None = None) -> tuple[int | None, bool]:
    """Prefer a live owner id, then the persisted value. Unknown stays unknown."""
    if live_owner_id is not None:
        await remember_guild_owner(guild_id, int(live_owner_id))
        return int(live_owner_id), True
    async with session_scope() as session:
        stored = (
            await session.execute(
                select(SecurityGuildState.guild_owner_id).where(SecurityGuildState.guild_id == guild_id)
            )
        ).scalar_one_or_none()
    if stored is None:
        return None, False
    return int(stored), True


def live_owner_id(bot, guild_id: int) -> int | None:
    if bot is None or not hasattr(bot, "get_guild"):
        return None
    guild = bot.get_guild(int(guild_id))
    if guild is None:
        return None
    owner_id = getattr(guild, "owner_id", None)
    if owner_id is None and getattr(guild, "owner", None) is not None:
        owner_id = getattr(guild.owner, "id", None)
    return int(owner_id) if owner_id is not None else None
