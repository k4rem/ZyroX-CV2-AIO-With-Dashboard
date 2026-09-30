"""Register scheduler job handlers (Phase 1)."""

from __future__ import annotations

import logging

from cls_platform.services.scheduler import register_job_handler

logger = logging.getLogger(__name__)


def register_scheduler_handlers(bot) -> None:
    async def role_temp_remove(job):
        payload = job.payload or {}
        guild_id = int(payload["guild_id"])
        user_id = int(payload["user_id"])
        role_id = int(payload["role_id"])
        guild = bot.get_guild(guild_id)
        if guild is None:
            return
        member = guild.get_member(user_id)
        if member is None:
            try:
                member = await guild.fetch_member(user_id)
            except Exception:
                return
        role = guild.get_role(role_id)
        if role is None or role not in member.roles:
            return
        try:
            await member.remove_roles(role, reason="Temporary role expired (scheduler)")
        except Exception as exc:
            logger.warning("role_temp_remove failed guild=%s user=%s: %s", guild_id, user_id, exc)
            raise

    register_job_handler("role_temp_remove", role_temp_remove)
