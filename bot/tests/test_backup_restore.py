"""Local backup + restore scratch validation."""

from __future__ import annotations

import json
import os
import sqlite3
import subprocess
import sys
from pathlib import Path

import pytest


@pytest.mark.usefixtures("postgres_ready")
def test_backup_restore_sqlite_and_json(tmp_path, monkeypatch):
    bot_dir = Path(__file__).resolve().parents[1]
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

    from scripts import cls_backup

    cls_backup.backup_tree(staging)
    runs = list(staging.iterdir())
    assert runs
    run_dir = runs[0]
    assert (run_dir / "sqlite" / "sample.db").is_file()
    assert (run_dir / "jsondb" / "state.json").is_file()

    restore_db = scratch / "restored.db"
    cls_backup.backup_sqlite(run_dir / "sqlite" / "sample.db", restore_db)
    conn = sqlite3.connect(restore_db)
    row = conn.execute("SELECT v FROM t").fetchone()
    conn.close()
    assert row[0] == "phase1-marker"

    restored_json = json.loads((run_dir / "jsondb" / "state.json").read_text(encoding="utf-8"))
    assert restored_json["marker"] == "phase1-json"

    assert not (run_dir / ".env").exists()
