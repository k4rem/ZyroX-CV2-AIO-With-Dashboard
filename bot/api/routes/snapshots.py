"""Snapshot capture API. Restore is Phase 6."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field

from api.dependencies import get_bot
from cls_platform.restore import RestoreError, execute_plan, execution_allowed, plan_for
from cls_platform.snapshots import capture_snapshot, list_snapshots

router = APIRouter()


def _root(request: Request) -> None:
    auth = getattr(request.state, "dashboard_auth", None)
    if auth is None or not auth.is_root:
        raise HTTPException(status_code=403, detail="Root access required")


@router.get("/{guild_id}/snapshots")
async def get_snapshots(guild_id: int):
    return await list_snapshots(guild_id)


class RestoreBody(BaseModel):
    present_member_ids: list[str] = Field(default_factory=list)
    confirmation: str | None = None


class _LiveGuild:
    def __init__(self, guild):
        self.guild = guild

    async def create_role(self, *, name, permissions):
        return await self.guild.create_role(name=name, permissions=permissions, reason="CLS restore")

    async def create_channel(self, *, name, parent_id, kind=None):
        parent = self.guild.get_channel(int(parent_id)) if parent_id else None
        if str(kind) in {"category", "4"}:
            return await self.guild.create_category(name, reason="CLS restore")
        return await self.guild.create_text_channel(name, category=parent, reason="CLS restore")

    async def set_overwrite(self, channel_id, target_id, allow, deny):
        channel = self.guild.get_channel(int(channel_id))
        target = self.guild.get_role(int(target_id)) or self.guild.get_member(int(target_id))
        if channel is None or target is None:
            return
        await channel.set_permissions(target, allow=int(allow or 0), deny=int(deny or 0), reason="CLS restore")

    async def ban(self, user_id):
        await self.guild.ban(discord_user(user_id), reason="CLS restore")

    async def set_member_roles(self, user_id, role_ids):
        member = self.guild.get_member(int(user_id))
        if member is None:
            return
        roles = [self.guild.get_role(int(role_id)) for role_id in role_ids]
        await member.edit(roles=[role for role in roles if role is not None], reason="CLS restore")

    async def edit_settings(self, settings):
        if settings.get("name"):
            await self.guild.edit(name=settings["name"], reason="CLS restore")


def discord_user(user_id: str):
    import discord

    return discord.Object(id=int(user_id))


@router.post("/{guild_id}/snapshots/{snapshot_id}/plan")
async def restore_plan(guild_id: int, snapshot_id: str, body: RestoreBody, request: Request):
    _root(request)
    try:
        return await plan_for(guild_id, snapshot_id, set(body.present_member_ids))
    except RestoreError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/{guild_id}/snapshots/{snapshot_id}/restore")
async def restore_execute(guild_id: int, snapshot_id: str, body: RestoreBody, request: Request):
    _root(request)
    try:
        plan = await plan_for(guild_id, snapshot_id, set(body.present_member_ids))
    except RestoreError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    if not body.confirmation:
        return plan
    if not execution_allowed(guild_id):
        plan["reason"] = "execution_disabled"
        return plan
    guild = get_bot().get_guild(guild_id)
    if guild is None:
        plan["reason"] = "guild_unavailable"
        return plan
    try:
        return await execute_plan(plan, _LiveGuild(guild), confirmation=body.confirmation, allow_execution=True)
    except RestoreError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.post("/{guild_id}/snapshots")
async def post_snapshot(guild_id: int, body: dict, request: Request):
    _root(request)
    try:
        return await capture_snapshot(guild_id, body)
    except (KeyError, TypeError, ValueError) as exc:
        raise HTTPException(status_code=400, detail="Snapshot structure is incomplete") from exc
