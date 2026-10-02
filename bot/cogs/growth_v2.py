"""Persist invite joins and close giveaways after restart."""

from __future__ import annotations

import asyncio
import logging

import discord
from discord.ext import commands

from cls_platform.giveaways_runtime import sync_message
from cls_platform.growth import (
    due_giveaways,
    end_giveaway,
    enter_giveaway,
    entry_block,
    entry_user_ids,
    giveaway_for,
    leave_giveaway,
    invite_log_channel,
    note_join,
    note_leave,
    promote_scheduled,
    sync_codes,
    unpublished_giveaways,
)

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
                await self._giveaways()
            except Exception:
                logger.exception("giveaway close failed")
            await asyncio.sleep(15)

    async def _allowed(self, row: dict) -> set[int] | None:
        guild = self.bot.get_guild(int(row["guild_id"]))
        if guild is None:
            return None
        required = int(row["required_role_id"]) if row.get("required_role_id") else None
        blocked = int(row["blocked_role_id"]) if row.get("blocked_role_id") else None
        user_ids = await entry_user_ids(row["id"])
        allowed: set[int] = set()
        for user_id in user_ids:
            member = guild.get_member(user_id)
            if member is None:
                try:
                    member = await guild.fetch_member(user_id)
                except (discord.NotFound, discord.HTTPException):
                    continue
            roles = {role.id for role in member.roles}
            if entry_block(roles, required=required, blocked=blocked, is_bot=member.bot) is None:
                allowed.add(member.id)
        return allowed

    async def _giveaways(self):
        for row in await due_giveaways():
            allowed = await self._allowed(row)
            await end_giveaway(int(row["guild_id"]), row["id"], eligible=allowed)
            await sync_message(self.bot, int(row["guild_id"]), row["id"])
        await promote_scheduled()
        for row in await unpublished_giveaways():
            await sync_message(self.bot, int(row["guild_id"]), row["id"])

    @commands.Cog.listener()
    async def on_interaction(self, interaction: discord.Interaction):
        if interaction.type is not discord.InteractionType.component or interaction.guild is None:
            return
        custom_id = str((interaction.data or {}).get("custom_id") or "")
        parts = custom_id.split(":")
        if len(parts) != 4 or parts[0] != "cls" or parts[1] != "gw":
            return
        action, giveaway_id = parts[2], parts[3]
        member = interaction.user
        if not isinstance(member, discord.Member):
            return
        row = await giveaway_for(interaction.guild.id, giveaway_id)
        if row is None or row["status"] != "open":
            await interaction.response.send_message("This giveaway is closed.", ephemeral=True)
            return
        if action == "enter":
            reason = entry_block(
                {role.id for role in member.roles},
                required=int(row["required_role_id"]) if row.get("required_role_id") else None,
                blocked=int(row["blocked_role_id"]) if row.get("blocked_role_id") else None,
                is_bot=member.bot,
            )
            if reason:
                await interaction.response.send_message(reason, ephemeral=True)
                return
            result = await enter_giveaway(interaction.guild.id, giveaway_id, member.id)
            text = "You're in." if result == "entered" else "You're already entered."
        elif action == "leave":
            result = await leave_giveaway(interaction.guild.id, giveaway_id, member.id)
            text = "You left this giveaway." if result == "left" else "You weren't entered."
        else:
            return
        await interaction.response.send_message(text, ephemeral=True)
        await sync_message(self.bot, interaction.guild.id, giveaway_id)

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
            recorded = await note_join(member.guild.id, member.id, after, after)
        else:
            recorded = await note_join(member.guild.id, member.id, before, after)
        await self._invite_log(member, recorded)

    @commands.Cog.listener()
    async def on_member_remove(self, member: discord.Member):
        if member.bot:
            return
        await note_leave(member.guild.id, member.id)

    async def _invite_log(self, member: discord.Member, recorded: dict) -> None:
        channel_id = await invite_log_channel(member.guild.id)
        if not channel_id:
            return
        channel = member.guild.get_channel(channel_id)
        if channel is None:
            return
        status = {"certain": "Confirmed", "ambiguous": "Ambiguous", "unknown": "Unknown"}.get(recorded.get("status"), "Unknown")
        if status == "Confirmed" and recorded.get("code"):
            text = f"{member.mention} joined. Attribution: Confirmed, invite `{recorded['code']}`."
        elif status == "Ambiguous":
            text = f"{member.mention} joined. Attribution: Ambiguous. More than one invite changed, so nobody was credited."
        else:
            text = f"{member.mention} joined. Attribution: Unknown. Discord did not show which invite was used."
        try:
            await channel.send(text)
        except discord.HTTPException:
            logger.exception("invite log failed")


async def setup(bot):
    await bot.add_cog(GrowthV2(bot))
