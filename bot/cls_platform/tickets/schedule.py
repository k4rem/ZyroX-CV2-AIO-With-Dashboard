"""Inactivity jobs. A new message cancels the pending warn and close, then arms a fresh pair."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from sqlalchemy import text

from cls_platform.database import session_scope
from cls_platform.services.scheduler import enqueue_job


async def cancel_pending(dedupe_key: str) -> None:
    async with session_scope() as session:
        await session.execute(
            text("UPDATE scheduler_jobs SET status = 'cancelled' WHERE dedupe_key = :key AND status = 'pending'"),
            {"key": dedupe_key},
        )


async def arm_inactivity(*, guild_id: int, ticket_id: str, generation: int, warn_seconds: int, close_seconds: int) -> None:
    warn_key = f"ticket-warn:{ticket_id}"
    close_key = f"ticket-close:{ticket_id}"
    await cancel_pending(warn_key)
    await cancel_pending(close_key)
    now = datetime.now(timezone.utc)
    payload = {"guild_id": guild_id, "ticket_id": ticket_id, "generation": generation}
    await enqueue_job("ticket_inactivity", now + timedelta(seconds=warn_seconds), {**payload, "phase": "warn"}, dedupe_key=warn_key)
    await enqueue_job(
        "ticket_inactivity",
        now + timedelta(seconds=max(close_seconds, warn_seconds + 1)),
        {**payload, "phase": "close"},
        dedupe_key=close_key,
    )


def payload_generation(payload: dict | None) -> int:
    value = (payload or {}).get("generation")
    if value is None:
        return -1
    return int(value)


def inactivity_still_due(status: str, generation: int, job_generation: int) -> bool:
    return status == "open" and int(generation) == int(job_generation)
