"""Command management API. Does not resync slash commands."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field

from api.dependencies import get_bot
from cls_platform.commands.catalog import (
    MODULES,
    build_tree,
    explain_access,
    filter_rows,
    guild_rows,
    iter_commands,
    module_summaries,
    overview,
    paginate,
    visibility,
)
from cls_platform.commands.policy import (
    PolicyError,
    policies_for,
    set_module_enabled,
    set_policy,
    module_states,
)
from cls_platform.commands.policy import CommandPolicy
from cls_platform.database import session_scope

router = APIRouter()


class PolicyBody(BaseModel):
    command_name: str
    enabled: bool = True
    allowed_role_ids: list[str] = Field(default_factory=list)
    blocked_role_ids: list[str] = Field(default_factory=list)
    allowed_channel_ids: list[str] = Field(default_factory=list)
    blocked_channel_ids: list[str] = Field(default_factory=list)


class ModuleBody(BaseModel):
    module_id: str
    enabled: bool


class BulkBody(BaseModel):
    action: str
    command_names: list[str] = Field(default_factory=list)
    allowed_channel_ids: list[str] = Field(default_factory=list)
    blocked_role_ids: list[str] = Field(default_factory=list)


class AccessBody(BaseModel):
    command_name: str
    role_ids: list[str] = Field(default_factory=list)
    channel_id: str | None = None


def _ints(values: list[str]) -> list[int]:
    return [int(item) for item in values if str(item).isdigit()]


def _actor(request: Request) -> int | None:
    auth = getattr(request.state, "dashboard_auth", None)
    return int(auth.user_id) if auth is not None else None


def _find(bot, name: str):
    for command in iter_commands(bot):
        if command.qualified_name == name:
            return command
    return None


def _require_visible(bot, name: str):
    if getattr(bot, "walk_commands", None) is None:
        return None
    command = _find(bot, name)
    if command is None or visibility(command) is not None:
        raise PolicyError("This command is not available in server command management.")
    return command


@router.get("/{guild_id}/commands")
async def command_list(
    guild_id: int,
    page: int = 1,
    page_size: int = 25,
    q: str = "",
    module: str = "",
    audience: str = "",
    kind: str = "",
    enabled: str = "",
    restricted: str = "",
    tree: int = 0,
):
    bot = get_bot()
    saved = await policies_for(guild_id)
    states = await module_states(guild_id)
    rows = guild_rows(bot, saved, states)
    modules = module_summaries(rows, states, bot)
    filtered = filter_rows(
        rows,
        query=q,
        module_id=module,
        audience=audience,
        kind=kind,
        enabled=enabled,
        restricted=restricted,
    )
    page_body = paginate(filtered, page, page_size)
    payload = {
        "overview": overview(rows, modules),
        "modules": modules,
        **page_body,
    }
    if tree:
        payload["tree"] = build_tree(filtered)
    return payload


@router.put("/{guild_id}/commands")
async def command_update(guild_id: int, body: PolicyBody, request: Request):
    if not body.command_name.strip():
        raise HTTPException(status_code=422, detail="command_name required")
    name = body.command_name.strip()
    try:
        _require_visible(get_bot(), name)
        return await set_policy(
            guild_id=guild_id,
            command_name=name,
            enabled=body.enabled,
            allowed_role_ids=_ints(body.allowed_role_ids),
            blocked_role_ids=_ints(body.blocked_role_ids),
            allowed_channel_ids=_ints(body.allowed_channel_ids),
            blocked_channel_ids=_ints(body.blocked_channel_ids),
            actor_id=_actor(request),
        )
    except PolicyError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.post("/{guild_id}/commands/modules")
async def command_module(guild_id: int, body: ModuleBody, request: Request):
    if body.module_id not in MODULES:
        raise HTTPException(status_code=422, detail="Unknown module")
    return await set_module_enabled(
        guild_id=guild_id,
        module_id=body.module_id,
        enabled=body.enabled,
        actor_id=_actor(request),
    )


@router.post("/{guild_id}/commands/bulk")
async def command_bulk(guild_id: int, body: BulkBody, request: Request):
    action = body.action.strip().lower()
    if action not in {"enable", "disable", "reset", "channels", "block_role"}:
        raise HTTPException(status_code=422, detail="Unknown bulk action")
    names = [item.strip() for item in body.command_names if item.strip()]
    if not names:
        raise HTTPException(status_code=422, detail="Select at least one command")
    bot = get_bot()
    saved = await policies_for(guild_id)
    actor = _actor(request)
    affected = 0
    try:
        if action == "reset":
            async with session_scope() as session:
                for name in names:
                    _require_visible(bot, name)
                    row = await session.get(CommandPolicy, (guild_id, name))
                    if row is not None:
                        await session.delete(row)
                    affected += 1
            return {"affected": affected, "action": action}
        for name in names:
            _require_visible(bot, name)
            current = saved.get(name, {})
            enabled = current.get("enabled", True)
            allowed_roles = [int(item) for item in current.get("allowed_role_ids") or []]
            blocked_roles = [int(item) for item in current.get("blocked_role_ids") or []]
            allowed_channels = [int(item) for item in current.get("allowed_channel_ids") or []]
            blocked_channels = [int(item) for item in current.get("blocked_channel_ids") or []]
            if action == "enable":
                enabled = True
            elif action == "disable":
                enabled = False
            elif action == "channels":
                allowed_channels = _ints(body.allowed_channel_ids)
            elif action == "block_role":
                extra = _ints(body.blocked_role_ids)
                blocked_roles = list(dict.fromkeys([*blocked_roles, *extra]))
            await set_policy(
                guild_id=guild_id,
                command_name=name,
                enabled=bool(enabled),
                allowed_role_ids=allowed_roles,
                blocked_role_ids=blocked_roles,
                allowed_channel_ids=allowed_channels,
                blocked_channel_ids=blocked_channels,
                actor_id=actor,
            )
            affected += 1
    except PolicyError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return {"affected": affected, "action": action}


@router.post("/{guild_id}/commands/access")
async def command_access(guild_id: int, body: AccessBody):
    bot = get_bot()
    name = body.command_name.strip()
    command = _find(bot, name) if getattr(bot, "walk_commands", None) else None
    if getattr(bot, "walk_commands", None) is not None and (command is None or visibility(command) is not None):
        raise HTTPException(status_code=404, detail="Command not found")
    role_ids = set(_ints(body.role_ids))
    channel_id = int(body.channel_id) if body.channel_id and str(body.channel_id).isdigit() else None
    discord_permissions = _discord_permissions(bot, guild_id, role_ids)
    if command is None:
        result = await explain_access(
            guild_id=guild_id,
            command=_Bare(name),
            role_ids=role_ids,
            channel_id=channel_id,
            discord_permissions=discord_permissions,
        )
        return result
    return await explain_access(
        guild_id=guild_id,
        command=command,
        role_ids=role_ids,
        channel_id=channel_id,
        discord_permissions=discord_permissions,
    )


class _Bare:
    def __init__(self, name: str):
        self.qualified_name = name
        self.name = name
        self.cog = None
        self.parent = None


def _discord_permissions(bot, guild_id: int, role_ids: set[int]) -> set[str] | None:
    guild = bot.get_guild(guild_id) if hasattr(bot, "get_guild") else None
    if guild is None or not role_ids:
        return None
    names: set[str] = set()
    found = False
    for role_id in role_ids:
        role = guild.get_role(role_id)
        if role is None:
            continue
        perms = getattr(role, "permissions", None)
        if perms is None:
            return None
        found = True
        try:
            names.update(label.replace("_", " ") for label, allowed in perms if allowed)
        except TypeError:
            return None
    return names if found else None
