"""Capture operational Discord events and deliver Logging V2 embeds."""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timedelta, timezone

import discord
from discord.ext import commands

from cls_platform.logging.attribution import classify_matches
from cls_platform.logging.entities import snapshot_channel, snapshot_role, snapshot_user
from cls_platform.logging.legacy import migrate_legacy_file
from cls_platform.logging.pipeline import event_ignored, message_ignored
from cls_platform.logging.publish import set_log_deliverer
from cls_platform.logging.render import render_discord
from cls_platform.logging.source import read_source
from cls_platform.logging.store import (
    appearance_for,
    delivery_target,
    ignores,
    purge_expired,
    record_event,
    remember_message,
    stored_message_record,
)

logger = logging.getLogger(__name__)
_MENTIONS = discord.AllowedMentions(everyone=False, users=True, roles=True, replied_user=False)


def embed_from_payload(payload: dict, when: datetime | None = None) -> discord.Embed:
    embed = discord.Embed(
        title=payload["title"],
        description=(payload.get("description") or None),
        color=payload.get("color") or 0x6B7280,
    )
    if payload.get("timestamp", True):
        embed.timestamp = when or datetime.now(timezone.utc)
    if payload.get("author_name"):
        author = {"name": str(payload["author_name"])[:256]}
        if payload.get("author_icon"):
            author["icon_url"] = payload["author_icon"]
        embed.set_author(**author)
    if payload.get("thumbnail"):
        embed.set_thumbnail(url=payload["thumbnail"])
    for field in payload.get("fields") or []:
        embed.add_field(name=str(field["name"])[:256], value=str(field["value"] or "—")[:1024], inline=bool(field.get("inline")))
    if payload.get("footer"):
        embed.set_footer(text=str(payload["footer"])[:2048])
    return embed


def _files(message: discord.Message) -> list[dict]:
    rows = []
    for attachment in message.attachments[:8]:
        rows.append(
            {
                "filename": attachment.filename,
                "size": attachment.size,
                "content_type": attachment.content_type,
            }
        )
    return rows


def _overwrites(channel) -> list[dict]:
    rows = []
    for target, overwrite in (getattr(channel, "overwrites", None) or {}).items():
        allow, deny = overwrite.pair()
        rows.append(
            {
                "id": str(target.id),
                "name": getattr(target, "name", None) or getattr(target, "display_name", "someone"),
                "kind": "role" if isinstance(target, discord.Role) else "member",
                "allow": allow.value,
                "deny": deny.value,
            }
        )
    return rows


def _channel_state(channel) -> dict:
    return {
        "name": channel.name,
        "topic": getattr(channel, "topic", None),
        "slowmode": getattr(channel, "slowmode_delay", None),
        "overwrites": _overwrites(channel),
    }


def _role_state(role: discord.Role) -> dict:
    snap = snapshot_role(role) or {}
    return {
        "name": role.name,
        "color": snap.get("color"),
        "mentionable": bool(role.mentionable),
        "permissions": role.permissions.value,
    }


def _changed(before: dict, after: dict) -> tuple[dict, dict] | None:
    keys = [key for key in after if before.get(key) != after.get(key)]
    if not keys:
        return None
    return {key: before.get(key) for key in keys}, {key: after.get(key) for key in keys}


def _meta(entities: dict, **extra) -> dict:
    reason = extra.get("reason")
    if reason == "__ambiguous__":
        extra["reason"] = None
        extra["attribution"] = "ambiguous"
    elif reason == "__audit_unavailable__":
        extra["reason"] = None
        extra["audit_unavailable"] = True
    elif reason == "__self__":
        extra["reason"] = None
        extra["attribution"] = "self"
    payload = {"entities": {key: value for key, value in entities.items() if value}}
    payload.update({key: value for key, value in extra.items() if value is not None})
    return payload


