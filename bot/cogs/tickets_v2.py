"""Discord button for Tickets V2. Storage is Postgres only."""

from __future__ import annotations

import discord
from discord.ext import commands

from cls_platform.tickets.store import TicketError, load_panel, open_ticket


class TicketsV2(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_interaction(self, interaction: discord.Interaction):
        data = interaction.data or {}
        custom_id = str(data.get("custom_id") or "")
        if not custom_id.startswith("cls-ticket:") or interaction.guild is None or not isinstance(interaction.user, discord.Member):
            return
        panel = await load_panel(custom_id.split(":", 1)[1])
        if panel is None or panel["guild_id"] != interaction.guild.id:
            await interaction.response.send_message("This panel is not available.", ephemeral=True)
            return
        if panel["questions"] and not data.get("components"):
            modal = discord.ui.Modal(title=panel["title"][:45], custom_id=custom_id)
            for question in panel["questions"][:5]:
                modal.add_item(discord.ui.TextInput(label=question["label"][:45], required=question["required"], custom_id=question["label"][:45]))
            await interaction.response.send_modal(modal)
            return
        answers = {}
        for row in data.get("components") or []:
            for component in row.get("components") or []:
                answers[str(component.get("custom_id") or "answer")] = str(component.get("value") or "")
        parent = interaction.guild.get_channel(int(panel["discord_category_id"])) if panel["discord_category_id"] else None
        try:
            opened = await open_ticket(
                guild_id=interaction.guild.id,
                category_id=panel["category_id"],
                opener_id=interaction.user.id,
                answers=answers,
            )
        except TicketError:
            await interaction.response.send_message("You already have an open ticket in this category.", ephemeral=True)
            return
        channel = None
        if parent is not None:
            channel = await interaction.guild.create_text_channel(
                opened["name"],
                category=parent,
                reason=f"CLS ticket {opened['number']}",
            )
        if interaction.response.is_done():
            await interaction.followup.send(f"Ticket {opened['name']} is open.", ephemeral=True)
        else:
            await interaction.response.send_message(f"Ticket {opened['name']} is open.", ephemeral=True)
        if channel is not None:
            await channel.send(f"Ticket opened by {interaction.user.mention}")


async def setup(bot):
    await bot.add_cog(TicketsV2(bot))
