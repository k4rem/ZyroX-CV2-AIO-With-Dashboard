"""Automod V2 HTTP API. The legacy /automod patch no longer writes runtime state."""

from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query

from api.dependencies import get_bot
from cls_platform.automod.engine import evaluate_message, followups_for, plan_actions, preset_rules
from cls_platform.automod.store import (
    apply_followup,
    ensure_config,
    get_config,
    get_violation,
    list_strikes,
    list_violations,
    mark_false_positive,
    overview,
    save_config,
)
from cls_platform.health.contract import check, module_health

router = APIRouter()

_PAGE_SIZES = {25, 50, 100}
_NOTES = [
    "CLS cannot punish the server owner.",
    "A member action fails when that member's highest role is above the CLS role.",
    "Discord can refuse timeout, kick, and ban for administrators.",
    "Deleting a message needs Manage Messages. Timeout needs Moderate Members. Kick needs Kick Members. Ban needs Ban Members.",
    "A channel notice needs View Channel and Send Messages in that channel.",
]


def _health(config: dict, snapshot: dict) -> dict:
    if snapshot.get("status") == "unavailable" or not snapshot.get("checks"):
        health = module_health([check(id="bot_member", ok=False, severity="unavailable", scope="guild")])
        return {**health, "notes": _NOTES}
    by_id = {row["id"]: row for row in snapshot.get("checks") or []}
    needed: set[str] = set()
    if config.get("enabled"):
        for rule in config.get("rules") or []:
            if not rule.get("enabled") or rule.get("mode") == "observe":
                continue
            if rule.get("message_action") == "delete":
                needed.add("manage_messages")
            member = rule.get("member_action")
            if member == "timeout":
                needed.add("moderate_members")
            elif member == "kick":
                needed.add("kick_members")
            elif member == "ban":
                needed.add("ban_members")
            if rule.get("notify_action") in {"channel", "both"}:
                needed.add("send_messages")
    rows = []
    for perm in ("manage_messages", "moderate_members", "kick_members", "ban_members", "send_messages"):
        if perm not in needed:
            continue
        known = by_id.get(perm)
        rows.append(
            check(
                id=perm,
                ok=bool(known and known.get("ok")),
                severity="error",
                scope="guild",
            )
        )
    if not rows:
        rows.append(check(id="manage_messages", ok=True, severity="ok", scope="guild", label="No enforcing actions", fix_hint=None))
    return {**module_health(rows), "notes": _NOTES}


def _with_health(config: dict, bot, guild_id: int) -> dict:
    from cls_platform.health.contract import runtime_snapshot

    guild = bot.get_guild(int(guild_id)) if bot is not None else None
    snapshot = runtime_snapshot(guild)
    config = dict(config)
    config["health"] = _health(config, snapshot)
    config["native"] = {
        "connected": False,
        "label": "CLS",
        "detail": "Discord-native AutoMod is not connected. CLS is the engine that enforces these rules.",
    }
    return config


@router.get("/{guild_id}/automod/v2")
async def get_automod_v2(guild_id: int, bot=Depends(get_bot)):
    config = await ensure_config(guild_id)
    return _with_health(config, bot, guild_id)


@router.put("/{guild_id}/automod/v2")
async def put_automod_v2(guild_id: int, body: dict, bot=Depends(get_bot)):
    try:
        saved = await save_config(guild_id, body)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return _with_health(saved, bot, guild_id)


@router.get("/{guild_id}/automod/v2/overview")
async def automod_overview(guild_id: int, bot=Depends(get_bot)):
    config = await ensure_config(guild_id)
    stats = await overview(guild_id)
    stats["health"] = _with_health(config, bot, guild_id)["health"]
    stats["native"] = {"connected": False, "label": "CLS"}
    return stats


