"""Execute one Automod V2 decision. Each action returns its own result."""

from __future__ import annotations

import logging
import time
from collections import defaultdict, deque
from datetime import datetime, timezone
from typing import Any

from cls_platform.automod.engine import (
    LOG_EVENTS,
    evaluate_message,
    gate_action,
    highest_escalation,
    logging_sentence,
    plan_actions,
    result,
)
from cls_platform.automod.store import active_strikes, add_strike, add_violation, get_config

logger = logging.getLogger("cls.automod.v2")

_SEEN: dict[int, deque] = defaultdict(lambda: deque(maxlen=2000))
_FLOOD: dict[tuple, deque] = defaultdict(lambda: deque(maxlen=30))
_DUPES: dict[tuple, deque] = defaultdict(lambda: deque(maxlen=30))
_RATE: dict[int, deque] = defaultdict(lambda: deque(maxlen=40))
_RATE_LIMIT = 15
_RATE_WINDOW = 10


def reset_runtime_state() -> None:
    _SEEN.clear()
    _FLOOD.clear()
    _DUPES.clear()
    _RATE.clear()


def _perm(member: Any, name: str) -> bool:
    perms = getattr(member, "guild_permissions", None)
    return bool(getattr(perms, name, False))


def hierarchy_ok(member: Any, me: Any) -> bool:
    member_top = getattr(member, "top_role", None)
    bot_top = getattr(me, "top_role", None)
    if member_top is None or bot_top is None:
        return False
    member_position = int(getattr(member_top, "position", 0) or 0)
    bot_position = int(getattr(bot_top, "position", 0) or 0)
    if member_position < bot_position:
        return True
    if member_position == bot_position:
        return int(getattr(member_top, "id", 0) or 0) < int(getattr(bot_top, "id", 0) or 0)
    return False


async def _safe(label: str, action, coro) -> dict:
    try:
        await coro
    except Exception as exc:
        code = getattr(exc, "status", None) or getattr(exc, "code", None)
        text = str(exc).strip() or exc.__class__.__name__
        discord_error = f"{code}: {text}" if code else text
        logger.warning("automod action %s failed: %s", label, discord_error)
        return result(action["kind"], action["label"], "failed", text or "Discord refused the action.", discord_error=discord_error)
    return result(action["kind"], action["label"], "succeeded", f"{action['label']} completed.")


async def execute_actions(actions: list[dict], target: Any, *, observe: bool) -> list[dict]:
    outcomes = []
    perms = {
        "manage_messages": bool(getattr(target, "manage_messages", False)),
        "moderate_members": bool(getattr(target, "moderate_members", False)),
        "kick_members": bool(getattr(target, "kick_members", False)),
        "ban_members": bool(getattr(target, "ban_members", False)),
        "send_messages": bool(getattr(target, "send_messages", False)),
    }
    for action in actions:
        if observe or action.get("outcome") == "skipped":
            outcomes.append(result(action["kind"], action["label"], "skipped", "Observe mode records the match and does not punish."))
            continue
        blocked = gate_action(
            action,
            perms=perms,
            is_owner=bool(getattr(target, "is_owner", False)),
            is_admin=bool(getattr(target, "is_admin", False)),
            hierarchy_ok=bool(getattr(target, "hierarchy_ok", False)),
        )
        if blocked:
            outcomes.append(blocked)
            continue
        kind = action["kind"]
        if kind in {"timeout", "kick", "ban"}:
            stamps = _RATE[int(getattr(target, "guild_id", 0) or 0)]
            moment = time.monotonic()
            while stamps and moment - stamps[0] > _RATE_WINDOW:
                stamps.popleft()
            if len(stamps) >= _RATE_LIMIT:
                outcomes.append(result(kind, action["label"], "skipped", "Paused. Too many member actions ran in the last 10 seconds."))
                continue
            stamps.append(moment)
        if kind == "delete":
            outcomes.append(await _safe(kind, action, target.delete_messages()))
        elif kind == "warn":
            outcomes.append(result(kind, action["label"], "succeeded", "A strike was added to the moderation ledger."))
        elif kind == "timeout":
            outcomes.append(await _safe(kind, action, target.timeout(int(action["duration_seconds"]))))
        elif kind == "kick":
            outcomes.append(await _safe(kind, action, target.kick()))
        elif kind == "ban":
            outcomes.append(await _safe(kind, action, target.ban()))
        elif kind == "dm":
            outcomes.append(await _safe(kind, action, target.dm()))
        elif kind == "notice":
            outcomes.append(await _safe(kind, action, target.notice()))
        else:
            outcomes.append(result(kind, action["label"], "skipped", "This action is not available."))
    return outcomes


