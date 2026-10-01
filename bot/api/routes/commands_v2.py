"""Command manager API. Does not resync slash commands."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field

from api.dependencies import get_bot
from cls_platform.commands.policy import inventory, policies_for, set_policy

router = APIRouter()


class PolicyBody(BaseModel):
    command_name: str
    enabled: bool = True
    allowed_role_ids: list[str] = Field(default_factory=list)


@router.get("/{guild_id}/commands")
async def command_list(guild_id: int):
    saved = await policies_for(guild_id)
    return {"commands": inventory(get_bot(), saved)}


@router.put("/{guild_id}/commands")
async def command_update(guild_id: int, body: PolicyBody, request: Request):
    if not body.command_name.strip():
        raise HTTPException(status_code=422, detail="command_name required")
    auth = getattr(request.state, "dashboard_auth", None)
    actor = int(auth.user_id) if auth is not None else None
    return await set_policy(
        guild_id=guild_id,
        command_name=body.command_name.strip(),
        enabled=body.enabled,
        allowed_role_ids=[int(item) for item in body.allowed_role_ids],
        actor_id=actor,
    )
