"""Logging V2 HTTP API."""

from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from api.dependencies import get_bot
from cls_platform.logging.entities import snapshot_user
from cls_platform.logging.pipeline import delivery_state
from cls_platform.logging.publish import recent_failures
from cls_platform.logging.present import catalog, groups
from cls_platform.logging.render import render_discord, sample_event
from cls_platform.logging.store import (
    CATEGORIES,
    EVENT_RETENTION_DAYS,
    MESSAGE_RETENTION_DAYS,
    LoggingError,
    appearance_for,
    delivery_target,
    event_routes,
    get_event,
    ignores_public,
    list_events,
    overview,
    route_for,
    routes,
    set_appearance,
    set_event_route,
    set_ignores,
    set_route,
)
from cogs.logging_v2 import embed_from_payload

router = APIRouter()


class RouteBody(BaseModel):
    category: str
    enabled: bool
    channel_id: str | None = None


class IgnoreBody(BaseModel):
    channels: list[str] = Field(default_factory=list)
    roles: list[str] = Field(default_factory=list)
    users: list[str] = Field(default_factory=list)


class EventRouteBody(BaseModel):
    mode: str
    channel_id: str | None = None


class AppearanceBody(BaseModel):
    style: str | None = None
    show_avatars: bool | None = None
    show_moderator: bool | None = None
    show_jump: bool | None = None
    show_timestamp: bool | None = None
    show_ids: bool | None = None
    footer_mode: str | None = None
    footer_text: str | None = None
    colors: dict[str, str] | None = None
    event_styles: dict | None = None
    ignore_scope: str | None = None


def _parse_time(value: str | None) -> datetime | None:
    if not value:
        return None
    return datetime.fromisoformat(value)


def _snowflake(value: str | None) -> int | None:
    if not value:
        return None
    if not str(value).isdigit():
        raise HTTPException(status_code=422, detail="invalid_snowflake")
    return int(value)


def _bot_or_none():
    try:
        return get_bot()
    except HTTPException:
        return None


async def _annotate(guild_id: int, rows: list[dict], bot) -> list[dict]:
    import discord

    guild = bot.get_guild(guild_id) if bot is not None else None
    me = getattr(guild, "me", None) if guild is not None else None
    checked = guild is not None and me is not None
    annotated = []
    for row in rows:
        channel = None
        resolution = "unchecked" if not checked else "missing"
        channel_id = row.get("channel_id")
        if checked and channel_id:
            channel = guild.get_channel(int(channel_id))
            if channel is None:
                try:
                    channel = await guild.fetch_channel(int(channel_id))
                except discord.Forbidden:
                    resolution = "forbidden"
                except discord.NotFound:
                    resolution = "unavailable"
                except discord.HTTPException:
                    resolution = "unavailable"
            if channel is not None:
                resolution = "found"
        can_view = can_send = can_embed = False
        if channel is not None and me is not None and hasattr(channel, "permissions_for"):
            perms = channel.permissions_for(me)
            can_view = bool(perms.view_channel)
            can_send = bool(perms.send_messages)
            can_embed = bool(perms.embed_links)
        annotated.append(
            {
                **row,
                "channel_name": getattr(channel, "name", None),
                "delivery": delivery_state(
                    enabled=bool(row.get("enabled")),
                    channel_id=channel_id,
                    resolution=resolution,
                    can_view=can_view,
                    can_send=can_send,
                    can_embed=can_embed,
                ),
            }
        )
    return annotated


@router.get("/{guild_id}/logging/v2")
async def logging_home(
    guild_id: int,
    category: str | None = None,
    event_type: str | None = None,
    actor_id: str | None = None,
    target_id: str | None = None,
    member_id: str | None = None,
    q: str | None = None,
    since: str | None = None,
    until: str | None = None,
    cursor: str | None = None,
    limit: int = Query(default=50, ge=1, le=100),
    page: int | None = Query(default=None, ge=1),
    page_size: int | None = Query(default=None),
    confidence: str | None = None,
):
    page_result = await list_events(
        guild_id,
        category=category,
        event_type=event_type,
        actor_id=_snowflake(actor_id),
        target_id=_snowflake(target_id),
        member_id=_snowflake(member_id),
        query=q,
        since=_parse_time(since),
        until=_parse_time(until),
        cursor=None if page is not None else cursor,
        limit=limit,
        page=page,
        page_size=page_size,
        confidence=confidence,
    )
    return {
        "categories": list(CATEGORIES),
        "event_types": catalog(),
        "retention": {"events_days": EVENT_RETENTION_DAYS, "message_content_days": MESSAGE_RETENTION_DAYS},
        "overview": await overview(guild_id),
        "routes": await _annotate(guild_id, await routes(guild_id), _bot_or_none()),
        "event_routes": await event_routes(guild_id),
        "groups": groups(),
        "appearance": await appearance_for(guild_id),
        "ignores": _named_ignores(guild_id, await ignores_public(guild_id), _bot_or_none()),
        "health": _logging_health(guild_id, _bot_or_none()),
        **page_result,
    }


