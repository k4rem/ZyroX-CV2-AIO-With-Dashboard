"""Role menu HTTP API. Legacy /reactionroles stays read-only for old clients."""

from __future__ import annotations

import re

import discord
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from api.dependencies import get_bot
from cls_platform.logging.store import record_event
from cls_platform.messages.deliver import DeliveryError
from cls_platform.role_menus.logic import custom_emoji_id
from cls_platform.role_menus.store import MenuError, create_menu, delete_menu, duplicate_menu, get_menu, list_menus, update_menu

router = APIRouter()
_LINK = re.compile(r"channels/(\d+)/(\d+)/(\d+)")


class OptionBody(BaseModel):
    role_id: str
    emoji: str = ""
    label: str = ""
    description: str = ""


class MenuBody(BaseModel):
    name: str = "Role menu"
    source: str = "created"
    type: str = "reaction"
    mode: str = "toggle"
    channel_id: str | None = None
    max_roles: int | None = None
    payload: dict | None = None
    button_style: str | None = None
    options: list[OptionBody] = Field(default_factory=list)


class MenuPatch(BaseModel):
    name: str | None = None
    mode: str | None = None
    type: str | None = None
    enabled: bool | None = None
    max_roles: int | None = None
    channel_id: str | None = None
    clear_channel: bool = False
    payload: dict | None = None
    button_style: str | None = None
    options: list[OptionBody] | None = None


class PublishBody(BaseModel):
    channel_id: str | None = None
    message_id: str | None = None


def _cog(bot):
    getter = getattr(bot, "get_cog", None)
    return getter("RoleMenus") if getter else None


async def _audit(guild_id: int, event_type: str, summary: str) -> None:
    try:
        await record_event(guild_id=guild_id, category="bot_actions", event_type=event_type, metadata={"summary": summary})
    except Exception:
        return


def _int(value: str | None) -> int | None:
    return int(value) if value and str(value).isdigit() else None


def _options(options: list[OptionBody] | None) -> list[dict] | None:
    if options is None:
        return None
    return [item.model_dump() for item in options]


def _health(bot, menu: dict) -> dict:
    warnings = []
    status = "Draft"
    if menu.get("publish_status") == "missing":
        status = "Message missing"
        warnings.append("The Discord message is gone.")
    elif menu.get("message_id"):
        status = "Published"
    if not menu.get("enabled"):
        status = "Disabled"
    guild = bot.get_guild(int(menu["guild_id"])) if bot is not None else None
    me = guild.me if guild else None
    if menu.get("message_id") and guild is not None:
        channel = guild.get_channel(int(menu["channel_id"])) if menu.get("channel_id") else None
        if channel is None and menu.get("channel_id"):
            status = "Message missing"
            warnings.append("The channel is not available to CLS.")
    emoji_ids = {str(emoji.id) for emoji in getattr(guild, "emojis", [])} if guild else set()
    for option in menu.get("options") or []:
        role = guild.get_role(int(option["role_id"])) if guild and str(option.get("role_id") or "").isdigit() else None
        if guild and role is None:
            warnings.append("A role on this menu is missing.")
            if status == "Published":
                status = "Missing role"
        elif role is not None and getattr(role, "managed", False):
            warnings.append(f"{role.name} is managed and cannot be assigned.")
        elif role is not None and me is not None and me.top_role and not (role.position < me.top_role.position or (role.position == me.top_role.position and int(role.id) < int(me.top_role.id))):
            warnings.append(f"{role.name} is above CLS.")
            if status == "Published":
                status = "Hierarchy problem"
        emoji_id = custom_emoji_id(option.get("emoji") or "")
        if emoji_id and guild is not None and emoji_id not in emoji_ids:
            warnings.append("A custom emoji is missing.")
            if status == "Published":
                status = "Missing emoji"
    shown = dict(menu)
    shown["status"] = status
    shown["warnings"] = list(dict.fromkeys(warnings))
    return shown


async def _annotate(bot, menu: dict) -> dict:
    shown = _health(bot, menu)
    cog = _cog(bot)
    if cog is None or not menu.get("message_id"):
        return shown
    guild = bot.get_guild(int(menu["guild_id"])) if bot is not None else None
    _message, status = await cog._fetch(guild, shown)
    if status == "missing" and shown["status"] != "Disabled":
        shown["status"] = "Message missing"
        shown["publish_status"] = "missing"
        shown["warnings"] = ["The Discord message is gone.", *shown["warnings"]]
    return shown


def _bot_position(bot, guild_id: int) -> int:
    guild = bot.get_guild(int(guild_id)) if bot is not None else None
    me = getattr(guild, "me", None) if guild is not None else None
    top = getattr(me, "top_role", None) if me is not None else None
    return int(getattr(top, "position", 0) or 0)


@router.get("/{guild_id}/reactionroles/v2")
async def menus_list(guild_id: int, bot=Depends(get_bot)):
    return {"menus": [await _annotate(bot, menu) for menu in await list_menus(guild_id)], "bot_position": _bot_position(bot, guild_id)}


