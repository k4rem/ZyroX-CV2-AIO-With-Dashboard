"""Logging V2 HTTP API."""

from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from cls_platform.logging.store import (
    CATEGORIES,
    LoggingError,
    get_event,
    list_events,
    overview,
    routes,
    set_route,
)

router = APIRouter()


class RouteBody(BaseModel):
    category: str
    enabled: bool
    channel_id: str | None = None


def _parse_time(value: str | None) -> datetime | None:
    if not value:
        return None
    return datetime.fromisoformat(value)


@router.get("/{guild_id}/logging/v2")
async def logging_home(
    guild_id: int,
    category: str | None = None,
    event_type: str | None = None,
    actor_id: str | None = None,
    target_id: str | None = None,
    since: str | None = None,
    until: str | None = None,
    cursor: str | None = None,
    limit: int = Query(default=50, ge=1, le=100),
):
    page = await list_events(
        guild_id,
        category=category,
        event_type=event_type,
        actor_id=int(actor_id) if actor_id else None,
        target_id=int(target_id) if target_id else None,
        since=_parse_time(since),
        until=_parse_time(until),
        cursor=cursor,
        limit=limit,
    )
    return {
        "categories": list(CATEGORIES),
        "overview": await overview(guild_id),
        "routes": await routes(guild_id),
        **page,
    }


@router.get("/{guild_id}/logging/v2/events/{event_id}")
async def logging_event(guild_id: int, event_id: str):
    try:
        return await get_event(guild_id, event_id)
    except LoggingError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.put("/{guild_id}/logging/v2/routes")
async def logging_route(guild_id: int, body: RouteBody):
    try:
        return await set_route(
            guild_id=guild_id,
            category=body.category,
            enabled=body.enabled,
            channel_id=int(body.channel_id) if body.channel_id else None,
        )
    except LoggingError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
