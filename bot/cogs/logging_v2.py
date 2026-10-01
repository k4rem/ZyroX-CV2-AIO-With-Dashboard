"""Persist operational Discord events and post them when a route is enabled."""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timedelta, timezone

import discord
from discord.ext import commands

from cls_platform.logging.store import purge_expired, record_event, remember_message, route_for, stored_message

logger = logging.getLogger(__name__)


class LoggingV2(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self._task: asyncio.Task | None = None

    async def cog_load(self):
        self._task = asyncio.create_task(self._retain())

    async def cog_unload(self):
        if self._task is not None:
            self._task.cancel()

    async def _retain(self):
        await self.bot.wait_until_ready()
        while True:
            try:
                await purge_expired()
            except Exception:
                logger.exception("logging retention failed")
            await asyncio.sleep(3600)

    async def _actor(self, guild: discord.Guild, action: discord.AuditLogAction, target_id: int | None):
        try:
            if guild.me is None or not guild.me.guild_permissions.view_audit_log:
                return None, "unknown"
            cutoff = datetime.now(timezone.utc) - timedelta(seconds=15)
            matches = []
            async for entry in guild.audit_logs(limit=5, action=action):
                if entry.created_at < cutoff:
                    continue
                target = getattr(entry.target, "id", None)
                if target_id is not None and target != target_id:
                    continue
                matches.append(entry)
            if len(matches) == 1 and matches[0].user is not None:
                return matches[0].user.id, "certain"
        except (discord.Forbidden, discord.HTTPException):
            return None, "unknown"
        return None, "unknown"

    async def _save(self, guild: discord.Guild, **payload):
        saved = await record_event(guild_id=guild.id, **payload)
        route = await route_for(guild.id, payload["category"])
        if route is None:
            return saved
        channel = guild.get_channel(route["channel_id"])
        if channel is None:
            return saved
        actor = saved["actor_id"] or "unknown"
        target = saved["target_id"] or "—"
        try:
            await channel.send(
                f"{saved['event_type']} · actor {actor} ({saved['actor_confidence']}) · target {target}",
                allowed_mentions=discord.AllowedMentions.none(),
            )
        except (discord.Forbidden, discord.HTTPException):
            logger.warning("log route delivery failed for guild %s", guild.id)
        return saved

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        await self._save(
            member.guild,
            category="join_leave_events",
            event_type="member_join",
            actor_id=member.id,
            actor_confidence="certain",
            target_id=member.id,
        )

    @commands.Cog.listener()
    async def on_member_remove(self, member: discord.Member):
        actor_id, confidence = await self._actor(member.guild, discord.AuditLogAction.kick, member.id)
        if actor_id:
            await self._save(
                member.guild,
                category="member_moderation",
                event_type="member_kick",
                actor_id=actor_id,
                actor_confidence=confidence,
                target_id=member.id,
            )
            return
        await self._save(
            member.guild,
            category="join_leave_events",
            event_type="member_leave",
            target_id=member.id,
            actor_confidence="unknown",
        )

    @commands.Cog.listener()
    async def on_member_ban(self, guild: discord.Guild, user: discord.User):
        actor_id, confidence = await self._actor(guild, discord.AuditLogAction.ban, user.id)
        await self._save(
            guild,
            category="member_moderation",
            event_type="member_ban",
            actor_id=actor_id,
            actor_confidence=confidence,
            target_id=user.id,
        )

    @commands.Cog.listener()
    async def on_member_unban(self, guild: discord.Guild, user: discord.User):
        actor_id, confidence = await self._actor(guild, discord.AuditLogAction.unban, user.id)
        await self._save(
            guild,
            category="member_moderation",
            event_type="member_unban",
            actor_id=actor_id,
            actor_confidence=confidence,
            target_id=user.id,
        )

    @commands.Cog.listener()
    async def on_member_update(self, before: discord.Member, after: discord.Member):
        before_roles = [role.id for role in before.roles if role.id != after.guild.id]
        after_roles = [role.id for role in after.roles if role.id != after.guild.id]
        if before_roles == after_roles:
            return
        actor_id, confidence = await self._actor(after.guild, discord.AuditLogAction.member_role_update, after.id)
        await self._save(
            after.guild,
            category="role_events",
            event_type="member_roles",
            actor_id=actor_id,
            actor_confidence=confidence,
            target_id=after.id,
            before={"role_ids": [str(role_id) for role_id in before_roles]},
            after={"role_ids": [str(role_id) for role_id in after_roles]},
        )

    @commands.Cog.listener()
    async def on_guild_channel_create(self, channel: discord.abc.GuildChannel):
        await self._save(channel.guild, category="channel_events", event_type="channel_create", channel_id=channel.id, after={"name": channel.name})

    @commands.Cog.listener()
    async def on_guild_channel_delete(self, channel: discord.abc.GuildChannel):
        await self._save(channel.guild, category="channel_events", event_type="channel_delete", channel_id=channel.id, before={"name": channel.name})

    @commands.Cog.listener()
    async def on_guild_channel_update(self, before: discord.abc.GuildChannel, after: discord.abc.GuildChannel):
        if before.name == after.name:
            return
        await self._save(
            after.guild,
            category="channel_events",
            event_type="channel_update",
            channel_id=after.id,
            before={"name": before.name},
            after={"name": after.name},
        )

    @commands.Cog.listener()
    async def on_guild_role_create(self, role: discord.Role):
        await self._save(role.guild, category="role_events", event_type="role_create", target_id=role.id, after={"name": role.name})

    @commands.Cog.listener()
    async def on_guild_role_delete(self, role: discord.Role):
        await self._save(role.guild, category="role_events", event_type="role_delete", target_id=role.id, before={"name": role.name})

    @commands.Cog.listener()
    async def on_guild_update(self, before: discord.Guild, after: discord.Guild):
        if before.name == after.name:
            return
        await self._save(after, category="guild_events", event_type="guild_update", before={"name": before.name}, after={"name": after.name})

    @commands.Cog.listener()
    async def on_voice_state_update(self, member: discord.Member, before: discord.VoiceState, after: discord.VoiceState):
        if before.channel == after.channel:
            return
        kind = "voice_move" if before.channel and after.channel else "voice_join" if after.channel else "voice_leave"
        channel = after.channel or before.channel
        await self._save(
            member.guild,
            category="voice_events",
            event_type=kind,
            actor_id=member.id,
            actor_confidence="certain",
            target_id=member.id,
            channel_id=channel.id if channel else None,
        )

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.guild is None or message.author.bot:
            return
        await remember_message(
            guild_id=message.guild.id,
            message_id=message.id,
            channel_id=message.channel.id,
            author_id=message.author.id,
            content=message.content or "",
        )

    @commands.Cog.listener()
    async def on_message_edit(self, before: discord.Message, after: discord.Message):
        if after.guild is None or after.author.bot or before.content == after.content:
            return
        await remember_message(
            guild_id=after.guild.id,
            message_id=after.id,
            channel_id=after.channel.id,
            author_id=after.author.id,
            content=after.content or "",
        )
        await self._save(
            after.guild,
            category="message_events",
            event_type="message_edit",
            actor_id=after.author.id,
            actor_confidence="certain",
            target_id=after.id,
            channel_id=after.channel.id,
            before={"content": (before.content or "")[:500]},
            after={"content": (after.content or "")[:500]},
        )

    @commands.Cog.listener()
    async def on_raw_message_delete(self, payload: discord.RawMessageDeleteEvent):
        if payload.guild_id is None:
            return
        guild = self.bot.get_guild(payload.guild_id)
        if guild is None:
            return
        content = await stored_message(payload.guild_id, payload.message_id)
        author_id = payload.cached_message.author.id if payload.cached_message else None
        await self._save(
            guild,
            category="message_events",
            event_type="message_delete",
            actor_id=author_id,
            actor_confidence="certain" if author_id else "unknown",
            target_id=payload.message_id,
            channel_id=payload.channel_id,
            metadata={"content": content} if content else {},
        )


async def setup(bot):
    await bot.add_cog(LoggingV2(bot))
