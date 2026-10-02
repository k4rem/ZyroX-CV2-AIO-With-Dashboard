"""Stable SQLite locations under the bot directory.

CWD-relative paths such as ``db/foo.db`` create a second empty database when
the process is started from another directory. This helper always points at
``<bot>/db/<name>`` and does not create the file.
"""

from __future__ import annotations

from pathlib import Path

BOT_ROOT = Path(__file__).resolve().parents[1]
DB_DIR = BOT_ROOT / "db"


def sqlite_path(name: str) -> Path:
    if not name or "/" in name or "\\" in name or name.startswith("."):
        raise ValueError("SQLite name must be a single file name")
    return DB_DIR / name


# Stores still opened with a CWD-relative path. F1 only moved the active
# legacy files this phase touches. Do not delete any of these.
REMAINING_CWD_STORES = (
    "automod.db",
    "invc.db",
    "autoreact.db",
    "welcome.db",
    "autorole.db",
    "verification.db",
    "fastgreet.db",
    "tickets",
    "logging",
)
