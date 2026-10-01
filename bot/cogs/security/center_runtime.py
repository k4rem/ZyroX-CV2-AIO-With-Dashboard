"""Bot Trap and phishing detection. Live punishment stays behind the ENFORCE lock."""

from __future__ import annotations

import discord
from discord.ext import commands

from cls_platform.security.center import get_settings, is_trusted, note_signal, phishing_match, trap_action
from cls_platform.security.config import ensure_guild_config


class SecurityCenterRuntime(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.guild is None or message.author.id == self.bot.user.id:
            return
        settings = await get_settings(message.guild.id)
        trap_ids = {int(item) for item in settings["trap_channel_ids"]}
        if message.channel.id in trap_ids and (message.author.bot or message.webhook_id):
            config = await ensure_guild_config(message.guild.id)
            trusted = await is_trusted(message.guild.id, message.author.id)
            action = trap_action(
                author_is_bot=message.author.bot,
                webhook=message.webhook_id is not None,
                trusted=trusted,
                mode=config.bot_mode,
                enforce_locked=True,
            )
            if action != "ignore":
                await note_signal(
                    guild_id=message.guild.id,
                    subject_id=message.author.id,
                    engine="bot",
                    kind="bot_trap" if action != "record_webhook" else "webhook_activity",
                    detail=action,
                )
            return
        if message.author.bot or not phishing_match(message.content or ""):
            return
        await note_signal(
            guild_id=message.guild.id,
            subject_id=message.author.id,
            engine="human",
            kind="phishing",
            detail=settings["phishing_action"],
        )


async def setup(bot):
    await bot.add_cog(SecurityCenterRuntime(bot))
