"""PostgreSQL-backed job scheduler (SKIP LOCKED claiming)."""

from __future__ import annotations

import asyncio
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Callable, Awaitable, Optional

from sqlalchemy import select, text
from sqlalchemy.exc import IntegrityError

from cls_platform.database import get_session_factory
from cls_platform.models import SchedulerJob

JobHandler = Callable[[SchedulerJob], Awaitable[None]]

_handlers: dict[str, JobHandler] = {}
_worker_running = False

MAX_ATTEMPTS = 5
LEASE = timedelta(seconds=60)
BACKOFF_CAP_S = 300


def backoff_delay(attempt_count: int) -> timedelta:
    """Exponential backoff after a failed attempt. Attempt count is 1-based."""
    seconds = min(BACKOFF_CAP_S, 2 ** max(attempt_count, 1))
    return timedelta(seconds=seconds)


def register_job_handler(job_type: str, handler: JobHandler) -> None:
    _handlers[job_type] = handler


async def enqueue_job(
    job_type: str,
    run_at: datetime,
    payload: dict[str, Any],
    dedupe_key: Optional[str] = None,
) -> uuid.UUID:
    factory = get_session_factory()
    async with factory() as session:
        job = SchedulerJob(
            job_type=job_type,
            run_at=run_at if run_at.tzinfo else run_at.replace(tzinfo=timezone.utc),
            payload=payload,
            dedupe_key=dedupe_key,
            status="pending",
        )
        session.add(job)
        try:
            await session.commit()
            return job.id
        except IntegrityError:
            await session.rollback()
            if not dedupe_key:
                raise
    async with factory() as session:
        existing = (
            await session.execute(select(SchedulerJob.id).where(SchedulerJob.dedupe_key == dedupe_key))
        ).scalar_one()
        return existing


async def _reclaim_abandoned(session) -> None:
    """Return running jobs whose lease expired. Exhausted attempts become failed."""
    await session.execute(
        text(
            """
            UPDATE scheduler_jobs
            SET status = CASE WHEN attempt_count >= :max_attempts THEN 'failed' ELSE 'pending' END,
                run_at = CASE
                    WHEN attempt_count >= :max_attempts THEN run_at
                    ELSE NOW()
                END,
                lease_until = NULL,
                last_error = COALESCE(last_error, 'abandoned running lease reclaimed')
            WHERE status = 'running'
              AND (lease_until IS NULL OR lease_until < NOW())
            """
        ),
        {"max_attempts": MAX_ATTEMPTS},
    )


async def run_scheduler_tick(limit: int = 5) -> int:
    """Claim and execute due jobs. Returns count processed.

    Claiming uses FOR UPDATE SKIP LOCKED. A second worker cannot take a row
    this worker already locked. Abandoned running rows are reclaimed only
    after their lease expires.
    """
    factory = get_session_factory()
    processed = 0
    async with factory() as session:
        await _reclaim_abandoned(session)
        result = await session.execute(
            text(
                """
                SELECT id FROM scheduler_jobs
                WHERE status = 'pending' AND run_at <= NOW()
                ORDER BY run_at ASC
                LIMIT :lim
                FOR UPDATE SKIP LOCKED
                """
            ),
            {"lim": limit},
        )
        ids = [row[0] for row in result.fetchall()]
        for job_id in ids:
            job_result = await session.execute(
                select(SchedulerJob).where(SchedulerJob.id == job_id).with_for_update()
            )
            job = job_result.scalar_one_or_none()
            if not job or job.status != "pending":
                continue
            now = datetime.now(timezone.utc)
            job.status = "running"
            job.attempt_count = int(job.attempt_count or 0) + 1
            job.claimed_at = now
            job.lease_until = now + LEASE
            await session.commit()

            handler = _handlers.get(job.job_type)
            try:
                if handler is None:
                    raise RuntimeError(f"No handler for job type {job.job_type}")
                await handler(job)
                job.status = "completed"
                job.completed_at = datetime.now(timezone.utc)
                job.last_error = None
                job.lease_until = None
            except Exception as exc:  # noqa: BLE001 — bounded retry surface
                job.lease_until = None
                job.last_error = str(exc)[:2000]
                if job.attempt_count < MAX_ATTEMPTS:
                    job.status = "pending"
                    job.run_at = datetime.now(timezone.utc) + backoff_delay(job.attempt_count)
                else:
                    job.status = "failed"
            await session.commit()
            processed += 1
    return processed


async def scheduler_worker_loop(stop_event: asyncio.Event, interval: float = 5.0) -> None:
    global _worker_running
    _worker_running = True
    while not stop_event.is_set():
        try:
            await run_scheduler_tick()
        except Exception:
            pass
        try:
            await asyncio.wait_for(stop_event.wait(), timeout=interval)
        except asyncio.TimeoutError:
            continue
    _worker_running = False
