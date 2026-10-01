"""Invite history and giveaways."""

from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from cls_platform.growth import create_giveaway, end_giveaway, giveaway_history, invite_history, reroll_giveaway

router = APIRouter()


class GiveawayBody(BaseModel):
    prize: str
    channel_id: str | None = None
    ends_at: str


@router.get("/{guild_id}/invites/v2")
async def invites_v2(guild_id: int):
    return {"joins": await invite_history(guild_id), "legacy_counts": False}


@router.get("/{guild_id}/giveaways")
async def giveaways(guild_id: int):
    return {"giveaways": await giveaway_history(guild_id)}


@router.post("/{guild_id}/giveaways")
async def giveaways_create(guild_id: int, body: GiveawayBody):
    return await create_giveaway(
        guild_id=guild_id,
        channel_id=int(body.channel_id) if body.channel_id else None,
        prize=body.prize,
        ends_at=datetime.fromisoformat(body.ends_at),
    )


@router.post("/{guild_id}/giveaways/{giveaway_id}/end")
async def giveaways_end(guild_id: int, giveaway_id: str):
    try:
        return await end_giveaway(guild_id, giveaway_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/{guild_id}/giveaways/{giveaway_id}/reroll")
async def giveaways_reroll(guild_id: int, giveaway_id: str):
    try:
        return await reroll_giveaway(guild_id, giveaway_id)
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
