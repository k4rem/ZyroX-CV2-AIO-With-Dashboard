"""Invite history and giveaways."""

from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

from cls_platform.giveaways_runtime import sync_message
from cls_platform.growth import (
    archive_giveaway,
    create_giveaway,
    end_giveaway,
    entry_user_ids,
    giveaway_for,
    giveaway_history,
    invite_history,
    reroll_giveaway,
    update_giveaway,
)
from api.dependencies import get_bot

router = APIRouter()


class GiveawayBody(BaseModel):
    prize: str
    description: str = ""
    channel_id: str | None = None
    ends_at: str
    starts_at: str | None = None
    winner_count: int = 1
    required_role_id: str | None = None
    blocked_role_id: str | None = None


class GiveawayPatch(BaseModel):
    prize: str | None = None
    description: str | None = None
    channel_id: str | None = None
    ends_at: str | None = None
    winner_count: int | None = None
    required_role_id: str | None = None
    blocked_role_id: str | None = None
    clear_required_role: bool = False
    clear_blocked_role: bool = False


def _actor(request: Request) -> int | None:
    auth = getattr(request.state, "dashboard_auth", None)
    return int(auth.user_id) if auth is not None else None


def _optional_id(value: str | None) -> int | None:
    if value and str(value).isdigit():
        return int(value)
    return None


@router.get("/{guild_id}/invites/v2")
async def invites_v2(guild_id: int):
    return {"joins": await invite_history(guild_id), "legacy_counts": False}


def _named(guild_id: int, rows: list[dict]) -> list[dict]:
    bot = get_bot()
    guild = bot.get_guild(guild_id) if bot is not None else None

    def name(user_id: str | None) -> str | None:
        if not user_id or guild is None:
            return None
        member = guild.get_member(int(user_id))
        return member.display_name if member is not None else "Former member"

    for row in rows:
        row["winners"] = [{"id": user_id, "name": name(user_id) or "Former member"} for user_id in row.get("winner_ids") or []]
        row["host_name"] = name(row.get("host_id"))
    return rows


@router.get("/{guild_id}/giveaways")
async def giveaways(guild_id: int):
    return {"giveaways": _named(guild_id, await giveaway_history(guild_id))}


@router.post("/{guild_id}/giveaways")
async def giveaways_create(guild_id: int, body: GiveawayBody, request: Request):
    if not body.prize.strip():
        raise HTTPException(status_code=422, detail="prize required")
    created = await create_giveaway(
        guild_id=guild_id,
        channel_id=_optional_id(body.channel_id),
        prize=body.prize.strip(),
        description=body.description,
        ends_at=datetime.fromisoformat(body.ends_at),
        starts_at=datetime.fromisoformat(body.starts_at) if body.starts_at else None,
        winner_count=body.winner_count,
        required_role_id=_optional_id(body.required_role_id),
        blocked_role_id=_optional_id(body.blocked_role_id),
        host_id=_actor(request),
    )
    if created["status"] == "open":
        await sync_message(get_bot(), guild_id, created["id"])
    return await giveaway_for(guild_id, created["id"]) or created


@router.patch("/{guild_id}/giveaways/{giveaway_id}")
async def giveaways_update(guild_id: int, giveaway_id: str, body: GiveawayPatch):
    changes = {}
    if body.prize is not None:
        changes["prize"] = body.prize
    if body.description is not None:
        changes["description"] = body.description
    if body.ends_at is not None:
        changes["ends_at"] = datetime.fromisoformat(body.ends_at)
    if body.winner_count is not None:
        changes["winner_count"] = body.winner_count
    if body.clear_required_role:
        changes["required_role_id"] = None
    elif body.required_role_id is not None:
        changes["required_role_id"] = _optional_id(body.required_role_id)
    if body.clear_blocked_role:
        changes["blocked_role_id"] = None
    elif body.blocked_role_id is not None:
        changes["blocked_role_id"] = _optional_id(body.blocked_role_id)
    if body.channel_id is not None:
        changes["channel_id"] = _optional_id(body.channel_id)
    try:
        updated = await update_giveaway(guild_id, giveaway_id, changes)
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    await sync_message(get_bot(), guild_id, giveaway_id)
    return updated


@router.post("/{guild_id}/giveaways/{giveaway_id}/end")
async def giveaways_end(guild_id: int, giveaway_id: str, request: Request):
    try:
        ended = await end_giveaway(guild_id, giveaway_id, eligible=await _eligible(guild_id, giveaway_id), actor_id=_actor(request))
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    await sync_message(get_bot(), guild_id, giveaway_id)
    return ended


@router.post("/{guild_id}/giveaways/{giveaway_id}/reroll")
async def giveaways_reroll(guild_id: int, giveaway_id: str, request: Request):
    try:
        rolled = await reroll_giveaway(guild_id, giveaway_id, eligible=await _eligible(guild_id, giveaway_id), actor_id=_actor(request))
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    await sync_message(get_bot(), guild_id, giveaway_id)
    return rolled


@router.delete("/{guild_id}/giveaways/{giveaway_id}")
async def giveaways_archive(guild_id: int, giveaway_id: str, request: Request):
    try:
        archived = await archive_giveaway(guild_id, giveaway_id, actor_id=_actor(request))
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    await sync_message(get_bot(), guild_id, giveaway_id)
    return archived


async def _eligible(guild_id: int, giveaway_id: str) -> set[int] | None:
    bot = get_bot()
    guild = bot.get_guild(guild_id) if bot is not None else None
    if guild is None:
        return None
    from cls_platform.growth import entry_block, giveaway_for

    row = await giveaway_for(guild_id, giveaway_id)
    if row is None:
        return set()
    required = int(row["required_role_id"]) if row.get("required_role_id") else None
    blocked = int(row["blocked_role_id"]) if row.get("blocked_role_id") else None
    allowed: set[int] = set()
    for user_id in await entry_user_ids(giveaway_id):
        member = guild.get_member(user_id)
        if member is None:
            continue
        roles = {role.id for role in member.roles}
        if entry_block(roles, required=required, blocked=blocked, is_bot=member.bot) is None:
            allowed.add(member.id)
    return allowed
