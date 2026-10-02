"""Structured Logging V2 events for Security Center. Presentation is finished in F4."""

from __future__ import annotations

from cls_platform.logging.store import record_event


async def security_event(
    *,
    guild_id: int,
    event_type: str,
    sentence: str,
    actor_id: int | None = None,
    target_id: int | None = None,
    channel_id: int | None = None,
    confidence: str = "unknown",
) -> None:
    if confidence not in {"certain", "probable", "unknown"}:
        confidence = "unknown"
    await record_event(
        guild_id=guild_id,
        category="security",
        event_type=event_type,
        actor_id=actor_id,
        actor_confidence=confidence if actor_id is not None else "unknown",
        target_id=target_id,
        channel_id=channel_id,
        metadata={"sentence": sentence},
    )
