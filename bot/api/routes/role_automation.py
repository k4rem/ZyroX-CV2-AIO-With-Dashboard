"""Role automation HTTP API."""

from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from api.dependencies import get_bot
from cls_platform.role_automation.logic import conditions_match
from cls_platform.role_automation.store import RuleError, create_rule, delete_rule, duplicate_rule, get_join, list_rules, save_join, update_rule
from cls_platform.role_menus.logic import role_block

router = APIRouter()


class JoinBody(BaseModel):
    member_role_ids: list[str] = Field(default_factory=list)
    bot_role_ids: list[str] = Field(default_factory=list)
    delay_seconds: int = 0
    screening: str = "immediate"


class ConditionBody(BaseModel):
    kind: str
    role_id: str | None = None
    op: str | None = None
    amount: int | None = None
    unit: str | None = None


class RuleBody(BaseModel):
    name: str = "Role rule"
    trigger: str = "role_add"
    trigger_role_id: str | None = None
    conditions: list[ConditionBody] = Field(default_factory=list)
    action: str = "add"
    action_role_id: str
    delay_seconds: int = 0
    enabled: bool = True


class RulePatch(BaseModel):
    name: str | None = None
    trigger: str | None = None
    trigger_role_id: str | None = None
    conditions: list[ConditionBody] | None = None
    action: str | None = None
    action_role_id: str | None = None
    delay_seconds: int | None = None
    enabled: bool | None = None


def _http(exc: RuleError) -> HTTPException:
    if str(exc) == "missing":
        return HTTPException(status_code=404, detail="Rule not found")
    return HTTPException(status_code=422, detail=str(exc))


def _position(bot, guild_id: int) -> int:
    guild = bot.get_guild(int(guild_id)) if bot is not None else None
    me = getattr(guild, "me", None) if guild is not None else None
    top = getattr(me, "top_role", None) if me is not None else None
    return int(getattr(top, "position", 0) or 0)


def _role_warning(bot, guild_id: int, role_id: str | None, label: str) -> str | None:
    if not role_id or not str(role_id).isdigit() or bot is None:
        return None
    guild = bot.get_guild(int(guild_id))
    if guild is None:
        return None
    role = guild.get_role(int(role_id))
    me = getattr(guild, "me", None)
    block = role_block(
        exists=role is not None,
        managed=bool(getattr(role, "managed", False)),
        bot_can_manage=bool(me and me.guild_permissions.manage_roles),
        below_bot=bool(role and me and getattr(me, "top_role", None) and (role.position < me.top_role.position or (role.position == me.top_role.position and int(role.id) < int(me.top_role.id)))),
    )
    if block is None:
        return None
    if "missing" in block or "no longer" in block:
        return f"Missing {label}."
    if "managed" in block:
        return f"The {label} is managed."
    if "Manage Roles" in block:
        return "CLS needs Manage Roles."
    return f"The {label} is above CLS."


def _health(bot, guild_id: int, rule: dict) -> dict:
    warnings = []
    if rule["trigger"] in {"role_add", "role_remove"}:
        warning = _role_warning(bot, guild_id, rule.get("trigger_role_id"), "trigger role")
        if warning:
            warnings.append(warning)
    warning = _role_warning(bot, guild_id, rule.get("action_role_id"), "action role")
    if warning:
        warnings.append(warning)
    shown = dict(rule)
    shown["warnings"] = warnings
    shown["status"] = "Disabled" if not rule["enabled"] else "Needs attention" if warnings else "Enabled"
    shown["matches"] = _matches(bot, guild_id, rule)
    return shown


def _matches(bot, guild_id: int, rule: dict) -> int | None:
    if rule["trigger"] not in {"join", "screening"} or bot is None:
        return None
    guild = bot.get_guild(int(guild_id))
    members = list(getattr(guild, "members", []) or [])
    if len(members) < 2:
        return None
    now = datetime.now(timezone.utc)
    count = 0
    for member in members:
        created = getattr(member, "created_at", None)
        age = int((now - created).total_seconds()) if created else 0
        if conditions_match(
            is_bot=bool(getattr(member, "bot", False)),
            role_ids={role.id for role in getattr(member, "roles", [])},
            account_age_seconds=max(0, age),
            conditions=rule["conditions"],
        ):
            count += 1
    return count


@router.get("/{guild_id}/autorole/v2")
async def automation_get(guild_id: int, bot=Depends(get_bot)):
    return {
        "join": await get_join(guild_id),
        "rules": [_health(bot, guild_id, rule) for rule in await list_rules(guild_id)],
        "bot_position": _position(bot, guild_id),
    }


@router.put("/{guild_id}/autorole/v2/join")
async def automation_join(guild_id: int, body: JoinBody):
    try:
        return await save_join(
            guild_id=guild_id,
            member_role_ids=body.member_role_ids,
            bot_role_ids=body.bot_role_ids,
            delay_seconds_value=body.delay_seconds,
            screening=body.screening,
        )
    except RuleError as exc:
        raise _http(exc) from exc


@router.post("/{guild_id}/autorole/v2/rules")
async def automation_create(guild_id: int, body: RuleBody, bot=Depends(get_bot)):
    try:
        saved = await create_rule(
            guild_id=guild_id,
            name=body.name,
            trigger=body.trigger,
            trigger_role_id=body.trigger_role_id,
            conditions=[item.model_dump() for item in body.conditions],
            action=body.action,
            action_role_id=body.action_role_id,
            delay_seconds_value=body.delay_seconds,
            enabled=body.enabled,
        )
    except RuleError as exc:
        raise _http(exc) from exc
    return _health(bot, guild_id, saved)


@router.patch("/{guild_id}/autorole/v2/rules/{rule_id}")
async def automation_update(guild_id: int, rule_id: str, body: RulePatch, bot=Depends(get_bot)):
    fields = body.model_dump(exclude_unset=True)
    if "conditions" in fields and fields["conditions"] is not None:
        fields["conditions"] = [item if isinstance(item, dict) else item for item in fields["conditions"]]
    try:
        saved = await update_rule(guild_id=guild_id, rule_id=rule_id, **fields)
    except RuleError as exc:
        raise _http(exc) from exc
    return _health(bot, guild_id, saved)


@router.post("/{guild_id}/autorole/v2/rules/{rule_id}/duplicate")
async def automation_duplicate(guild_id: int, rule_id: str, bot=Depends(get_bot)):
    try:
        saved = await duplicate_rule(guild_id=guild_id, rule_id=rule_id)
    except RuleError as exc:
        raise _http(exc) from exc
    return _health(bot, guild_id, saved)


@router.delete("/{guild_id}/autorole/v2/rules/{rule_id}")
async def automation_delete(guild_id: int, rule_id: str):
    try:
        await delete_rule(guild_id=guild_id, rule_id=rule_id)
    except RuleError as exc:
        raise _http(exc) from exc
    return {"deleted": True}
