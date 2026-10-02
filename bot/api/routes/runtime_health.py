"""Cached guild capability snapshot for shared pickers and module health."""

from __future__ import annotations

from fastapi import APIRouter, Depends

from api.dependencies import get_bot
from cls_platform.health.contract import runtime_snapshot

router = APIRouter()


@router.get("/{guild_id}/runtime-health")
async def guild_runtime_health(guild_id: int, bot=Depends(get_bot)):
    guild = bot.get_guild(int(guild_id)) if bot is not None else None
    return runtime_snapshot(guild)
