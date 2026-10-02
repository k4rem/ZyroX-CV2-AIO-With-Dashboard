"""Guild-scoped message templates, media, and CLS-owned Discord sends."""

from __future__ import annotations

import discord
from fastapi import APIRouter, Depends, File, HTTPException, Request, UploadFile
from fastapi.responses import Response
from pydantic import BaseModel

from api.dependencies import get_bot
from cls_platform import storage
from cls_platform.messages.deliver import DeliveryError, render_message
from cls_platform.messages.media import inspect_image, new_key, valid_key, MediaError
from cls_platform.messages.schema import MessageSchemaError, validate_payload, variable_values
from cls_platform.messages.store import (
    MessageError,
    create_template,
    delete_sent,
    delete_template,
    get_sent,
    get_template,
    list_sent,
    list_templates,
    mark_sent,
    record_sent,
    update_template,
)

router = APIRouter()
_MENTIONS = discord.AllowedMentions.none()


class TemplateBody(BaseModel):
    name: str
    payload: dict


class TemplatePatch(BaseModel):
    name: str | None = None
    payload: dict | None = None


class SendBody(BaseModel):
    channel_id: str
    template_id: str | None = None
    payload: dict | None = None


def _user(request: Request) -> int | None:
    auth = getattr(request.state, "dashboard_auth", None)
    return getattr(auth, "user_id", None)


def _errors(exc: Exception) -> HTTPException:
    if isinstance(exc, MessageSchemaError):
        return HTTPException(status_code=422, detail=exc.errors)
    text = str(exc)
    if "not found" in text.lower():
        return HTTPException(status_code=404, detail=text)
    return HTTPException(status_code=422, detail=text)


def _guild(bot, guild_id: int) -> discord.Guild:
    guild = bot.get_guild(guild_id)
    if guild is None:
        raise HTTPException(status_code=404, detail="Guild is not available to the bot.")
    return guild


async def _channel(guild: discord.Guild, channel_id: int):
    channel = guild.get_channel(channel_id)
    if channel is None or not hasattr(channel, "send"):
        raise HTTPException(status_code=422, detail="Choose a text channel.")
    me = guild.me
    if me is None or not channel.permissions_for(me).send_messages or not channel.permissions_for(me).embed_links:
        raise HTTPException(status_code=422, detail="CLS cannot send embeds in that channel.")
    return channel


def _namespace(guild_id: int) -> str:
    return f"g{guild_id}"


async def _discord_args(guild, payload: dict):
    try:
        return await render_message(guild.id, payload, variable_values(guild))
    except DeliveryError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.get("/{guild_id}/messages/context")
async def message_context(guild_id: int, bot=Depends(get_bot)):
    guild = _guild(bot, guild_id)
    values = variable_values(guild)
    return {"variables": [{"id": key, "value": value} for key, value in values.items()]}


@router.get("/{guild_id}/emojis")
async def guild_emojis(guild_id: int, bot=Depends(get_bot)):
    guild = _guild(bot, guild_id)
    return {
        "emojis": [
            {"id": str(emoji.id), "name": emoji.name, "url": str(emoji.url), "animated": bool(emoji.animated)}
            for emoji in getattr(guild, "emojis", ()) or ()
        ]
    }


@router.post("/{guild_id}/media")
async def upload_media(guild_id: int, file: UploadFile = File(...), bot=Depends(get_bot)):
    _guild(bot, guild_id)
    raw = await file.read()
    try:
        encoded = inspect_image(raw)
    except MediaError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    key = new_key()
    await storage.put(_namespace(guild_id), key, encoded)
    return {"key": key, "content_type": "image/png"}


@router.get("/{guild_id}/media/{key}")
async def read_media(guild_id: int, key: str):
    if not valid_key(key):
        raise HTTPException(status_code=404, detail="Image not found")
    data = await storage.get(_namespace(guild_id), key)
    if data is None:
        raise HTTPException(status_code=404, detail="Image not found")
    return Response(content=data, media_type="image/png")


@router.get("/{guild_id}/messages/templates")
async def templates(guild_id: int):
    return {"templates": await list_templates(guild_id)}


@router.post("/{guild_id}/messages/templates")
async def template_create(guild_id: int, body: TemplateBody, request: Request):
    try:
        return await create_template(guild_id=guild_id, name=body.name, payload=body.payload, created_by=_user(request))
    except (MessageError, MessageSchemaError) as exc:
        raise _errors(exc) from exc


@router.get("/{guild_id}/messages/templates/{template_id}")
async def template_get(guild_id: int, template_id: str):
    try:
        return await get_template(guild_id, template_id)
    except MessageError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.patch("/{guild_id}/messages/templates/{template_id}")
async def template_patch(guild_id: int, template_id: str, body: TemplatePatch):
    try:
        return await update_template(guild_id=guild_id, template_id=template_id, name=body.name, payload=body.payload)
    except (MessageError, MessageSchemaError) as exc:
        raise _errors(exc) from exc


@router.delete("/{guild_id}/messages/templates/{template_id}")
async def template_delete(guild_id: int, template_id: str):
    try:
        await delete_template(guild_id, template_id)
    except MessageError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return {"status": "deleted"}


