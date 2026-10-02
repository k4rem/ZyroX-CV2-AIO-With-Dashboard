"""Send welcome, direct-message, and goodbye through the shared message renderer."""

from __future__ import annotations

import discord

from cls_platform.messages.deliver import render_message
from cls_platform.messages.schema import MessageSchemaError
from cls_platform.welcome.store import (
    GOODBYE_VARIABLES,
    WELCOME_VARIABLES,
    member_values,
    read_channel,
    read_dm,
    read_goodbye,
)

_MENTIONS = discord.AllowedMentions(everyone=False, users=True, roles=False)


def can_send(channel, guild) -> bool:
    me = getattr(guild, "me", None)
    if channel is None or not hasattr(channel, "send") or me is None:
        return False
    perms = channel.permissions_for(me)
    return bool(perms.send_messages and perms.embed_links)


async def send_rendered(target, guild_id: int, payload: dict, values: dict, allowed):
    content, embeds, view, files = await render_message(guild_id, payload, values, allowed)
    kwargs = {"content": content, "embeds": embeds, "files": files, "allowed_mentions": _MENTIONS}
    if view is not None:
        kwargs["view"] = view
    return await target.send(**kwargs)


async def send_channel_welcome(member):
    record = await read_channel(member.guild.id)
    if not record["enabled"] or (record["skip_bots"] and member.bot) or not record["channel_id"]:
        return None
    channel = member.guild.get_channel(int(record["channel_id"]))
    if not can_send(channel, member.guild):
        return None
    message = await send_rendered(
        channel,
        member.guild.id,
        record["payload"],
        member_values(member, member.guild),
        WELCOME_VARIABLES,
    )
    if record["auto_delete_duration"]:
        await message.delete(delay=record["auto_delete_duration"])
    return message


async def send_direct_welcome(member):
    record = read_dm(member.guild.id)
    if not record["enabled"] or member.bot:
        return None
    return await send_rendered(
        member,
        member.guild.id,
        record["payload"],
        member_values(member, member.guild),
        WELCOME_VARIABLES,
    )


async def send_goodbye(member):
    record = await read_goodbye(member.guild.id)
    if not record["enabled"] or (record["skip_bots"] and member.bot) or not record["channel_id"]:
        return None
    channel = member.guild.get_channel(int(record["channel_id"]))
    if not can_send(channel, member.guild):
        return None
    return await send_rendered(
        channel,
        member.guild.id,
        record["payload"],
        member_values(member, member.guild),
        GOODBYE_VARIABLES,
    )


def ignored(exc: Exception) -> bool:
    return isinstance(exc, (discord.Forbidden, discord.HTTPException, MessageSchemaError, ValueError))
