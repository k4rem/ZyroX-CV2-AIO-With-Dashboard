"""Bot permission / hierarchy health checks."""

from __future__ import annotations

from collections.abc import Collection
from typing import Any

import discord

MODULE_REQUIRED: dict[str, list[str]] = {
    "Moderation": ["manage_roles", "kick_members", "ban_members", "moderate_members"],
    # view_audit_log is OBSERVABILITY health only. It is not an escalation trigger.
    "Antinuke": ["manage_guild", "ban_members", "manage_roles", "view_audit_log"],
    "Tickets": ["manage_channels", "manage_roles"],
    "Welcome": ["manage_roles", "send_messages"],
    "JoinToCreate": ["manage_channels", "move_members", "connect"],
    "Logging": ["view_audit_log", "send_messages"],
}


async def permission_health_summary(bot, *, guild_ids: Collection[int]) -> dict[str, Any]:
    """Per-guild bot permission health, restricted to ``guild_ids``.

    ``guild_ids`` is required on purpose: callers must pass the set the requesting
    Dashboard identity is authorized for, so this can never be called "for all guilds"
    by accident. Guilds outside the set are not read at all.
    """
    allowed = {int(g) for g in guild_ids}
    guilds_out = []
    for guild in bot.guilds:
        if guild.id not in allowed:
            continue
        me = getattr(guild, "me", None)
        if me is None:
            continue
        perms = me.guild_permissions
        missing_by_module: dict[str, list[str]] = {}
        for mod, needed in MODULE_REQUIRED.items():
            missing = [p for p in needed if not getattr(perms, p, False)]
            if missing:
                missing_by_module[mod] = missing
        top_role = me.top_role
        guilds_out.append(
            {
                "guild_id": str(guild.id),
                "guild_name": guild.name,
                "top_role_position": top_role.position if top_role else 0,
                "missing_by_module": missing_by_module,
                "critical": bool(missing_by_module),
            }
        )
    return {"guilds": guilds_out, "module_requirements": MODULE_REQUIRED}