def _logging_health(guild_id: int, bot) -> dict:
    guild = bot.get_guild(guild_id) if bot is not None else None
    me = getattr(guild, "me", None) if guild is not None else None
    perms = getattr(me, "guild_permissions", None) if me is not None else None
    audit = bool(perms.view_audit_log) if perms is not None else None
    return {
        "view_audit_log": audit,
        "view_channel": bool(perms.view_channel) if perms is not None else None,
        "send_messages": bool(perms.send_messages) if perms is not None else None,
        "embed_links": bool(perms.embed_links) if perms is not None else None,
        "attribution": "unavailable" if audit is False else ("available" if audit else "unchecked"),
        "note": "Attribution may be unavailable" if audit is False else None,
        "recent_failures": recent_failures(guild_id),
    }


def _export_row(event: dict) -> dict:
    hidden = {"content", "token", "secret", "authorization"}

    def scrub(value):
        if isinstance(value, dict):
            return {key: scrub(item) for key, item in value.items() if key not in hidden}
        if isinstance(value, list):
            return [scrub(item) for item in value]
        return value

    return scrub({key: event.get(key) for key in ("id", "event_type", "category", "occurred_at", "actor_id", "actor_confidence", "target_id", "channel_id", "before", "after", "metadata", "presentation")})


@router.get("/{guild_id}/logging/v2/export")
async def logging_export(
    guild_id: int,
    category: str | None = None,
    event_type: str | None = None,
    member_id: str | None = None,
    q: str | None = None,
    confidence: str | None = None,
):
    collected = []
    for number in range(1, 5):
        page_result = await list_events(
            guild_id,
            category=category,
            event_type=event_type,
            member_id=_snowflake(member_id),
            query=q,
            confidence=confidence,
            page=number,
            page_size=100,
        )
        collected.extend(_export_row(row) for row in page_result["events"])
        if number >= page_result["pages"]:
            break
    return {"format": "json", "events": collected, "retention_days": EVENT_RETENTION_DAYS}


@router.get("/{guild_id}/logging/v2/events/{event_id}")
async def logging_event(guild_id: int, event_id: str):
    try:
        return await get_event(guild_id, event_id)
    except LoggingError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/{guild_id}/logging/v2/members")
async def logging_members(guild_id: int, q: str = "", bot=Depends(get_bot)):
    guild = bot.get_guild(guild_id)
    needle = q.strip()
    if guild is None or len(needle) < 2:
        return {"members": []}
    try:
        found = await guild.query_members(query=needle, limit=8)
    except Exception:
        found = [
            member
            for member in guild.members
            if needle.lower() in (member.display_name or "").lower() or needle.lower() in (member.name or "").lower()
        ][:8]
    return {"members": [snapshot_user(member) for member in found]}


@router.put("/{guild_id}/logging/v2/routes")
async def logging_route(guild_id: int, body: RouteBody):
    try:
        saved = await set_route(
            guild_id=guild_id,
            category=body.category,
            enabled=body.enabled,
            channel_id=_snowflake(body.channel_id),
        )
    except LoggingError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return (await _annotate(guild_id, [saved], _bot_or_none()))[0]


@router.put("/{guild_id}/logging/v2/ignores")
async def logging_ignores(guild_id: int, body: IgnoreBody):
    try:
        saved = await set_ignores(
            guild_id=guild_id,
            channels=[int(item) for item in body.channels if str(item).isdigit()],
            roles=[int(item) for item in body.roles if str(item).isdigit()],
            users=[int(item) for item in body.users if str(item).isdigit()],
        )
        return _named_ignores(guild_id, saved, _bot_or_none())
    except HTTPException:
        raise
    except LoggingError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.put("/{guild_id}/logging/v2/event-routes/{event_type}")
async def logging_event_route(guild_id: int, event_type: str, body: EventRouteBody):
    try:
        return await set_event_route(
            guild_id=guild_id,
            event_type=event_type,
            mode=body.mode,
            channel_id=_snowflake(body.channel_id),
        )
    except LoggingError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.put("/{guild_id}/logging/v2/appearance")
