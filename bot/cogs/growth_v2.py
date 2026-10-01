"""Persist invite joins and close giveaways after restart."""

from __future__ import annotations

import asyncio
import logging

import discord
from discord.ext import commands

from cls_platform.growth import close_due, note_join, sync_codes

logger = logging.getLogger(__name__)


class GrowthV2(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self._uses: dict[int, dict[str, int]] = {}
        self._task: asyncio.Task | None = None

    async def cog_load(self):
        self._task = asyncio.create_task(self._loop())

    async def cog_unload(self):
        if self._task is not None:
            self._task.cancel()

    async def _loop(self):
        await self.bot.wait_until_ready()
        for guild in self.bot.guilds:
            await self._refresh(guild)
        while True:
            try:
                await close_due()
            except Exception:
                logger.exception("giveaway close failed")
            await asyncio.sleep(30)

    async def _refresh(self, guild: discord.Guild) -> dict[str, int]:
        try:
            invites = await guild.invites()
        except (discord.Forbidden, discord.HTTPException):
            return self._uses.get(guild.id, {})
        codes = [
            {"code": invite.code, "uses": invite.uses or 0, "inviter_id": invite.inviter.id if invite.inviter else None}
            for invite in invites
        ]
        await sync_codes(guild.id, codes)
        current = {invite.code: invite.uses or 0 for invite in invites}
        self._uses[guild.id] = current
        return current

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        before = dict(self._uses.get(member.guild.id, {}))
        after = await self._refresh(member.guild)
        if not before:
            await note_join(member.guild.id, member.id, after, after)
            return
        await note_join(member.guild.id, member.id, before, after)


async def setup(bot):
    await bot.add_cog(GrowthV2(bot))
