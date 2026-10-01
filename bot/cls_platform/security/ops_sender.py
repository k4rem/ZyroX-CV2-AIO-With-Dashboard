"""Send Ops alerts only to the configured channel inside OPS_GUILD_ID."""

from __future__ import annotations

import json
import logging

from cls_platform.config import OPS_GUILD_ID, OPS_SECURITY_ALERT_CHANNEL_ID
from cls_platform.security.alerts import configure_alert_sender, destination_is_valid

logger = logging.getLogger(__name__)


class DiscordOpsSender:
    """Resolves one Ops channel. Never falls back to a product guild or webhook."""

    def __init__(self, bot) -> None:
        self.bot = bot

    async def resolve(self):
        if OPS_GUILD_ID is None or OPS_SECURITY_ALERT_CHANNEL_ID is None:
            return None
        guild = self.bot.get_guild(int(OPS_GUILD_ID))
        if guild is None:
            return None
        channel = guild.get_channel(int(OPS_SECURITY_ALERT_CHANNEL_ID))
        if channel is None:
            getter = getattr(guild, "fetch_channel", None)
            if getter is None:
                return None
            try:
                channel = await getter(int(OPS_SECURITY_ALERT_CHANNEL_ID))
            except Exception:
                logger.warning("Ops alert channel could not be resolved")
                return None
        if not destination_is_valid(channel):
            return None
        return channel

    async def send(self, channel, payload, allowed_mentions: str = "none") -> None:
        import discord

        if not destination_is_valid(channel):
            raise RuntimeError("refusing to send outside the Ops security channel")
        text = json.dumps(payload, default=str, sort_keys=True)
        if len(text) > 1800:
            text = text[:1800] + "…"
        await channel.send(content=text, allowed_mentions=discord.AllowedMentions.none())


def install_ops_sender(bot) -> DiscordOpsSender:
    sender = DiscordOpsSender(bot)
    configure_alert_sender(sender)
    return sender