@router.post("/{guild_id}/messages/send")
async def send_message(guild_id: int, body: SendBody, request: Request, bot=Depends(get_bot)):
    if not body.channel_id.isdigit():
        raise HTTPException(status_code=422, detail="Choose a channel.")
    guild = _guild(bot, guild_id)
    channel = await _channel(guild, int(body.channel_id))
    payload = body.payload
    if payload is None and body.template_id:
        try:
            payload = (await get_template(guild_id, body.template_id))["payload"]
        except MessageError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
    if payload is None:
        raise HTTPException(status_code=422, detail="Nothing to send.")
    try:
        content, embeds, view, files = await _discord_args(guild, payload)
    except MessageSchemaError as exc:
        raise _errors(exc) from exc
    try:
        message = await channel.send(content=content, embeds=embeds, view=view, files=files, allowed_mentions=_MENTIONS)
    except discord.HTTPException as exc:
        raise HTTPException(status_code=422, detail="Discord rejected the message.") from exc
    saved = await record_sent(
        guild_id=guild_id,
        channel_id=channel.id,
        message_id=message.id,
        template_id=body.template_id,
        payload=validate_payload(payload),
        sent_by=_user(request),
    )
    return saved


@router.get("/{guild_id}/messages/sent")
async def sent_list(guild_id: int, bot=Depends(get_bot)):
    guild = _guild(bot, guild_id)
    rows = await list_sent(guild_id)
    refreshed = []
    for row in rows:
        if row["missing"]:
            refreshed.append(row)
            continue
        channel = guild.get_channel(int(row["channel_id"]))
        missing = False
        if channel is not None and hasattr(channel, "fetch_message"):
            try:
                await channel.fetch_message(int(row["message_id"]))
            except discord.NotFound:
                missing = True
            except discord.HTTPException:
                missing = False
        if missing:
            row = await mark_sent(guild_id, row["id"], missing=True)
        refreshed.append(row)
    return {"sent": refreshed}


@router.patch("/{guild_id}/messages/sent/{sent_id}")
async def sent_edit(guild_id: int, sent_id: str, body: TemplatePatch, bot=Depends(get_bot)):
    if body.payload is None:
        raise HTTPException(status_code=422, detail="Nothing to update.")
    guild = _guild(bot, guild_id)
    try:
        row = await get_sent(guild_id, sent_id)
    except MessageError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    channel = guild.get_channel(row.channel_id)
    if channel is None or not hasattr(channel, "fetch_message"):
        raise HTTPException(status_code=422, detail="Channel unavailable.")
    try:
        message = await channel.fetch_message(row.message_id)
    except discord.NotFound:
        await mark_sent(guild_id, sent_id, missing=True)
        raise HTTPException(status_code=404, detail="That Discord message is missing.")
    except discord.HTTPException as exc:
        raise HTTPException(status_code=422, detail="Could not load the Discord message.") from exc
    if message.author.id != getattr(guild.me, "id", None):
        raise HTTPException(status_code=403, detail="CLS can only edit messages it sent.")
    try:
        content, embeds, view, files = await _discord_args(guild, body.payload)
    except MessageSchemaError as exc:
        raise _errors(exc) from exc
    try:
        await message.edit(content=content, embeds=embeds, view=view, attachments=files, allowed_mentions=_MENTIONS)
    except discord.HTTPException as exc:
        raise HTTPException(status_code=422, detail="Discord rejected the update.") from exc
    return await mark_sent(guild_id, sent_id, payload=validate_payload(body.payload), edited=True, missing=False)


@router.post("/{guild_id}/messages/sent/{sent_id}/remove")
async def sent_remove(guild_id: int, sent_id: str, bot=Depends(get_bot)):
    """Delete the Discord message CLS sent and mark the registry row missing."""
    guild = _guild(bot, guild_id)
    try:
        row = await get_sent(guild_id, sent_id)
    except MessageError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    channel = guild.get_channel(row.channel_id)
    if channel is not None and hasattr(channel, "fetch_message"):
        try:
            message = await channel.fetch_message(row.message_id)
            if message.author.id == getattr(guild.me, "id", None):
                await message.delete()
        except discord.NotFound:
            pass
        except discord.HTTPException as exc:
            raise HTTPException(status_code=422, detail="Could not delete the Discord message.") from exc
    return await mark_sent(guild_id, sent_id, missing=True)


@router.post("/{guild_id}/messages/sent/{sent_id}/resend")
async def sent_resend(guild_id: int, sent_id: str, request: Request, bot=Depends(get_bot)):
    guild = _guild(bot, guild_id)
    try:
        row = await get_sent(guild_id, sent_id)
    except MessageError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    channel = await _channel(guild, row.channel_id)
    try:
        content, embeds, view, files = await _discord_args(guild, row.payload)
    except MessageSchemaError as exc:
        raise _errors(exc) from exc
    try:
        message = await channel.send(content=content, embeds=embeds, view=view, files=files, allowed_mentions=_MENTIONS)
    except discord.HTTPException as exc:
        raise HTTPException(status_code=422, detail="Discord rejected the message.") from exc
    return await mark_sent(
        guild_id,
        sent_id,
        message_id=message.id,
        channel_id=channel.id,
        missing=False,
        edited=True,
    )


@router.delete("/{guild_id}/messages/sent/{sent_id}")
async def sent_delete(guild_id: int, sent_id: str):
    try:
        await delete_sent(guild_id, sent_id)
    except MessageError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return {"status": "deleted"}
