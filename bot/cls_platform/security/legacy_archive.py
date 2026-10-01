"""Read-only copy of legacy anti.db. The live file is no longer a security writer."""

from __future__ import annotations

import shutil
from pathlib import Path


def archive_legacy_anti_db(root: Path | None = None) -> str:
    base = root or Path("db")
    src = base / "anti.db"
    if not src.exists():
        return "absent"
    dest_dir = base / "archive"
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest = dest_dir / "anti.db.retired"
    if not dest.exists():
        shutil.copy2(src, dest)
    try:
        dest.chmod(0o444)
    except OSError:
        pass
    return "archived"