@router.get("/{guild_id}/automod/v2/violations")
async def automod_violations(
    guild_id: int,
    page: int = 1,
    page_size: int = 25,
    rule: str | None = None,
    member: str | None = None,
    channel: str | None = None,
    action: str | None = None,
    result: str | None = None,
    since: str | None = None,
    until: str | None = None,
):
    if page_size not in _PAGE_SIZES:
        raise HTTPException(status_code=422, detail="Page size must be 25, 50, or 100.")
    try:
        member_id = int(member) if member else None
        channel_id = int(channel) if channel else None
        since_at = datetime.fromisoformat(since) if since else None
        until_at = datetime.fromisoformat(until) if until else None
    except ValueError as exc:
        raise HTTPException(status_code=422, detail="Filters must use snowflake ids and ISO dates.") from exc
    return await list_violations(
        guild_id,
        page=page,
        page_size=page_size,
        rule_id=rule,
        member_id=member_id,
        channel_id=channel_id,
        action=action,
        result=result,
        since=since_at,
        until=until_at,
    )


@router.get("/{guild_id}/automod/v2/violations/{violation_id}")
async def automod_violation(guild_id: int, violation_id: str):
    row = await get_violation(guild_id, violation_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Violation not found.")
    row["followups"] = followups_for(row["rule_id"])
    return row


@router.post("/{guild_id}/automod/v2/violations/{violation_id}/false-positive")
async def automod_false_positive(guild_id: int, violation_id: str):
    row = await mark_false_positive(guild_id, violation_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Violation not found.")
    row["followups"] = followups_for(row["rule_id"])
    return row


@router.post("/{guild_id}/automod/v2/violations/{violation_id}/follow-up")
async def automod_follow_up(guild_id: int, violation_id: str, body: dict):
    if body.get("confirm") is not True:
        raise HTTPException(status_code=422, detail="Confirm the policy change before it is saved.")
    try:
        saved = await apply_followup(guild_id, violation_id, str(body.get("kind") or ""), str(body.get("value") or ""))
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return saved


@router.get("/{guild_id}/automod/v2/strikes")
async def automod_strikes(guild_id: int, member: str | None = None):
    try:
        member_id = int(member) if member else None
    except ValueError as exc:
        raise HTTPException(status_code=422, detail="Member id must be a snowflake.") from exc
    return {"rows": await list_strikes(guild_id, member_id=member_id)}


@router.post("/{guild_id}/automod/v2/test")
async def automod_test(guild_id: int, body: dict):
    """Say which rules would match. Nothing is deleted, punished, or stored."""
    config = await get_config(guild_id)
    content = str(body.get("content") or "")
    probe = dict(config)
    probe["enabled"] = True
    hits = evaluate_message(
        probe,
        content=content,
        ctx={
            "member_id": int(body["member_id"]) if str(body.get("member_id") or "").isdigit() else 1,
            "channel_id": int(body["channel_id"]) if str(body.get("channel_id") or "").isdigit() else 1,
            "category_id": int(body["category_id"]) if str(body.get("category_id") or "").isdigit() else 0,
            "role_ids": body.get("role_ids") or [],
        },
        flood_stamps=list(body.get("flood_stamps") or []),
        duplicate_history=[(float(item[0]), str(item[1])) for item in body.get("duplicate_history") or []],
        now=float(body.get("now") or datetime.now(timezone.utc).timestamp()),
        attachments=list(body.get("attachments") or []),
    )
    return {
        "matches": [
            {
                **hit,
                "would_run": [
                    {"label": action["label"], "kind": action["kind"]}
                    for action in (hit["actions"] if hit["mode"] == "observe" else plan_actions(next(rule for rule in config["rules"] if rule["id"] == hit["rule_id"])))
                ],
            }
            for hit in hits
        ]
    }


@router.get("/{guild_id}/automod/v2/presets/{preset}")
async def automod_preset(guild_id: int, preset: str):
    if preset not in {"relaxed", "balanced", "strict"}:
        raise HTTPException(status_code=404, detail="Unknown preset.")
    return {"preset": preset, "rules": preset_rules(preset)}


@router.get("/{guild_id}/automod/v2/words")
async def export_words(guild_id: int, rule: str = Query("bad_words")):
    config = await get_config(guild_id)
    found = next((item for item in config["rules"] if item["id"] == rule), None)
    if found is None:
        raise HTTPException(status_code=404, detail="Rule not found.")
    key = "terms" if rule == "bad_words" else "phrases"
    return {"rule": rule, "text": "\n".join(found["trigger"].get(key) or [])}
