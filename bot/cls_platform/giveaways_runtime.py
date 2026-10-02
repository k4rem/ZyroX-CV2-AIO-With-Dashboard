"""Publish giveaway messages and keep the entry buttons alive."""

from __future__ import annotations

import discord

from cls_platform.growth import attach_message, giveaway_for, message_body


def _view(row: dict) -> discord.ui.View:
    view = discord.ui.View(timeout=None)
    if row.get("status") == "open":
        view.add_item(
            discord.ui.Button(
                label="Enter",
                style=discord.ButtonStyle.primary,
                custom_id=f"cls:gw:enter:{row['id']}",
            )
        )
        view.add_item(
            discord.ui.Button(
                label="Leave",
                style=discord.ButtonStyle.secondary,
                custom_id=f"cls:gw:leave:{row['id']}",
            )
        )
    return view


def _content(row: dict) -> str:
    from datetime import datetime

    ends = datetime.fromisoformat(row["ends_at"])
    return message_body(
        prize=row["prize"],
        description=row.get("description") or "",
        winner_count=int(row.get("winner_count") or 1),
        ends_at=ends,
        host_id=int(row["host_id"]) if row.get("host_id") else None,
        entry_count=int(row.get("entry_count") or 0),
        status=row["status"],
        winner_ids=[int(item) for item in row.get("winner_ids") or []],
    )


async def sync_message(bot, guild_id: int, giveaway_id: str) -> None:
    row = await giveaway_for(guild_id, giveaway_id)
    if row is None or not row.get("channel_id") or row["status"] == "scheduled":
        return
    channel = bot.get_channel(int(row["channel_id"]))
    if channel is None:
        return
    content = _content(row)
    view = _view(row)
    if row.get("message_id"):
        try:
            message = await channel.fetch_message(int(row["message_id"]))
        except discord.NotFound:
            message = None
        if message is not None:
            await message.edit(content=content, view=view)
            return
    sent = await channel.send(content=content, view=view)
    await attach_message(guild_id, giveaway_id, sent.id)