def _escalation_action(threshold: dict) -> dict:
    action = str(threshold["action"])
    seconds = threshold.get("duration_seconds")
    if action == "timeout":
        return {"kind": "timeout", "label": plan_actions({"member_action": "timeout", "timeout_seconds": int(seconds or 600), "message_action": "keep", "notify_action": "none"})[0]["label"], "duration_seconds": int(seconds or 600)}
    if action == "kick":
        return {"kind": "kick", "label": "Kick", "duration_seconds": None}
    return {"kind": "ban", "label": "Ban", "duration_seconds": None}


async def _log(guild_id: int, match: dict, target: Any, actions: list[dict]) -> str | None:
    try:
        from cls_platform.logging.store import record_event

        sentence = logging_sentence(match["rule_id"], match["summary"], getattr(target, "member_name", "member"), getattr(target, "channel_name", "channel"))
        recorded = await record_event(
            guild_id=guild_id,
            category="automod",
            event_type=LOG_EVENTS.get(match["rule_id"], "automod.keyword"),
            actor_id=int(getattr(target, "member_id", 0) or 0) or None,
            actor_confidence="certain",
            target_id=int(getattr(target, "member_id", 0) or 0) or None,
            channel_id=int(getattr(target, "channel_id", 0) or 0) or None,
            metadata={"sentence": sentence, "rule": match["name"], "actions": actions, "summary": match["summary"]},
        )
        return str(recorded.get("id") or "") or None
    except Exception:
        logger.exception("automod log event failed guild=%s", guild_id)
        return None


