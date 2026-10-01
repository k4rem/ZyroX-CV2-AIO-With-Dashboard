"""V2 security listeners. They record and attribute. They do not punish."""

from __future__ import annotations

import logging

import discord
from discord.ext import commands

from cls_platform.security.attribution import AuditCandidate
from cls_platform.security.feed import ObservationFeed
from cls_platform.security.guild_gate import security_guild_eligible
from cls_platform.security.owners import live_owner_id, remember_guild_owner
from cls_platform.security.permission_diff import (
    classify_member_grant,
    classify_role_change,
    permission_names,
)
from cls_platform.security.tiers import highest_tier, tier_of_added_bits

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


def _role_permission_delta(entry) -> tuple[set[str], set[str]]:
    before_roles = list(getattr(getattr(entry, "before", None), "roles", None) or [])
    after_roles = list(getattr(getattr(entry, "after", None), "roles", None) or [])
    before_ids = {getattr(role, "id", id(role)) for role in before_roles}
    after_ids = {getattr(role, "id", id(role)) for role in after_roles}
    added_roles = [role for role in after_roles if getattr(role, "id", id(role)) not in before_ids]
    removed_roles = [role for role in before_roles if getattr(role, "id", id(role)) not in after_ids]
    added: set[str] = set()
    for role in added_roles:
        added |= permission_names(getattr(role, "permissions", None))
    removed: set[str] = set()
    for role in removed_roles:
        removed |= permission_names(getattr(role, "permissions", None))
    return added, removed


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

    async def fetch_recent(self, guild_id, *, after_id, limit):
        from cls_platform.security.feed import FetchPage

        guild = self.bot.get_guild(int(guild_id))
        if guild is None:
            return FetchPage(entries=[])
        try:
            entries = []
            async for entry in guild.audit_logs(limit=limit, after=discord.Object(id=int(after_id))):
                if entry.action.name in {"role_update", "role_create", "member_role_update"}:
                    continue
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
        self._session_started = False
        _feed.source = _DiscordAuditSource(bot)

    def cog_unload(self) -> None:
        _feed.cancel_tasks()

    async def _remember_owner(self, guild) -> None:
        owner_id = getattr(guild, "owner_id", None)
        owner = getattr(guild, "owner", None)
        if owner_id is None and owner is not None:
            owner_id = getattr(owner, "id", None)
        if owner_id is None:
            owner_id = live_owner_id(self.bot, int(guild.id))
        if owner_id is not None:
            _feed.guild_owners[int(guild.id)] = int(owner_id)
            try:
                await remember_guild_owner(int(guild.id), int(owner_id))
            except Exception:
                logger.exception("security owner refresh failed guild=%s", guild.id)

    def _cls_role_ids(self, guild) -> set[int]:
        me = getattr(guild, "me", None)
        if me is None and self.bot is not None:
            me = getattr(self.bot, "user", None)
            getter = getattr(guild, "get_member", None)
            if getter and getattr(me, "id", None):
                me = getter(me.id)
        roles = getattr(me, "roles", None) or []
        return {int(role.id) for role in roles if getattr(role, "id", None) is not None}

    @commands.Cog.listener()
    async def on_ready(self) -> None:
        resumed = self._session_started
        self._session_started = True
        for guild in list(getattr(self.bot, "guilds", []) or []):
            await self._remember_owner(guild)
        await _feed.resume_pending_after_restart()
        if resumed:
            return
        # Process start is the new-session hook. Whether Discord treated that
        # connection as RESUME is V-7 and is not claimed here.
        for guild in list(getattr(self.bot, "guilds", []) or []):
            if security_guild_eligible(guild.id):
                await _feed.reconcile_watermark(int(guild.id))

    @commands.Cog.listener()
    async def on_resumed(self) -> None:
        await _feed.resume_pending_after_restart()

    @commands.Cog.listener()
    async def on_guild_join(self, guild) -> None:
        await self._remember_owner(guild)

    @commands.Cog.listener()
    async def on_guild_update(self, before, after) -> None:
        await self._remember_owner(after)

    @commands.Cog.listener()
    async def on_audit_log_entry_create(self, entry: discord.AuditLogEntry) -> None:
        guild = getattr(entry, "guild", None)
        if guild is None or not security_guild_eligible(guild.id):
            return
        action_name = getattr(getattr(entry, "action", None), "name", None)
        mapped = self._classify_entry(guild, entry, action_name)
        if mapped is None:
            return
        user = getattr(entry, "user", None)
        target = getattr(entry, "target", None)
        candidate = AuditCandidate(
            audit_entry_id=int(entry.id),
            discord_action=action_name or mapped["action_class"],
            action_class=mapped["action_class"],
            target_id=getattr(target, "id", None),
            actor_id=getattr(user, "id", None),
            entry_created_at=entry.created_at,
            change_digest=mapped["action_class"],
            permission_diff=mapped.get("permission_diff"),
            permission_tier=mapped.get("permission_tier"),
            actor_is_bot=bool(mapped.get("actor_is_bot")),
            reason_token=getattr(entry, "reason", None),
        )
        try:
            await self._remember_owner(guild)
            _feed.cls_user_id = getattr(getattr(self.bot, "user", None), "id", None)
            await _feed.ingest_audit(candidate, guild_id=int(guild.id), source="audit_push")
        except Exception:
            logger.exception("security audit listener failed guild=%s", guild.id)

    def _classify_entry(self, guild, entry, action_name: str | None) -> dict | None:
        target = getattr(entry, "target", None)
        if action_name in {"role_update", "role_create"}:
            classified = classify_role_change(
                guild_id=int(guild.id),
                role_id=int(getattr(target, "id", 0) or 0),
                managed=bool(getattr(target, "managed", False)),
                before=getattr(entry, "before", None),
                after=getattr(entry, "after", None),
                cls_role_ids=self._cls_role_ids(guild),
            )
            return classified
        if action_name == "member_role_update":
            added, removed = _role_permission_delta(entry)
            target_is_bot = bool(getattr(target, "bot", False))
            cls_id = getattr(getattr(self.bot, "user", None), "id", None)
            classified = classify_member_grant(
                target_is_bot=target_is_bot,
                target_is_cls=cls_id is not None and getattr(target, "id", None) == cls_id,
                added_permissions=added,
                removed=bool(removed) and not added,
            )
            return classified
        action_class = _PRIMARY.get(action_name or "")
        if action_class is None:
            return None
        if getattr(target, "managed", False) and action_class == "role.permission_escalation":
            return None
        tier = None
        if action_class == "bot.add":
            tier = highest_tier(permission_names(getattr(target, "guild_permissions", None)))
        return {
            "action_class": action_class,
            "permission_tier": tier,
            "actor_is_bot": bool(getattr(getattr(entry, "user", None), "bot", False)),
        }

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
        await self._remember_owner(guild)
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
