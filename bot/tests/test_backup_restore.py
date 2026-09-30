"""Local backup + restore scratch validation (SQLite, JSON, PostgreSQL)."""

from __future__ import annotations

import asyncio
import json
import os
import sqlite3
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import urlparse

import pytest

from scripts.cls_backup import (
    _normalize_pg_url,
    backup_postgres,
    backup_tree,
    postgres_env_from_url,
    restore_postgres_sql,
)

MARKER_SESSION_ID = uuid.UUID("11111111-1111-4111-8111-111111111111")
MARKER_AUDIT_ID = uuid.UUID("22222222-2222-4222-8222-222222222222")
MARKER_SCHEDULER_ID = uuid.UUID("33333333-3333-4333-8333-333333333333")
MARKER_USER = 800000000000009999
MARKER_AUDIT_ACTION = "phase1-pg-backup-marker"
MARKER_SCHEDULER_DEDUPE = "phase1-pg-backup-scheduler-marker"
RESTORE_DB_NAME = "cls_discord_restore_test"


def _pg_tool_available() -> bool:
    import shutil

    return bool(shutil.which("pg_dump") and shutil.which("psql"))


def _admin_connect_kwargs() -> dict:
    url = os.environ.get(
        "DATABASE_URL",
        "postgresql+asyncpg://postgres:cls@127.0.0.1:5433/cls_discord_test",
    )
    parsed = urlparse(_normalize_pg_url(url))
    return {
        "host": parsed.hostname or "127.0.0.1",
        "port": int(parsed.port or 5432),
        "user": parsed.username or "postgres",
        "password": parsed.password or "",
    }


def _database_url_for(dbname: str) -> str:
    base = os.environ.get(
        "DATABASE_URL",
        "postgresql+asyncpg://postgres:cls@127.0.0.1:5433/cls_discord_test",
    )
    parsed = urlparse(_normalize_pg_url(base))
    user = parsed.username or "postgres"
    password = parsed.password or ""
    host = parsed.hostname or "127.0.0.1"
    port = parsed.port or 5432
    auth = user if not password else f"{user}:{password}"
    return f"postgresql://{auth}@{host}:{port}/{dbname}"


async def _insert_pg_markers(source_db: str) -> None:
    import asyncpg

    kw = _admin_connect_kwargs()
    conn = await asyncpg.connect(database=source_db, **kw)
    try:
        await conn.execute(
            """
            TRUNCATE dashboard_grants, audit_events, scheduler_jobs, dashboard_sessions
            RESTART IDENTITY CASCADE
            """
        )
        expires = datetime.now(timezone.utc) + timedelta(hours=24)
        await conn.execute(
            """
            INSERT INTO dashboard_sessions
                (id, discord_user_id, expires_at, revoked_reason)
            VALUES ($1, $2, $3, $4)
            """,
            MARKER_SESSION_ID,
            MARKER_USER,
            expires,
            "phase1-pg-backup-session-marker",
        )
        await conn.execute(
            """
            INSERT INTO audit_events (id, actor_user_id, action, context)
            VALUES ($1, $2, $3, $4::jsonb)
            """,
            MARKER_AUDIT_ID,
            MARKER_USER,
            MARKER_AUDIT_ACTION,
            json.dumps({"marker": "phase1-pg-audit"}),
        )
        run_at = datetime.now(timezone.utc) + timedelta(hours=1)
        await conn.execute(
            """
            INSERT INTO scheduler_jobs
                (id, job_type, dedupe_key, run_at, payload, status)
            VALUES ($1, $2, $3, $4, $5::jsonb, 'pending')
            """,
            MARKER_SCHEDULER_ID,
            "phase1_backup_test",
            MARKER_SCHEDULER_DEDUPE,
            run_at,
            json.dumps({"marker": "phase1-pg-scheduler"}),
        )
    finally:
        await conn.close()


async def _drop_create_db(dbname: str) -> None:
    import asyncpg

    kw = _admin_connect_kwargs()
    conn = await asyncpg.connect(database="postgres", **kw)
    try:
        await conn.execute(
            "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname = $1 AND pid <> pg_backend_pid()",
            dbname,
        )
        await conn.execute(f'DROP DATABASE IF EXISTS "{dbname}"')
        await conn.execute(f'CREATE DATABASE "{dbname}"')
    finally:
        await conn.close()


