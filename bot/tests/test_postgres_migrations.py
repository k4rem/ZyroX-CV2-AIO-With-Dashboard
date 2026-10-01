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
        required = {
            "dashboard_sessions",
            "dashboard_roles",
            "dashboard_grants",
            "audit_events",
            "scheduler_jobs",
            "snapshot_metadata",
            "security_guild_configs",
            "security_action_policies",
            "security_trusted_actors",
            "security_guild_state",
            "security_gateway_signals",
            "security_observations",
            "security_incidents",
            "security_incident_events",
            "security_response_actions",
            "security_quarantines",
            "security_maintenance_windows",
            "security_alert_outbox",
            "alembic_version",
        }
        missing = required - names
        assert not missing, missing
        unique = await conn.fetch(
            """
            SELECT indexname, indexdef
            FROM pg_indexes
            WHERE schemaname = 'public'
              AND indexname IN (
                'uq_security_observations_audit',
                'ix_security_gateway_signals_correlation',
                'uq_security_incidents_active'
              )
            """
        )
        by_name = {row["indexname"]: row["indexdef"] for row in unique}
        assert "UNIQUE" in by_name["uq_security_observations_audit"].upper()
        assert "UNIQUE" not in by_name["ix_security_gateway_signals_correlation"].upper()
        assert "UNIQUE" in by_name["uq_security_incidents_active"].upper()
        await conn.close()

    asyncio.run(check())


@pytest.mark.usefixtures("postgres_ready")
def test_security_migration_downgrade_and_upgrade():
    bot_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    env = os.environ.copy()
    down = subprocess.run(
        [sys.executable, "-m", "alembic", "downgrade", "20260330_0001"],
        cwd=bot_dir,
        env=env,
        capture_output=True,
        text=True,
    )
    try:
        assert down.returncode == 0, down.stderr
    finally:
        up = subprocess.run(
            [sys.executable, "-m", "alembic", "upgrade", "head"],
            cwd=bot_dir,
            env=env,
            capture_output=True,
            text=True,
        )
    assert up.returncode == 0, up.stderr
