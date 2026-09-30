#!/usr/bin/env python3
"""Phase 1 backup runner (local staging + optional restic)."""

from __future__ import annotations

import argparse
import os
import shutil
import sqlite3
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse


def backup_sqlite(src: Path, dest: Path) -> None:
    """Consistent SQLite copy using the backup API."""
    dest.parent.mkdir(parents=True, exist_ok=True)
    if not src.is_file():
        return
    src_conn = sqlite3.connect(str(src))
    dest_conn = sqlite3.connect(str(dest))
    try:
        src_conn.backup(dest_conn)
    finally:
        dest_conn.close()
        src_conn.close()


def _normalize_pg_url(database_url: str) -> str:
    url = database_url.strip()
    for prefix in ("postgresql+asyncpg://", "postgresql+psycopg2://", "postgresql+psycopg://"):
        if url.startswith(prefix):
            return "postgresql://" + url[len(prefix) :]
    return url


def postgres_env_from_url(database_url: str) -> tuple[dict[str, str], str]:
    """Build pg_dump/psql environment from DATABASE_URL (password via env, not argv)."""
    env = os.environ.copy()
    parsed = urlparse(_normalize_pg_url(database_url))
    if parsed.hostname:
        env["PGHOST"] = parsed.hostname
    if parsed.port:
        env["PGPORT"] = str(parsed.port)
    if parsed.username:
        env["PGUSER"] = parsed.username
    if parsed.password:
        env["PGPASSWORD"] = parsed.password
    dbname = (parsed.path or "/postgres").lstrip("/") or "postgres"
    env["PGDATABASE"] = dbname
    return env, dbname


def backup_postgres(dump_path: Path, database_url: str | None = None) -> None:
    """Logical PostgreSQL backup via pg_dump (plain SQL). Raises on failure."""
    url = (database_url or os.getenv("DATABASE_URL", "")).strip()
    if not url.startswith("postgresql"):
        return
    env, _ = postgres_env_from_url(url)
    dump_path.parent.mkdir(parents=True, exist_ok=True)
    proc = subprocess.run(
        ["pg_dump", "-f", str(dump_path), "--no-owner", "--no-acl"],
        env=env,
        capture_output=True,
        text=True,
    )
    if proc.returncode != 0:
        detail = (proc.stderr or proc.stdout or "unknown error").strip()
        raise RuntimeError(f"pg_dump failed (exit {proc.returncode}): {detail}")
    if not dump_path.is_file() or dump_path.stat().st_size == 0:
        raise RuntimeError("pg_dump produced empty output")


def _psql_compatible_dump_path(dump_path: Path) -> Path:
    """Drop SET lines newer psql versions emit that older clients reject."""
    raw = dump_path.read_text(encoding="utf-8", errors="replace")
    skip = (
        "SET transaction_timeout",
        "SET idle_session_timeout",
    )
    filtered = [ln for ln in raw.splitlines() if not any(ln.strip().startswith(p) for p in skip)]
    if filtered == raw.splitlines():
        return dump_path
    compatible = dump_path.with_name(dump_path.stem + ".psql_compat.sql")
    compatible.write_text("\n".join(filtered) + "\n", encoding="utf-8")
    return compatible


def restore_postgres_sql(dump_path: Path, target_database_url: str) -> None:
    """Restore plain SQL dump into target database via psql. Raises on failure."""
    if not dump_path.is_file():
        raise RuntimeError("postgres dump file missing")
    env, _ = postgres_env_from_url(target_database_url)
    sql_path = _psql_compatible_dump_path(dump_path)
    proc = subprocess.run(
        ["psql", "-v", "ON_ERROR_STOP=1", "-f", str(sql_path)],
        env=env,
        capture_output=True,
        text=True,
    )
    if proc.returncode != 0:
        detail = (proc.stderr or proc.stdout or "unknown error").strip()
        raise RuntimeError(f"psql restore failed (exit {proc.returncode}): {detail}")


def backup_tree(staging: Path) -> None:
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    run_dir = staging / ts
    run_dir.mkdir(parents=True, exist_ok=True)

    db_dir = Path("db")
    if db_dir.is_dir():
        for f in db_dir.glob("*.db"):
            backup_sqlite(f, run_dir / "sqlite" / f.name)

    for extra in ("j2c_data.db", "rr.db"):
        p = Path(extra)
        if p.is_file():
            backup_sqlite(p, run_dir / "sqlite" / p.name)

    jsondb = Path("jsondb")
    if jsondb.is_dir():
        shutil.copytree(jsondb, run_dir / "jsondb", dirs_exist_ok=True)

    pg_url = os.getenv("DATABASE_URL", "")
    if pg_url.startswith("postgresql"):
        backup_postgres(run_dir / "postgres.sql", pg_url)

    repo = os.getenv("RESTIC_REPOSITORY", "").strip()
    if repo:
        password = os.getenv("RESTIC_PASSWORD", "")
        subprocess.run(
            ["restic", "backup", str(run_dir)],
            check=False,
            env={**os.environ, "RESTIC_PASSWORD": password},
        )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=["run", "verify"])
    args = parser.parse_args()
    staging = Path(os.getenv("BACKUP_STAGING_DIR", "backups/staging"))
    if args.command == "run":
        try:
            backup_tree(staging)
        except RuntimeError as exc:
            print(str(exc), file=sys.stderr)
            sys.exit(1)
        print(f"Backup staged under {staging}")
    elif args.command == "verify":
        print("Restore verification is manual: copy staged artifacts to scratch paths and validate.")


if __name__ == "__main__":
    main()