async def _verify_restored_markers(dbname: str) -> None:
    import asyncpg

    kw = _admin_connect_kwargs()
    conn = await asyncpg.connect(database=dbname, **kw)
    try:
        alembic = await conn.fetchval("SELECT version_num FROM alembic_version LIMIT 1")
        assert alembic

        session = await conn.fetchrow(
            "SELECT discord_user_id, revoked_reason FROM dashboard_sessions WHERE id = $1",
            MARKER_SESSION_ID,
        )
        assert session is not None
        assert session["discord_user_id"] == MARKER_USER
        assert session["revoked_reason"] == "phase1-pg-backup-session-marker"

        audit = await conn.fetchrow(
            "SELECT action, context FROM audit_events WHERE id = $1",
            MARKER_AUDIT_ID,
        )
        assert audit is not None
        assert audit["action"] == MARKER_AUDIT_ACTION
        audit_ctx = audit["context"]
        if isinstance(audit_ctx, str):
            audit_ctx = json.loads(audit_ctx)
        assert audit_ctx["marker"] == "phase1-pg-audit"

        job = await conn.fetchrow(
            "SELECT dedupe_key, payload FROM scheduler_jobs WHERE id = $1",
            MARKER_SCHEDULER_ID,
        )
        assert job is not None
        assert job["dedupe_key"] == MARKER_SCHEDULER_DEDUPE
        job_payload = job["payload"]
        if isinstance(job_payload, str):
            job_payload = json.loads(job_payload)
        assert job_payload["marker"] == "phase1-pg-scheduler"

        fk = await conn.fetchval(
            """
            SELECT 1 FROM information_schema.table_constraints
            WHERE table_name = 'dashboard_grants' AND constraint_type = 'FOREIGN KEY'
            LIMIT 1
            """
        )
        assert fk == 1
    finally:
        await conn.close()


@pytest.mark.usefixtures("postgres_ready")
def test_backup_restore_sqlite_and_json(tmp_path, monkeypatch):
    staging = tmp_path / "staging"
    scratch = tmp_path / "scratch"
    db_dir = tmp_path / "db"
    json_dir = tmp_path / "jsondb"
    db_dir.mkdir()
    json_dir.mkdir()

    src_db = db_dir / "sample.db"
    conn = sqlite3.connect(src_db)
    conn.execute("CREATE TABLE t (id INTEGER PRIMARY KEY, v TEXT)")
    conn.execute("INSERT INTO t (v) VALUES ('phase1-marker')")
    conn.commit()
    conn.close()
    (json_dir / "state.json").write_text(json.dumps({"marker": "phase1-json"}), encoding="utf-8")

    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("BACKUP_STAGING_DIR", str(staging))
    monkeypatch.delenv("DATABASE_URL", raising=False)

    backup_tree(staging)
    runs = list(staging.iterdir())
    assert runs
    run_dir = runs[0]
    assert (run_dir / "sqlite" / "sample.db").is_file()
    assert (run_dir / "jsondb" / "state.json").is_file()

    restore_db = scratch / "restored.db"
    from scripts import cls_backup

    cls_backup.backup_sqlite(run_dir / "sqlite" / "sample.db", restore_db)
    conn = sqlite3.connect(restore_db)
    row = conn.execute("SELECT v FROM t").fetchone()
    conn.close()
    assert row[0] == "phase1-marker"

    restored_json = json.loads((run_dir / "jsondb" / "state.json").read_text(encoding="utf-8"))
    assert restored_json["marker"] == "phase1-json"

    assert not (run_dir / ".env").exists()


@pytest.mark.usefixtures("postgres_ready")
def test_backup_restore_postgres_roundtrip(tmp_path, monkeypatch):
    if not _pg_tool_available():
        pytest.skip("pg_dump/psql not on PATH")

    source_db = "cls_discord_test"
    asyncio.run(_insert_pg_markers(source_db))

    staging = tmp_path / "staging"
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("BACKUP_STAGING_DIR", str(staging))
    monkeypatch.setenv("DATABASE_URL", _database_url_for(source_db))

    backup_tree(staging)
    run_dir = next(staging.iterdir())
    dump_path = run_dir / "postgres.sql"
    assert dump_path.is_file()
    assert dump_path.stat().st_size > 0

    dump_text = dump_path.read_text(encoding="utf-8", errors="replace")
    assert "PGPASSWORD" not in dump_text
    assert "DATABASE_URL" not in dump_text
    env, _ = postgres_env_from_url(_database_url_for(source_db))
    password = env.get("PGPASSWORD", "")
    if password:
        assert password not in dump_text

    asyncio.run(_drop_create_db(RESTORE_DB_NAME))
    restore_postgres_sql(dump_path, _database_url_for(RESTORE_DB_NAME))
    asyncio.run(_verify_restored_markers(RESTORE_DB_NAME))


def test_pg_dump_invalid_target_fails(tmp_path):
    if not _pg_tool_available():
        pytest.skip("pg_dump not on PATH")

    bad_url = "postgresql://postgres:cls@127.0.0.1:59999/nonexistent_db"
    dump_path = tmp_path / "bad.sql"
    with pytest.raises(RuntimeError, match="pg_dump failed"):
        backup_postgres(dump_path, bad_url)
    assert not dump_path.is_file() or dump_path.stat().st_size == 0