async def handle_message(target: Any, *, now: float | None = None) -> list[dict]:
    """Run the pipeline for one message. Returns the persisted violation rows."""
    guild_id = int(target.guild_id)
    message_id = int(getattr(target, "message_id", 0) or 0)
    if message_id and message_id in _SEEN[guild_id]:
        return []
    if message_id:
        _SEEN[guild_id].append(message_id)
    if getattr(target, "is_owner", False):
        return []
    config = await get_config(guild_id)
    moment = now if now is not None else time.time()
    content = str(getattr(target, "content", "") or "")
    channel_id = int(getattr(target, "channel_id", 0) or 0)
    member_id = int(target.member_id)
    flood_key = (guild_id, member_id, channel_id) if _per_channel(config) else (guild_id, member_id)
    flood_rule = next((rule for rule in config["rules"] if rule["id"] == "flood"), None)
    if flood_rule and flood_rule.get("enabled") and flood_rule.get("trigger", {}).get("per_channel"):
        flood_key = (guild_id, member_id, channel_id)
    else:
        flood_key = (guild_id, member_id)
    dupe_key = (guild_id, member_id)
    matches = evaluate_message(
        config,
        content=content,
        ctx={
            "member_id": member_id,
            "channel_id": channel_id,
            "category_id": int(getattr(target, "category_id", 0) or 0),
            "role_ids": list(getattr(target, "role_ids", []) or []),
        },
        flood_stamps=list(_FLOOD[flood_key]),
        duplicate_history=list(_DUPES[dupe_key]),
        now=moment,
        attachments=list(getattr(target, "attachments", []) or []),
        own_codes=set(getattr(target, "own_codes", []) or []),
    )
    _FLOOD[flood_key].append(moment)
    normalized = content
    from cls_platform.automod.engine import normalize_duplicate

    duplicate_rule = next((rule for rule in config["rules"] if rule["id"] == "duplicate"), {})
    token = normalize_duplicate(content) if (duplicate_rule.get("trigger") or {}).get("normalized", True) else content
    if token:
        _DUPES[dupe_key].append((moment, token))
    saved = []
    for match in matches:
        observe = match["mode"] == "observe"
        planned = match["actions"] if observe else plan_actions(_rule_from_match(config, match["rule_id"]))
        outcomes = await execute_actions(planned, target, observe=observe)
        strike_effect = None
        points = int(match.get("points") or 0)
        if any(item.get("kind") == "warn" for item in planned) and points < 1:
            points = 1
        if points > 0 and not observe:
            ttl = int(config.get("strike_ttl_seconds") or 604800)
            strike = await add_strike(
                guild_id=guild_id,
                member_id=member_id,
                rule_id=match["rule_id"],
                reason=match["summary"],
                points=points,
                ttl_seconds=ttl,
                source="automod",
                violation_id=None,
                moderator_id=None,
            )
            recent = await active_strikes(guild_id, member_id)
            chosen = highest_escalation(recent, config.get("escalations") or [], moment)
            already = {item["kind"] for item in outcomes if item["outcome"] == "succeeded"}
            strike_effect = {"strike_id": strike["id"], "points": points}
            if chosen and chosen["action"] not in already:
                extra = _escalation_action(chosen)
                escalated = await execute_actions([extra], target, observe=False)
                outcomes.extend(escalated)
                strike_effect["threshold"] = chosen
                strike_effect["results"] = escalated
            elif chosen:
                skipped = result(chosen["action"], chosen["action"], "skipped", "The rule already applied this action.")
                outcomes.append(skipped)
                strike_effect["threshold"] = chosen
                strike_effect["results"] = [skipped]
        log_id = await _log(guild_id, match, target, outcomes)
        violation_id = await add_violation(
            guild_id=guild_id,
            member_id=member_id,
            channel_id=channel_id or None,
            message_id=message_id or None,
            rule_id=match["rule_id"],
            summary=match["summary"],
            excerpt=match["excerpt"],
            detail={
                "threshold": match["threshold"],
                "detector": {"summary": match["summary"], "engine": "cls"},
                "scope": match["scope"],
                "engine": "cls",
                "actions": outcomes,
                "strike": strike_effect,
            },
            actions=outcomes,
            log_event_id=log_id,
            occurred_at=datetime.fromtimestamp(moment, tz=timezone.utc),
        )
        if strike_effect and strike_effect.get("strike_id") is None and points > 0:
            pass
        saved.append({"id": violation_id, "rule_id": match["rule_id"], "actions": outcomes, "sentence": logging_sentence(match["rule_id"], match["summary"], getattr(target, "member_name", "member"), getattr(target, "channel_name", "channel"))})
    return saved


def _per_channel(config: dict) -> bool:
    rule = next((item for item in config.get("rules") or [] if item["id"] == "flood"), None)
    return bool(rule and (rule.get("trigger") or {}).get("per_channel"))


def _rule_from_match(config: dict, rule_id: str) -> dict:
    return next(rule for rule in config["rules"] if rule["id"] == rule_id)


async def record_manual_warning(*, guild_id: int, member_id: int, moderator_id: int, reason: str) -> dict:
    """Bridge a /warn into the same ledger. warn.db remains a display counter until F5."""
    config = await get_config(guild_id)
    return await add_strike(
        guild_id=guild_id,
        member_id=member_id,
        rule_id="manual",
        reason=reason or "Manual warning",
        points=1,
        ttl_seconds=int(config.get("strike_ttl_seconds") or 604800),
        source="manual",
        violation_id=None,
        moderator_id=moderator_id,
    )
