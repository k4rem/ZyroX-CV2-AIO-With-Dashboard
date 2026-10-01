"""Join and button flow for Verification V2. Starts disabled."""

from __future__ import annotations

from datetime import datetime, timezone

import discord
from discord.ext import commands

from cls_platform.verification.store import get_config, mark_verified, observe_member


class VerificationV2(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def _roots(self) -> set[int]:
        raw = getattr(self.bot, "owner_ids", None) or set()
        return {int(item) for item in raw}

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        decision = await observe_member(
            guild_id=member.guild.id,
            user_id=member.id,
            owner_id=member.guild.owner_id,
            root_ids=self._roots(),
            joined_at=datetime.now(timezone.utc),
            now=datetime.now(timezone.utc),
        )
        if decision != "assign_unverified":
            return
        config = await get_config(member.guild.id)
        role_id = config.get("unverified_role_id")
        if not role_id:
            return
        role = member.guild.get_role(int(role_id))
        if role is None or role >= member.guild.me.top_role:
            return
        await member.add_roles(role, reason="CLS verification: unverified")

    @commands.Cog.listener()
    async def on_interaction(self, interaction: discord.Interaction):
        data = interaction.data or {}
        custom_id = str(data.get("custom_id") or "")
        if not custom_id.startswith("cls-verify:"):
            return
        if interaction.guild is None or interaction.user is None:
            return
        if interaction.user.id == interaction.guild.owner_id or interaction.user.id in self._roots():
            await mark_verified(interaction.guild.id, interaction.user.id)
            await interaction.response.send_message("Owner access is unchanged.", ephemeral=True)
            return
        config = await get_config(interaction.guild.id)
        if not config["enabled"]:
            await interaction.response.send_message("Verification is off.", ephemeral=True)
            return
        member = interaction.user
        unverified = interaction.guild.get_role(int(config["unverified_role_id"])) if config["unverified_role_id"] else None
        if isinstance(member, discord.Member) and unverified and unverified in member.roles:
            await member.remove_roles(unverified, reason="CLS verification passed")
        if config["verified_role_id"] and isinstance(member, discord.Member):
            verified = interaction.guild.get_role(int(config["verified_role_id"]))
            if verified and verified < interaction.guild.me.top_role:
                await member.add_roles(verified, reason="CLS verification status")
        await mark_verified(interaction.guild.id, interaction.user.id)
        await interaction.response.send_message("You are verified. Protected categories use their normal permissions.", ephemeral=True)


async def setup(bot):
    await bot.add_cog(VerificationV2(bot))
