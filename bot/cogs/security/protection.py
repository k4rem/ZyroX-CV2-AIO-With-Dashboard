"""V2 security listeners. They record and attribute. They do not punish."""

from __future__ import annotations

import logging

import discord
from discord.ext import commands

from cls_platform.security.attribution import AuditCandidate
from cls_platform.security.feed import ObservationFeed
from cls_platform.security.guild_gate import security_guild_eligible
from cls_platform.security.tiers import tier_of_added_bits

logger = logging.getLogger(__name__)

_feed = ObservationFeed()

_PRIMARY = {
    "channel_delete": "channel.delete",
    "role_delete": "role.delete",
    "ban": "member.ban",
    "kick": "member.kick",
    "member_prune": "member.prune",
    "role_update": "role.permission_escalation",
    "role_create": "role.permission_escalation",
    "member_role_update": "member.privileged_role_grant",
    "bot_add": "bot.add",
    "webhook_create": "webhook.create",
}


def get_feed() -> ObservationFeed:
    return _feed


def _perm_names(permissions) -> set[str]:
    if permissions is None:
        return set()
    return {name for name, value in permissions if value}


class _DiscordAuditSource:
    """Read-only audit fetch. Never edits members, roles, or channels."""

    def __init__(self, bot) -> None:
        self.bot = bot

    async def fetch(self, guild_id, discord_action, *, after_id, limit):
        from cls_platform.security.feed import FetchPage

        guild = self.bot.get_guild(int(guild_id))
        if guild is None:
            return FetchPage(entries=[])
        action = getattr(discord.AuditLogAction, discord_action, None)
        if action is None:
            return FetchPage(entries=[])
        try:
            entries = []
            async for entry in guild.audit_logs(limit=limit, after=discord.Object(id=int(after_id)), action=action):
                mapped = _PRIMARY.get(entry.action.name)
                if mapped is None:
                    continue
                user = getattr(entry, "user", None)
                target = getattr(entry, "target", None)
                entries.append(
                    AuditCandidate(
                        audit_entry_id=int(entry.id),
                        discord_action=entry.action.name,
                        action_class=mapped,
                        target_id=getattr(target, "id", None),
                        actor_id=getattr(user, "id", None),
                        entry_created_at=entry.created_at,
                        change_digest=mapped,
                    )
                )
            return FetchPage(entries=entries)
        except discord.Forbidden:
            return FetchPage(error="forbidden")
        except discord.HTTPException as exc:
            retry_after = float(getattr(exc, "retry_after", 0) or 0)
            if getattr(exc, "status", None) == 429 or retry_after:
                return FetchPage(error="rate_limited", retry_after=retry_after or 1)
            logger.warning("audit fetch failed guild=%s status=%s", guild_id, getattr(exc, "status", None))
            return FetchPage(entries=[])


class SecurityProtection(commands.Cog):
    def __init__(self, bot) -> None:
        self.bot = bot
        _feed.source = _DiscordAuditSource(bot)

    @commands.Cog.listener()
    async def on_audit_log_entry_create(self, entry: discord.AuditLogEntry) -> None:
        guild = getattr(entry, "guild", None)
        if guild is None or not security_guild_eligible(guild.id):
            return
        action_name = getattr(getattr(entry, "action", None), "name", None)
        action_class = _PRIMARY.get(action_name or "")
        if action_class is None:
            return
        target = getattr(entry, "target", None)
        if getattr(target, "managed", False) and action_class == "role.permission_escalation":
            return
        user = getattr(entry, "user", None)
        candidate = AuditCandidate(
            audit_entry_id=int(entry.id),
            discord_action=action_name,
            action_class=action_class,
            target_id=getattr(target, "id", None),
            actor_id=getattr(user, "id", None),
            entry_created_at=entry.created_at,
            change_digest=action_class,
        )
        try:
            _feed.cls_user_id = getattr(getattr(self.bot, "user", None), "id", None)
            await _feed.ingest_audit(candidate, guild_id=int(guild.id), source="audit_push")
        except Exception:
            logger.exception("security audit listener failed guild=%s", guild.id)

    @commands.Cog.listener()
    async def on_guild_channel_delete(self, channel) -> None:
        await self._signal(getattr(channel, "guild", None), "channel.delete", getattr(channel, "id", None), "delete")

    @commands.Cog.listener()
    async def on_guild_role_delete(self, role) -> None:
        if getattr(role, "managed", False):
            return
        await self._signal(getattr(role, "guild", None), "role.delete", getattr(role, "id", None), "delete")

    @commands.Cog.listener()
    async def on_member_ban(self, guild, user) -> None:
        await self._signal(guild, "member.ban", getattr(user, "id", None), "ban")

    @commands.Cog.listener()
    async def on_member_join(self, member) -> None:
        if not getattr(member, "bot", False):
            return
        await self._signal(getattr(member, "guild", None), "bot.add", getattr(member, "id", None), "bot_add")

    @commands.Cog.listener()
    async def on_guild_role_update(self, before, after) -> None:
        if getattr(after, "managed", False):
            return
        added = _perm_names(getattr(after, "permissions", None)) - _perm_names(getattr(before, "permissions", None))
        if tier_of_added_bits(added) is None:
            return
        digest = ",".join(sorted(added))
        await self._signal(getattr(after, "guild", None), "role.permission_escalation", after.id, digest)

    async def _signal(self, guild, action_class: str, target_id, digest: str) -> None:
        if guild is None or not security_guild_eligible(guild.id):
            return
        try:
            await _feed.record_gateway_signal(
                guild_id=int(guild.id),
                action_class=action_class,
                target_id=int(target_id) if target_id is not None else None,
                change_digest=digest,
                discord_action=None,
            )
        except Exception:
            logger.exception("security gateway listener failed guild=%s", getattr(guild, "id", None))
