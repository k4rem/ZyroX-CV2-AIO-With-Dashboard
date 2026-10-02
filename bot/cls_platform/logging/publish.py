"""Store a log event, then deliver it when a route asks. Delivery failure is not a product failure."""

from __future__ import annotations

import logging
from collections import deque
from typing import Awaitable, Callable

logger = logging.getLogger("cls.logging.publish")

Deliverer = Callable[[int, int, dict], Awaitable[None]]
_deliverer: Deliverer | None = None
RECENT_FAILURES: dict[int, deque] = {}


def set_log_deliverer(deliverer: Deliverer | None) -> None:
    global _deliverer
    _deliverer = deliverer


def recent_failures(guild_id: int) -> list[str]:
    return list(RECENT_FAILURES.get(int(guild_id), ()))


def _remember_failure(guild_id: int, message: str) -> None:
    bucket = RECENT_FAILURES.setdefault(int(guild_id), deque(maxlen=5))
    bucket.append(message[:180])


async def publish(**payload) -> dict | None:
    from cls_platform.logging.store import delivery_target, record_event

    try:
        decision = await delivery_target(int(payload["guild_id"]), payload["category"], payload["event_type"])
    except Exception:
        logger.warning("log route lookup failed guild=%s", payload.get("guild_id"))
        decision = {"capture": True, "deliver": False, "channel_id": None}
    if not decision["capture"]:
        return None
    saved = await record_event(**payload)
    if decision["deliver"] and decision["channel_id"] and _deliverer is not None:
        try:
            await _deliverer(int(payload["guild_id"]), int(decision["channel_id"]), saved)
        except Exception:
            logger.warning("log delivery failed guild=%s event=%s", payload.get("guild_id"), payload.get("event_type"))
            _remember_failure(int(payload["guild_id"]), f"{payload.get('event_type')} was stored and not delivered")
    return saved


async def log_moderation_command(
    *,
    guild_id: int,
    command: str,
    moderator_id: int,
    target_id: int,
    reason: str | None = None,
    duration: str | None = None,
    result: str = "succeeded",
    moderator_name: str | None = None,
    target_name: str | None = None,
) -> None:
    """Record a moderation command. Never raises into the command that already succeeded."""
    who = moderator_name or "A moderator"
    whom = target_name or "a member"
    bits = [f"{who} used /{command} on {whom}"]
    if duration:
        bits.append(f"for {duration}")
    if reason:
        bits.append(f"Reason: {reason[:300]}")
    sentence = " · ".join(bits)
    try:
        await publish(
            guild_id=guild_id,
            category="member_moderation",
            event_type="moderation_command",
            actor_id=moderator_id,
            actor_confidence="certain",
            target_id=target_id,
            metadata={
                "sentence": sentence,
                "command": command,
                "reason": (reason or "")[:500] or None,
                "duration": duration,
                "result": result,
                "source_module": "Moderation",
                "entities": {
                    "actor": {"id": str(moderator_id), "display_name": moderator_name or "Moderator"},
                    "target": {"id": str(target_id), "display_name": target_name or "Member"},
                },
            },
        )
    except Exception:
        logger.warning("moderation command log skipped guild=%s command=%s", guild_id, command)
