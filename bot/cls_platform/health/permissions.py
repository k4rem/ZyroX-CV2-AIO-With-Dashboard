"""Bot permission / hierarchy health checks."""

from __future__ import annotations

from typing import Any

import discord

MODULE_REQUIRED: dict[str, list[str]] = {
    "Moderation": ["manage_roles", "kick_members", "ban_members", "moderate_members"],
    "Antinuke": ["manage_guild", "ban_members", "manage_roles"],
    "Tickets": ["manage_channels", "manage_roles"],
    "Welcome": ["manage_roles", "send_messages"],
    "JoinToCreate": ["manage_channels", "move_members", "connect"],
    "Logging": ["view_audit_log", "send_messages"],
}


async def permission_health_summary(bot) -> dict[str, Any]:
    guilds_out = []
    for guild in bot.guilds:
        me = guild.me
        if not me:
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
