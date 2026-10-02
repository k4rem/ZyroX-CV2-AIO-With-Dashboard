"""Auto react rules."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field

from cls_platform.autoreact import create_rule, delete_rule, duplicate_rule, list_rules, update_rule

router = APIRouter()


class RuleBody(BaseModel):
    name: str = "Untitled rule"
    enabled: bool = True
    scope: str = "all"
    channel_ids: list[str] = Field(default_factory=list)
    mode: str = "contains"
    pattern: str = ""
    emojis: list[str] = Field(default_factory=list)


def _actor(request: Request) -> int | None:
    auth = getattr(request.state, "dashboard_auth", None)
    return int(auth.user_id) if auth is not None else None


@router.get("/{guild_id}/autoreact/v2")
async def rules(guild_id: int):
    return {"rules": await list_rules(guild_id)}


@router.post("/{guild_id}/autoreact/v2")
async def rules_create(guild_id: int, body: RuleBody, request: Request):
    return await create_rule(guild_id, body.model_dump(), actor_id=_actor(request))


@router.patch("/{guild_id}/autoreact/v2/{rule_id}")
async def rules_update(guild_id: int, rule_id: str, body: RuleBody, request: Request):
    try:
        return await update_rule(guild_id, rule_id, body.model_dump(), actor_id=_actor(request))
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/{guild_id}/autoreact/v2/{rule_id}/duplicate")
async def rules_duplicate(guild_id: int, rule_id: str, request: Request):
    try:
        return await duplicate_rule(guild_id, rule_id, actor_id=_actor(request))
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.delete("/{guild_id}/autoreact/v2/{rule_id}")
async def rules_delete(guild_id: int, rule_id: str, request: Request):
    try:
        await delete_rule(guild_id, rule_id, actor_id=_actor(request))
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return {"status": "deleted"}
