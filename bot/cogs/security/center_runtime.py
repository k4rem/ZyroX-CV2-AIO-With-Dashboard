"""Human honeypot, bot trap, and phishing. Live member punishment stays behind the ENFORCE lock."""

from __future__ import annotations

import discord
from discord.ext import commands

from cls_platform.security.center import is_trusted
from cls_platform.security.guild_gate import security_guild_eligible
from cls_platform.security.workflows import handle_center_message


class SecurityCenterRuntime(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.guild is None or self.bot.user is None or message.author.id == self.bot.user.id:
            return
        if not security_guild_eligible(message.guild.id):
            return
        permissions = getattr(message.author, "guild_permissions", None)
        staff = bool(getattr(permissions, "administrator", False)) or message.author.id == getattr(message.guild, "owner_id", None)
        trusted = await is_trusted(message.guild.id, message.author.id)

        async def delete_message():
            await message.delete()

        await handle_center_message(
            guild_id=message.guild.id,
            channel_id=message.channel.id,
            author_id=message.author.id,
            content=message.content or "",
            author_is_bot=bool(message.author.bot),
            webhook=message.webhook_id is not None,
            trusted=trusted,
            staff=staff,
            eligible=True,
            delete_message=delete_message,
        )


async def setup(bot):
    await bot.add_cog(SecurityCenterRuntime(bot))
