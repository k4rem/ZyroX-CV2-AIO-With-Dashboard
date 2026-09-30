"""PostgreSQL-backed job scheduler (SKIP LOCKED claiming)."""

from __future__ import annotations

import asyncio
import uuid
from datetime import datetime, timezone
from typing import Any, Callable, Awaitable, Optional

from sqlalchemy import select, text

from cls_platform.database import get_session_factory
from cls_platform.models import SchedulerJob

JobHandler = Callable[[SchedulerJob], Awaitable[None]]

_handlers: dict[str, JobHandler] = {}
_worker_running = False


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
        await session.commit()
        return job.id


async def run_scheduler_tick(limit: int = 5) -> int:
    """Claim and execute due jobs. Returns count processed."""
    factory = get_session_factory()
    processed = 0
    async with factory() as session:
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
            job.status = "running"
            job.attempt_count += 1
            await session.commit()

            handler = _handlers.get(job.job_type)
            try:
                if handler is None:
                    raise RuntimeError(f"No handler for job type {job.job_type}")
                await handler(job)
                job.status = "completed"
                job.completed_at = datetime.now(timezone.utc)
                job.last_error = None
            except Exception as exc:  # noqa: BLE001 — bounded retry surface
                job.status = "pending" if job.attempt_count < 5 else "failed"
                job.last_error = str(exc)[:2000]
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
