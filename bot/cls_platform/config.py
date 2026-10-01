"""Phase 1 platform configuration (server-side only)."""

from __future__ import annotations

import os
from typing import Optional

from cls_platform.env_parse import parse_discord_snowflake_list, parse_env_bool


def _optional_snowflake(name: str) -> Optional[int]:
    raw = os.getenv(name, "").strip()
    if not raw:
        return None
    ids = parse_discord_snowflake_list(name)
    if not ids:
        return None
    return next(iter(ids))


DATABASE_URL: str = os.getenv(
    "DATABASE_URL",
    "postgresql+asyncpg://cls:cls@localhost:5432/cls_discord",
).strip()

ROOT_OWNER_ID: Optional[int] = _optional_snowflake("ROOT_OWNER_ID")
OPS_GUILD_ID: Optional[int] = _optional_snowflake("OPS_GUILD_ID")
OPS_SECURITY_ALERT_CHANNEL_ID: Optional[int] = _optional_snowflake("OPS_SECURITY_ALERT_CHANNEL_ID")

INTERNAL_SERVICE_KEY: Optional[str] = os.getenv("INTERNAL_SERVICE_KEY", "").strip() or None
INTERNAL_IDENTITY_SIGNING_KEY: Optional[str] = (
    os.getenv("INTERNAL_IDENTITY_SIGNING_KEY", "").strip() or None
)
INTERNAL_IDENTITY_AUDIENCE: str = os.getenv(
    "INTERNAL_IDENTITY_AUDIENCE", "cls-fastapi"
).strip()
INTERNAL_IDENTITY_TTL_SECONDS: int = int(os.getenv("INTERNAL_IDENTITY_TTL_SECONDS", "60"))

STORAGE_ROOT: str = os.getenv("STORAGE_ROOT", "storage").strip()
BACKUP_STAGING_DIR: str = os.getenv("BACKUP_STAGING_DIR", "backups/staging").strip()

POSTGRES_ENABLED: bool = parse_env_bool("POSTGRES_ENABLED", "true")


def root_owner_configured() -> bool:
    return ROOT_OWNER_ID is not None
