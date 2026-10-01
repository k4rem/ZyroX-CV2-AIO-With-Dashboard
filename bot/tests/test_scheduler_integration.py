"""Scheduler persistence + restart semantics (Postgres, mocked Discord)."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock

import pytest

from tests.conftest import TEST_GUILD_A, TEST_ROLE_A, TEST_USER


@pytest.mark.asyncio
async def test_scheduler_job_completes_once(db_reset, fake_bot):
    from cls_platform.database import init_database
    from cls_platform.services.scheduler import enqueue_job, register_job_handler, run_scheduler_tick

    await init_database()
    calls = {"n": 0}

    async def handler(job):
        calls["n"] += 1

    register_job_handler("test_job", handler)
    run_at = datetime.now(timezone.utc) - timedelta(seconds=1)
    await enqueue_job("test_job", run_at, {"k": 1}, dedupe_key="test:1")
    assert await run_scheduler_tick() == 1
    assert calls["n"] == 1
    assert await run_scheduler_tick() == 0


@pytest.mark.asyncio
async def test_role_temp_remove_missing_member_safe(db_reset, fake_bot):
    from cls_platform.scheduler_bootstrap import register_scheduler_handlers
    from cls_platform.services.scheduler import enqueue_job, run_scheduler_tick

    register_scheduler_handlers(fake_bot)
    run_at = datetime.now(timezone.utc) - timedelta(seconds=1)
    await enqueue_job(
        "role_temp_remove",
        run_at,
        {"guild_id": TEST_GUILD_A, "user_id": TEST_USER, "role_id": TEST_ROLE_A},
        dedupe_key="rt:1",
    )
    processed = await run_scheduler_tick()
    assert processed == 1


@pytest.mark.asyncio
async def test_scheduler_bounded_retry(db_reset):
    from cls_platform.services.scheduler import enqueue_job, register_job_handler, run_scheduler_tick
    from cls_platform.database import get_session_factory
    from cls_platform.models import SchedulerJob
    from sqlalchemy import select

    async def boom(job):
        raise RuntimeError("discord down")

    register_job_handler("fail_job", boom)
    jid = await enqueue_job(
        "fail_job",
        datetime.now(timezone.utc),
        {},
        dedupe_key="fail:1",
    )
    from sqlalchemy import text

    for _ in range(6):
        await run_scheduler_tick()
        factory = get_session_factory()
        async with factory() as session:
            await session.execute(
                text(
                    "UPDATE scheduler_jobs SET run_at = NOW() - interval '1 second' "
                    "WHERE status = 'pending'"
                )
            )
            await session.commit()
    factory = get_session_factory()
    async with factory() as session:
        row = (
            await session.execute(select(SchedulerJob).where(SchedulerJob.id == jid))
        ).scalar_one()
        assert row.status == "failed"
        assert row.attempt_count >= 5


@pytest.mark.asyncio
async def test_scheduler_survives_worker_restart(db_reset):
    """Job row persists in Postgres; a later tick completes it exactly once."""
    import uuid

    from cls_platform.services.scheduler import enqueue_job, register_job_handler, run_scheduler_tick
    from cls_platform.database import get_session_factory
    from cls_platform.models import SchedulerJob
    from sqlalchemy import select

    calls = {"n": 0}

    async def handler(job):
        calls["n"] += 1

    register_job_handler("restart_job", handler)
    run_at = datetime.now(timezone.utc) - timedelta(seconds=1)
    jid = await enqueue_job(
        "restart_job",
        run_at,
        {"marker": "restart"},
        dedupe_key=f"restart:{uuid.uuid4()}",
    )
    assert await run_scheduler_tick() == 1
    assert calls["n"] == 1
    factory = get_session_factory()
    async with factory() as session:
        row = (await session.execute(select(SchedulerJob).where(SchedulerJob.id == jid))).scalar_one()
        assert row.status == "completed"
    assert await run_scheduler_tick() == 0


@pytest.mark.asyncio
async def test_repeated_temprole_and_failed_history_can_schedule_again(db_reset):
    from sqlalchemy import select

    from cls_platform.database import get_session_factory
    from cls_platform.models import SchedulerJob
    from cls_platform.services.scheduler import enqueue_job, register_job_handler, run_scheduler_tick

    async def handler(job):
        return None

    register_job_handler("role_temp_remove", handler)
    key = f"role_temp:{TEST_GUILD_A}:{TEST_USER}:{TEST_ROLE_A}"
    payload = {"guild_id": TEST_GUILD_A, "user_id": TEST_USER, "role_id": TEST_ROLE_A}
    past = datetime.now(timezone.utc) - timedelta(seconds=1)
    first = await enqueue_job("role_temp_remove", past, payload, dedupe_key=key)
    assert await run_scheduler_tick() >= 1
    second = await enqueue_job(
        "role_temp_remove",
        datetime.now(timezone.utc) + timedelta(seconds=30),
        payload,
        dedupe_key=key,
    )
    assert second != first
    duplicate = await enqueue_job("role_temp_remove", past, payload, dedupe_key=key)
    assert duplicate == second
    factory = get_session_factory()
    async with factory() as session:
        row = (await session.execute(select(SchedulerJob).where(SchedulerJob.id == second))).scalar_one()
        row.status = "failed"
        await session.commit()
    third = await enqueue_job("role_temp_remove", past, payload, dedupe_key=key)
    assert third not in {first, second}


@pytest.mark.asyncio
async def test_stale_running_lease_is_reclaimed(db_reset):
    from sqlalchemy import select

    from cls_platform.database import get_session_factory
    from cls_platform.models import SchedulerJob
    from cls_platform.services.scheduler import enqueue_job, register_job_handler, run_scheduler_tick

    calls = {"n": 0}

    async def handler(job):
        calls["n"] += 1

    register_job_handler("role_temp_remove", handler)
    key = f"role_temp:stale:{TEST_USER}"
    job_id = await enqueue_job(
        "role_temp_remove",
        datetime.now(timezone.utc) + timedelta(hours=1),
        {"guild_id": TEST_GUILD_A, "user_id": TEST_USER, "role_id": TEST_ROLE_A},
        dedupe_key=key,
    )
    factory = get_session_factory()
    async with factory() as session:
        row = (await session.execute(select(SchedulerJob).where(SchedulerJob.id == job_id))).scalar_one()
        row.status = "running"
        row.lease_until = datetime.now(timezone.utc) - timedelta(seconds=5)
        row.attempt_count = 1
        await session.commit()
    assert await run_scheduler_tick() >= 1
    assert calls["n"] == 1
