#!/usr/bin/env python3
"""Phase 1 backup runner (local staging + optional restic)."""

from __future__ import annotations

import argparse
import os
import shutil
import sqlite3
import subprocess
import tempfile
from datetime import datetime
from pathlib import Path


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


def backup_tree(staging: Path) -> None:
    ts = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
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
        dump_path = run_dir / "postgres.sql"
        # sync pg_dump via DATABASE_URL host parsing is deployment-specific; use env PGHOST if set
        env = os.environ.copy()
        subprocess.run(
            ["pg_dump", "-f", str(dump_path)],
            check=False,
            env=env,
        )

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
        backup_tree(staging)
        print(f"Backup staged under {staging}")
    elif args.command == "verify":
        print("Restore verification is manual: copy staged artifacts to scratch paths and validate.")


if __name__ == "__main__":
    main()
