"""Welcome, direct message, and goodbye configuration plus test sends."""

from __future__ import annotations

import discord
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel

from api.dependencies import get_bot
from cls_platform.messages.deliver import DeliveryError
from cls_platform.messages.schema import MessageSchemaError, validate_payload
from cls_platform.welcome.runtime import can_send, send_rendered
from cls_platform.welcome.store import (
    GOODBYE_VARIABLES,
    WELCOME_VARIABLES,
    member_values,
    preview_values,
    read_channel,
    read_dm,
    read_goodbye,
    write_channel,
    write_dm,
    write_goodbye,
)

router = APIRouter()


class WelcomeBody(BaseModel):
    enabled: bool = False
    skip_bots: bool = False
    channel_id: str | None = None
    auto_delete_duration: int | None = None
    payload: dict


class DirectBody(BaseModel):
    enabled: bool = False
    payload: dict


class TestBody(BaseModel):
    mode: str
    target: str
    channel_id: str | None = None
    payload: dict


def _guild(bot, guild_id: int):
    guild = bot.get_guild(guild_id)
    if guild is None:
        raise HTTPException(status_code=404, detail="Guild is not available to the bot.")
    return guild


def _payload(payload: dict, enabled: bool) -> dict:
    if not enabled:
        return payload
    try:
        return validate_payload(payload)
    except MessageSchemaError as exc:
        raise HTTPException(status_code=422, detail=exc.errors) from exc


def _channel_id(value: str | None, enabled: bool) -> int | None:
    if not value:
        if enabled:
            raise HTTPException(status_code=422, detail="Choose a channel.")
        return None
    if not str(value).isdigit():
        raise HTTPException(status_code=422, detail="Choose a channel.")
    return int(value)


def _destinations(guild) -> list[dict]:
    names = {}
    for channel in getattr(guild, "channels", []) or []:
        kind = channel.type.value if hasattr(getattr(channel, "type", None), "value") else getattr(channel, "type", None)
        if str(kind) in {"4", "category"}:
            names[channel.id] = channel.name
    rows = []
    for channel in getattr(guild, "channels", []) or []:
        kind = channel.type.value if hasattr(getattr(channel, "type", None), "value") else getattr(channel, "type", None)
        if str(kind) not in {"0", "5", "text", "news", "guild_text", "guild_news"}:
            continue
        if not can_send(channel, guild):
            continue
        parent = getattr(channel, "category_id", None) or getattr(channel, "parent_id", None)
        rows.append(
            {
                "id": str(channel.id),
                "name": channel.name,
                "parent_name": names.get(parent),
            }
        )
    return rows


async def _member(guild, request: Request):
    auth = getattr(request.state, "dashboard_auth", None)
    user_id = getattr(auth, "user_id", None)
    if not user_id:
        return None
    getter = getattr(guild, "get_member", None)
    member = getter(int(user_id)) if getter else None
    if member is None and hasattr(guild, "fetch_member"):
        try:
            member = await guild.fetch_member(int(user_id))
        except discord.HTTPException:
            member = None
    return member


def _mark(guild, record: dict) -> dict:
    channel_id = record.get("channel_id")
    ok = True
    if channel_id:
        ok = can_send(guild.get_channel(int(channel_id)), guild)
    return {**record, "channel_ok": ok}


@router.get("/{guild_id}/welcome/home")
async def welcome_home(guild_id: int, request: Request, bot=Depends(get_bot)):
    guild = _guild(bot, guild_id)
    member = await _member(guild, request)
    if member is not None:
        values = preview_values(member_values(member, guild))
    else:
        values = preview_values(member_values(type("M", (), {"id": 0, "mention": "@member", "name": "member", "display_name": "member", "joined_at": None, "created_at": None, "display_avatar": None})(), guild))
    return {
        "welcome": _mark(guild, await read_channel(guild_id)),
        "dm": read_dm(guild_id),
        "goodbye": _mark(guild, await read_goodbye(guild_id)),
        "preview": values,
        "destinations": _destinations(guild),
    }


@router.put("/{guild_id}/welcome/channel")
async def save_channel(guild_id: int, body: WelcomeBody, bot=Depends(get_bot)):
    guild = _guild(bot, guild_id)
    channel_id = _channel_id(body.channel_id, body.enabled)
    if channel_id is not None and guild.get_channel(channel_id) is None:
        raise HTTPException(status_code=422, detail="That channel is not in this server.")
    if body.auto_delete_duration is not None and not 0 <= body.auto_delete_duration <= 86400:
        raise HTTPException(status_code=422, detail="Auto-delete must be between 0 and 86400 seconds.")
    saved = await write_channel(
        guild_id,
        enabled=body.enabled,
        skip_bots=body.skip_bots,
        channel_id=channel_id,
        auto_delete_duration=body.auto_delete_duration or None,
        payload=_payload(body.payload, body.enabled),
    )
    return _mark(guild, saved)


@router.put("/{guild_id}/welcome/dm")
async def save_dm(guild_id: int, body: DirectBody, bot=Depends(get_bot)):
    _guild(bot, guild_id)
    return write_dm(guild_id, enabled=body.enabled, payload=_payload(body.payload, body.enabled))


@router.put("/{guild_id}/welcome/goodbye")
async def save_goodbye(guild_id: int, body: WelcomeBody, bot=Depends(get_bot)):
    guild = _guild(bot, guild_id)
    channel_id = _channel_id(body.channel_id, body.enabled)
    if channel_id is not None and guild.get_channel(channel_id) is None:
        raise HTTPException(status_code=422, detail="That channel is not in this server.")
    saved = await write_goodbye(
        guild_id,
        enabled=body.enabled,
        skip_bots=body.skip_bots,
        channel_id=channel_id,
        payload=_payload(body.payload, body.enabled),
    )
    return _mark(guild, saved)


@router.post("/{guild_id}/welcome/test")
async def welcome_test(guild_id: int, body: TestBody, request: Request, bot=Depends(get_bot)):
    if body.mode not in {"welcome", "dm", "goodbye"} or body.target not in {"me", "channel"}:
        raise HTTPException(status_code=422, detail="Choose a test destination.")
    guild = _guild(bot, guild_id)
    member = await _member(guild, request)
    if member is None:
        raise HTTPException(status_code=422, detail="Join the server before sending a test.")
    allowed = GOODBYE_VARIABLES if body.mode == "goodbye" else WELCOME_VARIABLES
    try:
        payload = validate_payload(body.payload)
    except MessageSchemaError as exc:
        raise HTTPException(status_code=422, detail=exc.errors) from exc
    values = member_values(member, guild)
    try:
        if body.target == "me":
            await send_rendered(member, guild_id, payload, values, allowed)
        else:
            channel_id = _channel_id(body.channel_id, True)
            channel = guild.get_channel(channel_id)
            if not can_send(channel, guild):
                raise HTTPException(status_code=422, detail="CLS cannot send embeds in that channel.")
            await send_rendered(channel, guild_id, payload, values, allowed)
    except DeliveryError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except discord.Forbidden as exc:
        raise HTTPException(status_code=422, detail="Discord refused the test message.") from exc
    except discord.HTTPException as exc:
        raise HTTPException(status_code=422, detail="Discord rejected the test message.") from exc
    return {"status": "sent"}
