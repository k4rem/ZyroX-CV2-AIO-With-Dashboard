"""Alembic upgrade against disposable test database."""

from __future__ import annotations

import os
import subprocess
import sys

import pytest


@pytest.mark.usefixtures("postgres_ready")
def test_phase1_tables_exist():
    import asyncio
    import asyncpg

    async def check():
        conn = await asyncpg.connect(
            host="127.0.0.1",
            port=5433,
            user="postgres",
            password="cls",
            database="cls_discord_test",
        )
        tables = await conn.fetch(
            "SELECT tablename FROM pg_tables WHERE schemaname='public' ORDER BY tablename"
        )
        names = {r["tablename"] for r in tables}
        await conn.close()
        required = {
            "dashboard_sessions",
            "dashboard_roles",
            "dashboard_grants",
            "audit_events",
            "scheduler_jobs",
            "snapshot_metadata",
            "alembic_version",
        }
        missing = required - names
        assert not missing, missing

    asyncio.run(check())
