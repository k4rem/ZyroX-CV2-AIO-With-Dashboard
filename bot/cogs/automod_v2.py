"""The only Automod enforcement listener."""

from __future__ import annotations

import logging

import discord
from discord.ext import commands

from cls_platform.automod.runtime import handle_message

logger = logging.getLogger("cls.automod.v2")


class _Target:
    def __init__(self, message: discord.Message):
        author = message.author
        guild = message.guild
        me = guild.me if guild else None
        self.guild_id = guild.id
        self.member_id = author.id
        self.channel_id = message.channel.id
        self.message_id = message.id
        self.content = message.content or ""
        self.member_name = getattr(author, "display_name", None) or getattr(author, "name", "member")
        self.channel_name = getattr(message.channel, "name", "channel")
        self.category_id = getattr(getattr(message.channel, "category", None), "id", 0) or 0
        self.role_ids = [role.id for role in getattr(author, "roles", []) or []]
        self.is_owner = author.id == getattr(guild, "owner_id", None)
        self.is_admin = bool(getattr(getattr(author, "guild_permissions", None), "administrator", False))
        self.hierarchy_ok = False
        self.manage_messages = False
        self.moderate_members = False
        self.kick_members = False
        self.ban_members = False
        self.send_messages = False
        self.attachments = [
            {"filename": item.filename, "content_type": getattr(item, "content_type", "") or ""}
            for item in message.attachments
        ]
        vanity = getattr(guild, "vanity_url_code", None)
        self.own_codes = [vanity] if vanity else []
        self._message = message
        if me is not None:
            perms = me.guild_permissions
            self.manage_messages = perms.manage_messages
            self.moderate_members = perms.moderate_members
            self.kick_members = perms.kick_members
            self.ban_members = perms.ban_members
            channel_perms = message.channel.permissions_for(me)
            self.send_messages = channel_perms.send_messages
            member_top = getattr(author, "top_role", None)
            bot_top = me.top_role
            if member_top is not None and bot_top is not None:
                if member_top.position < bot_top.position or (
                    member_top.position == bot_top.position and member_top.id < bot_top.id
                ):
                    self.hierarchy_ok = True

    async def delete_messages(self):
        await self._message.delete()

    async def timeout(self, seconds: int):
        import datetime as dt

        until = discord.utils.utcnow() + dt.timedelta(seconds=seconds)
        await self._message.author.timeout(until, reason="CLS Automod")

    async def kick(self):
        await self._message.author.kick(reason="CLS Automod")

    async def ban(self):
        await self._message.guild.ban(self._message.author, reason="CLS Automod", delete_message_days=0)

    async def dm(self):
        await self._message.author.send(f"A message in {self._message.guild.name} was caught by Automod.")

    async def notice(self):
        await self._message.channel.send(f"{self._message.author.mention} a message was caught by Automod.", delete_after=8)


class AutomodV2(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.guild is None or message.author.bot or message.webhook_id:
            return
        try:
            await handle_message(_Target(message))
        except Exception:
            logger.exception("automod v2 failed guild=%s message=%s", message.guild.id, message.id)
