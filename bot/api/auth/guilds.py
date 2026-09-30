"""Authorized guild listing for Dashboard."""

from __future__ import annotations

from api.auth.context import DashboardAuthContext
from cls_platform.config import OPS_GUILD_ID
from cls_platform.services import grants as grant_service
from api.auth.allowlist import is_guild_allowed


async def authorized_guild_ids(auth: DashboardAuthContext, bot) -> set[int]:
    ids: set[int] = set()
    for guild in bot.guilds:
        if not is_guild_allowed(guild.id):
            continue
        if OPS_GUILD_ID is not None and guild.id == OPS_GUILD_ID:
            continue
        ids.add(guild.id)

    if auth.is_root:
        return ids

    grants = await grant_service.list_grants_for_user(auth.user_id)
    grant_guilds = {g.guild_id for g in grants}
    return ids.intersection(grant_guilds)