async def logging_appearance(guild_id: int, body: AppearanceBody):
    try:
        return await set_appearance(guild_id, body.model_dump(exclude_unset=True))
    except LoggingError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


async def _send_sample(guild, channel, category: str, event_type: str | None = None):
    import discord

    me = guild.me
    if channel is None:
        raise HTTPException(status_code=422, detail="Channel unavailable.")
    if me is None or not channel.permissions_for(me).send_messages or not channel.permissions_for(me).embed_links:
        raise HTTPException(status_code=422, detail="Missing permission to send embeds in that channel.")
    actor = snapshot_user(me) or {"id": str(me.id), "display_name": me.display_name, "username": me.name, "avatar_url": None}
    event = sample_event(category, actor=actor, channel=snapshot_channel_safe(channel), event_type=event_type)
    rendered = render_discord(event, await appearance_for(guild.id))
    view = None
    if rendered.get("jump_url"):
        view = discord.ui.View()
        view.add_item(discord.ui.Button(style=discord.ButtonStyle.link, label="View message", url=rendered["jump_url"]))
    try:
        await channel.send(embed=embed_from_payload(rendered), view=view, allowed_mentions=discord.AllowedMentions.none())
    except Exception as exc:
        raise HTTPException(status_code=422, detail="Could not deliver the test log.") from exc


@router.post("/{guild_id}/logging/v2/routes/{category}/test")
async def logging_test(guild_id: int, category: str, bot=Depends(get_bot)):
    if category not in CATEGORIES:
        raise HTTPException(status_code=422, detail="unknown_category")
    guild = bot.get_guild(guild_id)
    if guild is None:
        raise HTTPException(status_code=404, detail="Guild is not available to the bot.")
    route = await route_for(guild_id, category)
    if route is None:
        raise HTTPException(status_code=422, detail="Enable this category and choose a channel first.")
    channel = guild.get_channel(route["channel_id"])
    await _send_sample(guild, channel, category)
    saved = await route_for(guild_id, category)
    route_row = {"category": category, "enabled": True, "channel_id": str(channel.id)}
    if saved is not None:
        route_row["channel_id"] = str(saved["channel_id"])
    annotated = await _annotate(guild_id, [route_row], bot)
    return {"status": "sent", "channel_id": str(channel.id), "route": annotated[0]}


@router.post("/{guild_id}/logging/v2/event-routes/{event_type}/test")
async def logging_event_test(guild_id: int, event_type: str, bot=Depends(get_bot)):
    from cls_platform.logging.present import TITLES, category_for_event

    if event_type not in TITLES:
        raise HTTPException(status_code=422, detail="unknown_event")
    guild = bot.get_guild(guild_id)
    if guild is None:
        raise HTTPException(status_code=404, detail="Guild is not available to the bot.")
    category = category_for_event(event_type)
    decision = await delivery_target(guild_id, category, event_type)
    if not decision["deliver"] or not decision["channel_id"]:
        raise HTTPException(status_code=422, detail="This event is not delivered to Discord.")
    channel = guild.get_channel(decision["channel_id"])
    await _send_sample(guild, channel, category, event_type)
    return {"status": "sent", "channel_id": str(decision["channel_id"])}


def _named_ignores(guild_id: int, raw: dict, bot) -> dict:
    guild = bot.get_guild(guild_id) if bot is not None else None

    def user(user_id: str) -> dict:
        member = guild.get_member(int(user_id)) if guild is not None else None
        snap = snapshot_user(member) if member is not None else None
        return snap or {"id": user_id, "display_name": None, "username": None, "avatar_url": None}

    def channel(channel_id: str) -> dict:
        found = guild.get_channel(int(channel_id)) if guild is not None else None
        return {"id": channel_id, "name": getattr(found, "name", None)}

    def role(role_id: str) -> dict:
        found = guild.get_role(int(role_id)) if guild is not None else None
        return {"id": role_id, "name": getattr(found, "name", None)}

    return {
        "channels": [channel(item) for item in raw.get("channels", [])],
        "roles": [role(item) for item in raw.get("roles", [])],
        "users": [user(item) for item in raw.get("users", [])],
    }


def snapshot_channel_safe(channel) -> dict:
    from cls_platform.logging.entities import snapshot_channel

    return snapshot_channel(channel) or {"id": str(channel.id), "name": channel.name, "type": "text"}