class LoggingV2(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self._task: asyncio.Task | None = None

    async def cog_load(self):
        set_log_deliverer(self._deliver_published)
        self._task = asyncio.create_task(self._retain())

    async def cog_unload(self):
        set_log_deliverer(None)
        if self._task is not None:
            self._task.cancel()

    async def _deliver_published(self, guild_id: int, channel_id: int, event: dict):
        guild = self.bot.get_guild(int(guild_id))
        if guild is None:
            return
        await self._deliver(guild, int(channel_id), event)

    async def _retain(self):
        await self.bot.wait_until_ready()
        for _ in range(30):
            try:
                await migrate_legacy_file()
                break
            except Exception:
                logger.exception("legacy logging migration failed")
                await asyncio.sleep(2)
        while True:
            try:
                await purge_expired()
            except Exception:
                logger.exception("logging retention failed")
            await asyncio.sleep(3600)

    async def _audit(self, guild: discord.Guild, action: discord.AuditLogAction, target_id: int | None, channel_id: int | None = None):
        try:
            if guild.me is None or not guild.me.guild_permissions.view_audit_log:
                return None, "unknown", "__audit_unavailable__"
            cutoff = datetime.now(timezone.utc) - timedelta(seconds=15)
            matches = []
            async for entry in guild.audit_logs(limit=6, action=action):
                if entry.created_at < cutoff:
                    continue
                target = getattr(entry.target, "id", None)
                extra_channel = getattr(getattr(entry, "extra", None), "channel", None)
                extra_id = getattr(extra_channel, "id", None)
                if channel_id is not None:
                    if channel_id not in {target, extra_id}:
                        continue
                elif target_id is not None and target != target_id:
                    continue
                matches.append((entry.user, entry.reason))
            user, confidence, reason, note = classify_matches(matches)
            if note == "ambiguous":
                return None, "unknown", "__ambiguous__"
            return user, confidence, reason
        except (discord.Forbidden, discord.HTTPException):
            return None, "unknown", "__audit_unavailable__"

    async def _message_actor(self, guild: discord.Guild, action: discord.AuditLogAction, channel_id: int, author_id: int | None):
        try:
            if guild.me is None or not guild.me.guild_permissions.view_audit_log:
                return None, "unknown", "__audit_unavailable__"
            cutoff = datetime.now(timezone.utc) - timedelta(seconds=15)
            matches = []
            async for entry in guild.audit_logs(limit=6, action=action):
                if entry.created_at < cutoff:
                    continue
                extra_channel = getattr(getattr(entry, "extra", None), "channel", None)
                if extra_channel is not None and getattr(extra_channel, "id", None) not in {None, channel_id}:
                    continue
                target = getattr(entry.target, "id", None)
                if action is discord.AuditLogAction.message_bulk_delete and target not in {None, channel_id}:
                    continue
                if action is discord.AuditLogAction.message_delete and author_id and target not in {None, author_id}:
                    continue
                matches.append((entry.user, entry.reason))
            user, confidence, reason, note = classify_matches(matches)
            if note == "ambiguous":
                return None, "unknown", "__ambiguous__"
            return user, confidence, reason
        except (discord.Forbidden, discord.HTTPException):
            return None, "unknown", "__audit_unavailable__"

    async def _incident(self, guild_id: int, subject_id: int | None) -> str | None:
        if subject_id is None:
            return None
        try:
            from sqlalchemy import select

            from cls_platform.database import session_scope
            from cls_platform.security.models import SecurityIncident

            async with session_scope() as session:
                found = (
                    await session.execute(
                        select(SecurityIncident.id)
                        .where(
                            SecurityIncident.guild_id == guild_id,
                            SecurityIncident.subject_id == subject_id,
                            SecurityIncident.status == "ACTIVE",
                        )
                        .limit(1)
                    )
                ).scalar_one_or_none()
            return str(found) if found else None
        except Exception:
            logger.debug("incident lookup skipped", exc_info=True)
            return None

    async def _deliver(self, guild: discord.Guild, channel_id: int, event: dict):
        channel = guild.get_channel(channel_id)
        me = guild.me
        if channel is None or me is None or not hasattr(channel, "permissions_for"):
            return
        perms = channel.permissions_for(me)
        if not perms.send_messages or not perms.embed_links:
            logger.warning("log route missing send or embed permission for guild %s", guild.id)
            return
        rendered = render_discord(event, await appearance_for(guild.id))
        view = None
        if rendered.get("jump_url"):
            view = discord.ui.View()
            view.add_item(discord.ui.Button(style=discord.ButtonStyle.link, label="View message", url=rendered["jump_url"]))
        try:
            await channel.send(embed=embed_from_payload(rendered), view=view, allowed_mentions=_MENTIONS)
        except (discord.Forbidden, discord.HTTPException):
            logger.warning("log route delivery failed for guild %s", guild.id)

    async def _save(self, guild: discord.Guild, **payload):
        decision = await delivery_target(guild.id, payload["category"], payload["event_type"])
        if not decision["capture"]:
            return None
        appearance = await appearance_for(guild.id)
        if appearance.get("ignore_scope") == "all":
            if event_ignored(
                channel_id=payload.get("channel_id"),
                actor_id=payload.get("actor_id"),
                target_id=payload.get("target_id"),
                ignores=await ignores(guild.id),
            ):
                return None
        metadata = dict(payload.get("metadata") or {})
        module = read_source(guild_id=guild.id, target_id=payload.get("target_id"))
        me = guild.me
        if module and me is not None and payload.get("actor_id") == me.id and not metadata.get("source_module"):
            metadata["source_module"] = module
            payload["metadata"] = metadata
        elif metadata is not payload.get("metadata"):
            payload["metadata"] = metadata
        saved = await record_event(guild_id=guild.id, **payload)
        if decision["deliver"] and decision["channel_id"]:
            await self._deliver(guild, decision["channel_id"], saved)
        return saved

    async def _ignored_message(self, guild: discord.Guild, channel_id: int, author) -> bool:
        role_ids = [role.id for role in getattr(author, "roles", []) or []]
        return message_ignored(
            channel_id=channel_id,
            author_id=getattr(author, "id", None),
            author_role_ids=role_ids,
            ignores=await ignores(guild.id),
        )

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        created = int(member.created_at.timestamp())
        await self._save(
            member.guild,
            category="join_leave_events",
            event_type="member_bot_add" if member.bot else "member_join",
            actor_id=member.id,
            actor_confidence="certain",
            target_id=member.id,
            metadata=_meta(
                {"actor": snapshot_user(member), "target": snapshot_user(member)},
                account_created=member.created_at.date().isoformat(),
                account_created_unix=created,
                member_count=member.guild.member_count,
            ),
        )

    @commands.Cog.listener()
    async def on_member_remove(self, member: discord.Member):
        ban_actor, ban_confidence, _ban_reason = await self._audit(member.guild, discord.AuditLogAction.ban, member.id)
        if ban_actor is not None:
            return
        actor, confidence, reason = await self._audit(member.guild, discord.AuditLogAction.kick, member.id)
        roles = [snapshot_role(role) for role in member.roles if role.id != member.guild.id]
        incident = await self._incident(member.guild.id, member.id)
        if actor is not None:
            await self._save(
                member.guild,
                category="member_moderation",
                event_type="member_kick",
                actor_id=actor.id,
                actor_confidence=confidence,
                target_id=member.id,
                before={"roles": roles},
                metadata=_meta(
                    {"actor": snapshot_user(actor), "target": snapshot_user(member)},
                    reason=reason,
                    incident_id=incident,
                ),
            )
            return
        await self._save(
            member.guild,
            category="join_leave_events",
            event_type="member_bot_remove" if member.bot else "member_leave",
            target_id=member.id,
            actor_confidence="unknown",
            before={"roles": roles},
            metadata=_meta(
                {"target": snapshot_user(member)},
                incident_id=incident,
                reason=reason if reason in {"__audit_unavailable__", "__ambiguous__"} else None,
            ),
        )

    @commands.Cog.listener()
    async def on_member_ban(self, guild: discord.Guild, user: discord.User):
        actor, confidence, reason = await self._audit(guild, discord.AuditLogAction.ban, user.id)
        await self._save(
            guild,
            category="member_moderation",
            event_type="member_ban",
            actor_id=getattr(actor, "id", None),
            actor_confidence=confidence,
            target_id=user.id,
            metadata=_meta(
                {"actor": snapshot_user(actor), "target": snapshot_user(user)},
                reason=reason,
                incident_id=await self._incident(guild.id, user.id),
            ),
        )

    @commands.Cog.listener()
    async def on_member_unban(self, guild: discord.Guild, user: discord.User):
        actor, confidence, reason = await self._audit(guild, discord.AuditLogAction.unban, user.id)
        await self._save(
            guild,
            category="member_moderation",
            event_type="member_unban",
            actor_id=getattr(actor, "id", None),
            actor_confidence=confidence,
            target_id=user.id,
            metadata=_meta({"actor": snapshot_user(actor), "target": snapshot_user(user)}, reason=reason),
        )

    @commands.Cog.listener()
    async def on_member_update(self, before: discord.Member, after: discord.Member):
        await self._roles(before, after)
        await self._nickname(before, after)
        await self._timeout(before, after)
        await self._boost(before, after)

    async def _roles(self, before: discord.Member, after: discord.Member):
        before_roles = [snapshot_role(role) for role in before.roles if role.id != after.guild.id]
        after_roles = [snapshot_role(role) for role in after.roles if role.id != after.guild.id]
        if [role["id"] for role in before_roles] == [role["id"] for role in after_roles]:
            return
        actor, confidence, reason = await self._audit(after.guild, discord.AuditLogAction.member_role_update, after.id)
        await self._save(
            after.guild,
            category="role_events",
            event_type="member_roles",
            actor_id=getattr(actor, "id", None),
            actor_confidence=confidence,
            target_id=after.id,
            before={"roles": before_roles},
            after={"roles": after_roles},
            metadata=_meta(
                {"actor": snapshot_user(actor), "target": snapshot_user(after)},
                reason=reason,
                incident_id=await self._incident(after.guild.id, after.id),
            ),
        )

    async def _nickname(self, before: discord.Member, after: discord.Member):
        if before.nick == after.nick:
            return
        actor, confidence, reason = await self._audit(after.guild, discord.AuditLogAction.member_update, after.id)
        await self._save(
            after.guild,
            category="member_moderation",
            event_type="member_nickname",
            actor_id=getattr(actor, "id", None),
            actor_confidence=confidence,
            target_id=after.id,
            before={"nickname": before.nick},
            after={"nickname": after.nick},
            metadata=_meta({"actor": snapshot_user(actor), "target": snapshot_user(after)}, reason=reason),
        )

    async def _timeout(self, before: discord.Member, after: discord.Member):
        previous = getattr(before, "timed_out_until", None)
        current = getattr(after, "timed_out_until", None)
        if previous == current:
            return
        actor, confidence, reason = await self._audit(after.guild, discord.AuditLogAction.member_update, after.id)
        added = current is not None and (previous is None or current > previous)
        await self._save(
            after.guild,
            category="member_moderation",
            event_type="member_timeout" if added else "member_timeout_removed",
            actor_id=getattr(actor, "id", None),
            actor_confidence=confidence,
            target_id=after.id,
            before={"until": previous.isoformat() if previous else None},
            after={"until": current.isoformat() if current else None},
            metadata=_meta({"actor": snapshot_user(actor), "target": snapshot_user(after)}, reason=reason),
        )

    async def _boost(self, before: discord.Member, after: discord.Member):
        previous = getattr(before, "premium_since", None)
        current = getattr(after, "premium_since", None)
        if previous == current:
            return
        name = after.display_name
        started = current is not None and previous is None
        await self._save(
            after.guild,
            category="join_leave_events",
            event_type="member_boost" if started else "member_boost_end",
            actor_id=after.id,
            actor_confidence="certain",
            target_id=after.id,
            metadata=_meta(
                {"actor": snapshot_user(after), "target": snapshot_user(after)},
                sentence=f"{name} started boosting" if started else f"{name} stopped boosting",
                attribution="self",
            ),
        )

    @commands.Cog.listener()
    async def on_guild_channel_create(self, channel: discord.abc.GuildChannel):
        actor, confidence, reason = await self._audit(channel.guild, discord.AuditLogAction.channel_create, channel.id)
        await self._save(
            channel.guild,
            category="channel_events",
            event_type="channel_create",
            actor_id=getattr(actor, "id", None),
            actor_confidence=confidence,
            channel_id=channel.id,
            after={"name": channel.name},
            metadata=_meta({"actor": snapshot_user(actor), "channel": snapshot_channel(channel)}, reason=reason),
        )

    @commands.Cog.listener()
    async def on_guild_channel_delete(self, channel: discord.abc.GuildChannel):
        actor, confidence, reason = await self._audit(channel.guild, discord.AuditLogAction.channel_delete, channel.id)
        await self._save(
            channel.guild,
            category="channel_events",
            event_type="channel_delete",
            actor_id=getattr(actor, "id", None),
            actor_confidence=confidence,
            channel_id=channel.id,
            before={"name": channel.name},
            metadata=_meta({"actor": snapshot_user(actor), "channel": snapshot_channel(channel)}, reason=reason),
        )

    @commands.Cog.listener()
    async def on_guild_channel_update(self, before: discord.abc.GuildChannel, after: discord.abc.GuildChannel):
        changed = _changed(_channel_state(before), _channel_state(after))
        if changed is None:
            return
        actor, confidence, reason = await self._audit(after.guild, discord.AuditLogAction.channel_update, after.id)
        await self._save(
            after.guild,
            category="channel_events",
            event_type="channel_update",
            actor_id=getattr(actor, "id", None),
            actor_confidence=confidence,
            channel_id=after.id,
            before=changed[0],
            after=changed[1],
            metadata=_meta({"actor": snapshot_user(actor), "channel": snapshot_channel(after)}, reason=reason),
        )

    @commands.Cog.listener()
    async def on_guild_role_create(self, role: discord.Role):
        actor, confidence, reason = await self._audit(role.guild, discord.AuditLogAction.role_create, role.id)
        await self._save(
            role.guild,
            category="role_events",
            event_type="role_create",
            actor_id=getattr(actor, "id", None),
            actor_confidence=confidence,
            target_id=role.id,
            after=_role_state(role),
            metadata=_meta({"actor": snapshot_user(actor), "target": snapshot_role(role)}, reason=reason),
        )

    @commands.Cog.listener()
    async def on_guild_role_delete(self, role: discord.Role):
        actor, confidence, reason = await self._audit(role.guild, discord.AuditLogAction.role_delete, role.id)
        await self._save(
            role.guild,
            category="role_events",
            event_type="role_delete",
            actor_id=getattr(actor, "id", None),
            actor_confidence=confidence,
            target_id=role.id,
            before=_role_state(role),
            metadata=_meta({"actor": snapshot_user(actor), "target": snapshot_role(role)}, reason=reason),
        )

    @commands.Cog.listener()
    async def on_guild_role_update(self, before: discord.Role, after: discord.Role):
        changed = _changed(_role_state(before), _role_state(after))
        if changed is None:
            return
        actor, confidence, reason = await self._audit(after.guild, discord.AuditLogAction.role_update, after.id)
        await self._save(
            after.guild,
            category="role_events",
            event_type="role_update",
            actor_id=getattr(actor, "id", None),
            actor_confidence=confidence,
            target_id=after.id,
            before=changed[0],
            after=changed[1],
            metadata=_meta({"actor": snapshot_user(actor), "target": snapshot_role(after)}, reason=reason),
        )

    @commands.Cog.listener()
    async def on_guild_update(self, before: discord.Guild, after: discord.Guild):
        def state(guild: discord.Guild) -> dict:
            return {
                "name": guild.name,
                "description": guild.description,
                "verification_level": getattr(guild.verification_level, "name", str(guild.verification_level)),
                "explicit_content_filter": getattr(guild.explicit_content_filter, "name", str(guild.explicit_content_filter)),
                "afk_timeout": guild.afk_timeout,
                "afk_channel": getattr(guild.afk_channel, "name", None),
                "system_channel": getattr(guild.system_channel, "name", None),
                "icon": getattr(guild.icon, "key", None),
                "banner": getattr(guild.banner, "key", None),
            }

        changed = _changed(state(before), state(after))
        if changed is None:
            return
        actor, confidence, reason = await self._audit(after, discord.AuditLogAction.guild_update, None)
        await self._save(
            after,
            category="guild_events",
            event_type="guild_update",
            actor_id=getattr(actor, "id", None),
            actor_confidence=confidence,
            before=changed[0],
            after=changed[1],
            metadata=_meta({"actor": snapshot_user(actor)}, reason=reason),
        )

    @commands.Cog.listener()
    async def on_voice_state_update(self, member: discord.Member, before: discord.VoiceState, after: discord.VoiceState):
        if before.channel == after.channel:
            await self._voice_flags(member, before, after)
            return
        if before.channel and after.channel is None:
            await self._voice_exit(member, before, after)
            return
        if before.channel and after.channel:
            await self._voice_switch(member, before, after)
            return
        await self._voice_self(member, before, after, "voice_join", f"{member.display_name} joined #{after.channel.name}")

    async def _voice_self(self, member, before, after, event_type: str, sentence: str):
        channel = after.channel or before.channel
        await self._save(
            member.guild,
            category="voice_events",
            event_type=event_type,
            actor_id=member.id,
            actor_confidence="certain",
            target_id=member.id,
            channel_id=channel.id if channel else None,
            before={"channel": snapshot_channel(before.channel)} if before.channel else None,
            after={"channel": snapshot_channel(after.channel)} if after.channel else None,
            metadata=_meta(
                {
                    "actor": snapshot_user(member),
                    "target": snapshot_user(member),
                    "channel": snapshot_channel(channel),
                },
                sentence=sentence,
                attribution="self",
            ),
        )

    async def _voice_exit(self, member, before, after):
        actor, confidence, reason = await self._audit(member.guild, discord.AuditLogAction.member_disconnect, member.id)
        if actor is not None and getattr(actor, "id", None) != member.id:
            await self._save(
                member.guild,
                category="voice_events",
                event_type="voice_disconnect",
                actor_id=actor.id,
                actor_confidence=confidence,
                target_id=member.id,
                channel_id=before.channel.id,
                before={"channel": snapshot_channel(before.channel)},
                metadata=_meta(
                    {
                        "actor": snapshot_user(actor),
                        "target": snapshot_user(member),
                        "channel": snapshot_channel(before.channel),
                    },
                    sentence=f"{getattr(actor, 'display_name', 'A moderator')} disconnected {member.display_name} from #{before.channel.name}",
                    reason=reason,
                ),
            )
            return
        if reason in {"__audit_unavailable__", "__ambiguous__"}:
            await self._save(
                member.guild,
                category="voice_events",
                event_type="voice_leave",
                actor_confidence="unknown",
                target_id=member.id,
                channel_id=before.channel.id,
                before={"channel": snapshot_channel(before.channel)},
                metadata=_meta(
                    {"target": snapshot_user(member), "channel": snapshot_channel(before.channel)},
                    sentence=f"{member.display_name} left #{before.channel.name}",
                    reason=reason,
                ),
            )
            return
        await self._voice_self(member, before, after, "voice_leave", f"{member.display_name} left #{before.channel.name}")

    async def _voice_switch(self, member, before, after):
        actor, confidence, reason = await self._audit(member.guild, discord.AuditLogAction.member_move, member.id)
        if actor is not None and getattr(actor, "id", None) != member.id:
            await self._save(
                member.guild,
                category="voice_events",
                event_type="voice_mod_move",
                actor_id=actor.id,
                actor_confidence=confidence,
                target_id=member.id,
                channel_id=after.channel.id,
                before={"channel": snapshot_channel(before.channel)},
                after={"channel": snapshot_channel(after.channel)},
                metadata=_meta(
                    {
                        "actor": snapshot_user(actor),
                        "target": snapshot_user(member),
                        "channel": snapshot_channel(after.channel),
                    },
                    sentence=f"{getattr(actor, 'display_name', 'A moderator')} moved {member.display_name} from #{before.channel.name} to #{after.channel.name}",
                    reason=reason,
                ),
            )
            return
        if reason in {"__audit_unavailable__", "__ambiguous__"}:
            await self._save(
                member.guild,
                category="voice_events",
                event_type="voice_move",
                actor_confidence="unknown",
                target_id=member.id,
                channel_id=after.channel.id,
                before={"channel": snapshot_channel(before.channel)},
                after={"channel": snapshot_channel(after.channel)},
                metadata=_meta(
                    {"target": snapshot_user(member), "channel": snapshot_channel(after.channel)},
                    sentence=f"{member.display_name} changed voice channels",
                    reason=reason,
                ),
            )
            return
        await self._voice_self(
            member,
            before,
            after,
            "voice_move",
            f"{member.display_name} moved from #{before.channel.name} to #{after.channel.name}",
        )

    async def _voice_flags(self, member, before, after):
        pairs = (
            ("mute", "voice_server_mute", "voice_server_unmute", "server mute"),
            ("deaf", "voice_server_deafen", "voice_server_undeafen", "server deafen"),
            ("self_mute", "voice_self_mute", "voice_self_unmute", "self mute"),
            ("self_deaf", "voice_self_deafen", "voice_self_undeafen", "self deafen"),
            ("self_stream", "voice_stream", None, "streaming"),
            ("self_video", "voice_camera", None, "camera"),
        )
        channel = after.channel
        for attr, on_type, off_type, label in pairs:
            previous = bool(getattr(before, attr, False))
            current = bool(getattr(after, attr, False))
            if previous == current:
                continue
            enabled = current
            event_type = on_type if enabled or off_type is None else off_type
            if attr in {"mute", "deaf"}:
                actor, confidence, reason = await self._audit(member.guild, discord.AuditLogAction.member_update, member.id)
                actor_id = getattr(actor, "id", None)
                entities = {"target": snapshot_user(member), "channel": snapshot_channel(channel)}
                if actor is not None:
                    entities["actor"] = snapshot_user(actor)
                sentence = f"{getattr(actor, 'display_name', 'Someone')} changed {label} for {member.display_name}"
            else:
                actor_id = member.id
                confidence = "certain"
                reason = "__self__"
                entities = {"actor": snapshot_user(member), "target": snapshot_user(member), "channel": snapshot_channel(channel)}
                sentence = f"{member.display_name} changed {label}"
            await self._save(
                member.guild,
                category="voice_events",
                event_type=event_type,
                actor_id=actor_id,
                actor_confidence=confidence if actor_id else "unknown",
                target_id=member.id,
                channel_id=channel.id if channel else None,
                metadata=_meta(entities, sentence=sentence, reason=reason),
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
            attachments=_files(message),
        )

    @commands.Cog.listener()
    async def on_message_edit(self, before: discord.Message, after: discord.Message):
        if after.guild is None or after.author.bot or before.content == after.content:
            return
        if await self._ignored_message(after.guild, after.channel.id, after.author):
            return
        await remember_message(
            guild_id=after.guild.id,
            message_id=after.id,
            channel_id=after.channel.id,
            author_id=after.author.id,
            content=after.content or "",
            attachments=_files(after),
        )
        await self._save(
            after.guild,
            category="message_events",
            event_type="message_edit",
            actor_id=after.author.id,
            actor_confidence="certain",
            target_id=after.id,
            channel_id=after.channel.id,
            before={"content": (before.content or "")[:1000]},
            after={"content": (after.content or "")[:1000]},
            metadata=_meta(
                {"actor": snapshot_user(after.author), "channel": snapshot_channel(after.channel)},
                jump_url=after.jump_url,
            ),
        )

    @commands.Cog.listener()
    async def on_raw_message_delete(self, payload: discord.RawMessageDeleteEvent):
        if payload.guild_id is None:
            return
        guild = self.bot.get_guild(payload.guild_id)
        if guild is None:
            return
        cached = payload.cached_message
        author = cached.author if cached is not None else None
        if author is not None and author.bot:
            return
        if author is not None and await self._ignored_message(guild, payload.channel_id, author):
            return
        stored = await stored_message_record(payload.guild_id, payload.message_id)
        if author is None and stored is None:
            author_id = None
        else:
            author_id = author.id if author is not None else stored["author_id"]
        if author is None and stored is not None:
            ignored = message_ignored(
                channel_id=payload.channel_id,
                author_id=author_id,
                author_role_ids=[],
                ignores=await ignores(guild.id),
            )
            if ignored:
                return
        actor, confidence, reason = await self._message_actor(
            guild, discord.AuditLogAction.message_delete, payload.channel_id, author_id
        )
        channel = guild.get_channel(payload.channel_id)
        content = cached.content if cached is not None and cached.content else (stored or {}).get("content")
        attachments = _files(cached) if cached is not None else (stored or {}).get("attachments") or []
        author_entity = snapshot_user(author) if author is not None else None
        if author_entity is None and author_id is not None:
            author_entity = {"id": str(author_id), "display_name": "Unknown member", "username": None, "avatar_url": None}
        await self._save(
            guild,
            category="message_events",
            event_type="message_delete",
            actor_id=getattr(actor, "id", None),
            actor_confidence=confidence if actor is not None else "unknown",
            target_id=payload.message_id,
            channel_id=payload.channel_id,
            metadata=_meta(
                {
                    "actor": snapshot_user(actor),
                    "target": author_entity,
                    "author": author_entity,
                    "channel": snapshot_channel(channel),
                },
                content=content,
                attachments=attachments,
                reason=reason,
            ),
        )

    @commands.Cog.listener()
    async def on_raw_bulk_message_delete(self, payload: discord.RawBulkMessageDeleteEvent):
        if payload.guild_id is None:
            return
        guild = self.bot.get_guild(payload.guild_id)
        if guild is None:
            return
        if message_ignored(channel_id=payload.channel_id, author_id=None, author_role_ids=[], ignores=await ignores(guild.id)):
            return
        actor, confidence, reason = await self._message_actor(
            guild, discord.AuditLogAction.message_bulk_delete, payload.channel_id, None
        )
        channel = guild.get_channel(payload.channel_id)
        await self._save(
            guild,
            category="message_events",
            event_type="message_bulk_delete",
            actor_id=getattr(actor, "id", None),
            actor_confidence=confidence if actor is not None else "unknown",
            channel_id=payload.channel_id,
            metadata=_meta(
                {"actor": snapshot_user(actor), "channel": snapshot_channel(channel)},
                count=len(payload.message_ids),
                reason=reason,
            ),
        )


    @commands.Cog.listener()
    async def on_thread_create(self, thread: discord.Thread):
        await self._object_event(thread.guild, "channel_events", "thread_create", discord.AuditLogAction.thread_create, thread.id, f"Thread {thread.name} was created", channel_id=thread.id)

    @commands.Cog.listener()
    async def on_thread_update(self, before: discord.Thread, after: discord.Thread):
        changed = _changed({"name": before.name, "archived": before.archived}, {"name": after.name, "archived": after.archived})
        if changed is None:
            return
        await self._object_event(
            after.guild,
            "channel_events",
            "thread_update",
            discord.AuditLogAction.thread_update,
            after.id,
            f"Thread {after.name} was updated",
            channel_id=after.id,
            before=changed[0],
            after=changed[1],
        )

    @commands.Cog.listener()
    async def on_thread_delete(self, thread: discord.Thread):
        await self._object_event(thread.guild, "channel_events", "thread_delete", discord.AuditLogAction.thread_delete, thread.id, f"Thread {thread.name} was deleted", channel_id=thread.id)

    @commands.Cog.listener()
    async def on_invite_create(self, invite: discord.Invite):
        if invite.guild is None:
            return
        await self._object_event(
            invite.guild,
            "guild_events",
            "invite_create",
            discord.AuditLogAction.invite_create,
            None,
            f"Invite {invite.code} was created",
            channel_id=getattr(invite.channel, "id", None),
        )

    @commands.Cog.listener()
    async def on_invite_delete(self, invite: discord.Invite):
        if invite.guild is None:
            return
        await self._object_event(
            invite.guild,
            "guild_events",
            "invite_delete",
            discord.AuditLogAction.invite_delete,
            None,
            f"Invite {invite.code} was deleted",
            channel_id=getattr(invite.channel, "id", None),
        )

    @commands.Cog.listener()
    async def on_guild_emojis_update(self, guild: discord.Guild, before, after):
        await self._collection(guild, before, after, "emoji", discord.AuditLogAction.emoji_create, discord.AuditLogAction.emoji_update, discord.AuditLogAction.emoji_delete)

    @commands.Cog.listener()
    async def on_guild_stickers_update(self, guild: discord.Guild, before, after):
        await self._collection(guild, before, after, "sticker", discord.AuditLogAction.sticker_create, discord.AuditLogAction.sticker_update, discord.AuditLogAction.sticker_delete)

    @commands.Cog.listener()
    async def on_webhooks_update(self, channel: discord.abc.GuildChannel):
        await self._audit_kind(
            channel.guild,
            channel.id,
            (
                ("webhook_create", discord.AuditLogAction.webhook_create, "A webhook was created"),
                ("webhook_update", discord.AuditLogAction.webhook_update, "A webhook was updated"),
                ("webhook_delete", discord.AuditLogAction.webhook_delete, "A webhook was deleted"),
            ),
            "guild_events",
            channel.id,
        )

    @commands.Cog.listener()
    async def on_scheduled_event_create(self, event: discord.ScheduledEvent):
        await self._object_event(event.guild, "guild_events", "scheduled_event_create", discord.AuditLogAction.scheduled_event_create, event.id, f"{event.name} was scheduled")

    @commands.Cog.listener()
    async def on_scheduled_event_update(self, before: discord.ScheduledEvent, after: discord.ScheduledEvent):
        changed = _changed({"name": before.name, "status": str(before.status)}, {"name": after.name, "status": str(after.status)})
        if changed is None:
            return
        await self._object_event(
            after.guild,
            "guild_events",
            "scheduled_event_update",
            discord.AuditLogAction.scheduled_event_update,
            after.id,
            f"{after.name} was updated",
            before=changed[0],
            after=changed[1],
        )

    @commands.Cog.listener()
    async def on_scheduled_event_delete(self, event: discord.ScheduledEvent):
        await self._object_event(event.guild, "guild_events", "scheduled_event_delete", discord.AuditLogAction.scheduled_event_delete, event.id, f"{event.name} was deleted")

    @commands.Cog.listener()
    async def on_guild_channel_pins_update(self, channel, last_pin):
        guild = getattr(channel, "guild", None)
        if guild is None:
            return
        await self._audit_kind(
            guild,
            channel.id,
            (
                ("message_pin", discord.AuditLogAction.message_pin, f"A message was pinned in #{channel.name}"),
                ("message_unpin", discord.AuditLogAction.message_unpin, f"A message was unpinned in #{channel.name}"),
            ),
            "message_events",
            channel.id,
        )

    async def _object_event(self, guild, category, event_type, action, target_id, sentence, channel_id=None, before=None, after=None):
        actor, confidence, reason = await self._audit(guild, action, target_id)
        await self._save(
            guild,
            category=category,
            event_type=event_type,
            actor_id=getattr(actor, "id", None),
            actor_confidence=confidence if actor is not None else "unknown",
            target_id=target_id,
            channel_id=channel_id,
            before=before,
            after=after,
            metadata=_meta({"actor": snapshot_user(actor)}, sentence=sentence, reason=reason),
        )

    async def _collection(self, guild, before, after, kind, created, updated, deleted):
        old = {item.id: item for item in before}
        new = {item.id: item for item in after}
        for item_id, item in new.items():
            if item_id not in old:
                await self._object_event(guild, "guild_events", f"{kind}_create", created, item_id, f"{kind.capitalize()} {item.name} was created")
            elif getattr(old[item_id], "name", None) != item.name:
                await self._object_event(
                    guild,
                    "guild_events",
                    f"{kind}_update",
                    updated,
                    item_id,
                    f"{kind.capitalize()} {old[item_id].name} was renamed to {item.name}",
                    before={"name": old[item_id].name},
                    after={"name": item.name},
                )
        for item_id, item in old.items():
            if item_id not in new:
                await self._object_event(guild, "guild_events", f"{kind}_delete", deleted, item_id, f"{kind.capitalize()} {item.name} was deleted")

    async def _audit_kind(self, guild, target_id, options, category, channel_id):
        found = []
        for event_type, action, sentence in options:
            actor, confidence, reason = await self._audit(guild, action, None, channel_id=target_id)
            if actor is not None or reason == "__ambiguous__":
                found.append((event_type, actor, confidence, reason, sentence))
        if len(found) != 1:
            return
        event_type, actor, confidence, reason, sentence = found[0]
        await self._save(
            guild,
            category=category,
            event_type=event_type,
            actor_id=getattr(actor, "id", None),
            actor_confidence=confidence if actor is not None else "unknown",
            channel_id=channel_id,
            target_id=target_id,
            metadata=_meta({"actor": snapshot_user(actor)} if actor is not None else {}, sentence=sentence, reason=reason),
        )


async def setup(bot):
    await bot.add_cog(LoggingV2(bot))