@router.get("/{guild_id}/reactionroles/v2/messages")
async def menus_messages(guild_id: int, channel_id: str = "", link: str = "", bot=Depends(get_bot)):
    guild = bot.get_guild(int(guild_id)) if bot is not None else None
    if guild is None:
        return {"messages": []}
    match = _LINK.search(link or "")
    if match:
        if match.group(1) != str(guild_id):
            raise HTTPException(status_code=404, detail="That message is not in this server.")
        channel = guild.get_channel(int(match.group(2)))
        if channel is None or not hasattr(channel, "fetch_message"):
            raise HTTPException(status_code=404, detail="CLS cannot see that channel.")
        try:
            message = await channel.fetch_message(int(match.group(3)))
        except discord.NotFound:
            raise HTTPException(status_code=404, detail="That message was not found.") from None
        return {"messages": [_message(message)]}
    channel = guild.get_channel(int(channel_id)) if channel_id.isdigit() else None
    if channel is None or not hasattr(channel, "history"):
        return {"messages": []}
    rows = []
    async for message in channel.history(limit=20):
        rows.append(_message(message))
    return {"messages": rows}


def _message(message) -> dict:
    excerpt = (message.content or "").strip()
    if not excerpt and message.embeds:
        excerpt = (message.embeds[0].title or message.embeds[0].description or "").strip()
    return {
        "id": str(message.id),
        "channel_id": str(message.channel.id),
        "excerpt": (excerpt or "No text")[:140],
        "author": getattr(message.author, "display_name", "") or "",
        "created_at": message.created_at.isoformat() if message.created_at else None,
        "own": bool(message.author and message.author.id == getattr(message.guild.me, "id", None)) if message.guild else False,
    }


@router.post("/{guild_id}/reactionroles/v2")
async def menus_create(guild_id: int, body: MenuBody):
    try:
        return await create_menu(
            guild_id=guild_id,
            name=body.name,
            source=body.source,
            menu_type=body.type,
            mode=body.mode,
            channel_id=_int(body.channel_id),
            max_roles=body.max_roles,
            payload=body.payload,
            options=_options(body.options) or [],
            button_style=body.button_style,
        )
    except MenuError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.get("/{guild_id}/reactionroles/v2/{menu_id}")
async def menus_get(guild_id: int, menu_id: str, bot=Depends(get_bot)):
    try:
        shown = await _annotate(bot, await get_menu(guild_id, menu_id))
        shown["bot_position"] = _bot_position(bot, guild_id)
        return shown
    except MenuError as exc:
        raise HTTPException(status_code=404, detail="Menu not found") from exc


@router.patch("/{guild_id}/reactionroles/v2/{menu_id}")
async def menus_update(guild_id: int, menu_id: str, body: MenuPatch, bot=Depends(get_bot)):
    try:
        saved = await update_menu(
            guild_id=guild_id,
            menu_id=menu_id,
            name=body.name,
            mode=body.mode,
            menu_type=body.type,
            enabled=body.enabled,
            max_roles=body.max_roles,
            max_roles_set="max_roles" in body.model_fields_set or body.mode == "unique",
            channel_id=None if body.clear_channel else _int(body.channel_id),
            channel_set=body.clear_channel or body.channel_id is not None,
            payload=body.payload,
            options=_options(body.options),
            button_style=body.button_style,
        )
    except MenuError as exc:
        status = 404 if str(exc) == "missing" else 422
        raise HTTPException(status_code=status, detail=str(exc) if status == 422 else "Menu not found") from exc
    if body.enabled is True:
        await _audit(guild_id, "role_menu_enabled", f"Role menu {saved['name']} enabled")
    elif body.enabled is False:
        await _audit(guild_id, "role_menu_disabled", f"Role menu {saved['name']} disabled")
    elif body.model_fields_set - {"enabled"}:
        await _audit(guild_id, "role_menu_edited", f"Role menu {saved['name']} edited")
    if saved.get("message_id"):
        cog = _cog(bot)
        if cog is not None:
            await cog.sync(guild_id, menu_id)
            saved = await get_menu(guild_id, menu_id)
    return await _annotate(bot, saved)


@router.post("/{guild_id}/reactionroles/v2/{menu_id}/duplicate")
async def menus_duplicate(guild_id: int, menu_id: str):
    try:
        return await duplicate_menu(guild_id=guild_id, menu_id=menu_id)
    except MenuError as exc:
        raise HTTPException(status_code=404, detail="Menu not found") from exc


@router.delete("/{guild_id}/reactionroles/v2/{menu_id}")
async def menus_delete(guild_id: int, menu_id: str, remove_reactions: bool = False, bot=Depends(get_bot)):
    try:
        menu = await get_menu(guild_id, menu_id)
    except MenuError as exc:
        raise HTTPException(status_code=404, detail="Menu not found") from exc
    cog = _cog(bot)
    if remove_reactions and cog is not None:
        await cog.clear_reactions(guild_id, menu)
    await delete_menu(guild_id=guild_id, menu_id=menu_id)
    return {"deleted": True}


@router.post("/{guild_id}/reactionroles/v2/{menu_id}/publish")
async def menus_publish(guild_id: int, menu_id: str, body: PublishBody, bot=Depends(get_bot)):
    cog = _cog(bot)
    if cog is None:
        raise HTTPException(status_code=422, detail="Role menus are not running.")
    try:
        saved = await cog.publish(guild_id, menu_id, channel_id=_int(body.channel_id), message_id=_int(body.message_id))
    except MenuError as exc:
        raise HTTPException(status_code=404, detail="Menu not found") from exc
    except DeliveryError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return await _annotate(bot, saved)


@router.post("/{guild_id}/reactionroles/v2/{menu_id}/republish")
async def menus_republish(guild_id: int, menu_id: str, bot=Depends(get_bot)):
    cog = _cog(bot)
    if cog is None:
        raise HTTPException(status_code=422, detail="Role menus are not running.")
    try:
        saved = await cog.republish(guild_id, menu_id)
    except MenuError as exc:
        raise HTTPException(status_code=404, detail="Menu not found") from exc
    except DeliveryError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return await _annotate(bot, saved)
