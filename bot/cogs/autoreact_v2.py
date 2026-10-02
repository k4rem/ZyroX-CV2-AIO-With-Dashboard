"""React to member messages that match a saved rule."""

from __future__ import annotations

import logging

import discord
from discord.ext import commands

from cls_platform.autoreact import matching_rules

logger = logging.getLogger(__name__)


class AutoReactV2(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.guild is None or message.author.bot or message.author.id == self.bot.user.id:
            return
        rules = await matching_rules(message.guild.id, message.content or "", message.channel.id)
        for rule in rules:
            for emoji in rule["emojis"]:
                try:
                    token = discord.PartialEmoji.from_str(emoji) if emoji.startswith("<") else emoji
                    await message.add_reaction(token)
                except (discord.HTTPException, discord.NotFound):
                    logger.info("auto react skipped an unavailable emoji")


async def setup(bot):
    await bot.add_cog(AutoReactV2(bot))
