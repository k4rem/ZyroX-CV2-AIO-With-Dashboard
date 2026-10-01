"""One-time copy of the JSON logging config into Logging V2.

Existing V2 routes are left alone. Emoji and reaction categories have no V2
destination, so they are not copied. system_events becomes guild_events.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from sqlalchemy import func, select

from cls_platform.database import session_scope
from cls_platform.logging.store import CATEGORIES, LogIgnore, LogMigration, LogRoute

LEGACY_CATEGORY_MAP = {
    "message_events": "message_events",
    "join_leave_events": "join_leave_events",
    "member_moderation": "member_moderation",
    "voice_events": "voice_events",
    "channel_events": "channel_events",
    "role_events": "role_events",
    "system_events": "guild_events",
}


def legacy_config_path() -> Path:
    return Path(__file__).resolve().parents[2] / "jsondb" / "logging_config.json"


def _ints(values) -> list[int]:
    found = []
    for value in values or []:
        if str(value).isdigit():
            found.append(int(value))
    return found


async def migrate_legacy_payload(guild_id: int, config: dict) -> str:
    if not isinstance(config, dict):
        return "skipped"
    now = datetime.now(timezone.utc)
    async with session_scope() as session:
        if await session.get(LogMigration, guild_id) is not None:
            return "skipped"
        existing = (
            await session.execute(select(func.count()).select_from(LogRoute).where(LogRoute.guild_id == guild_id))
        ).scalar_one()
        if int(existing):
            session.add(LogMigration(guild_id=guild_id, migrated_at=now))
            return "skipped"
        enabled = config.get("log_enabled") or {}
        channels = config.get("log_channels") or {}
        written = set()
        for source, dest in LEGACY_CATEGORY_MAP.items():
            if dest not in CATEGORIES or dest in written:
                continue
            raw_channel = channels.get(source)
            channel_id = int(raw_channel) if str(raw_channel).isdigit() else None
            turned_on = bool(enabled.get(source))
            if not turned_on and channel_id is None:
                continue
            session.add(LogRoute(guild_id=guild_id, category=dest, enabled=turned_on, channel_id=channel_id))
            written.add(dest)
        for kind, key in (("channel", "ignore_channels"), ("role", "ignore_roles"), ("user", "ignore_users")):
            for entity_id in _ints(config.get(key)):
                session.add(LogIgnore(guild_id=guild_id, kind=kind, entity_id=entity_id))
        session.add(LogMigration(guild_id=guild_id, migrated_at=now))
        return "migrated"


async def migrate_legacy_file(path: Path | None = None) -> dict:
    source = path or legacy_config_path()
    if not source.exists():
        return {"migrated": 0, "skipped": 0}
    data = json.loads(source.read_text(encoding="utf-8") or "{}")
    if not isinstance(data, dict):
        return {"migrated": 0, "skipped": 0}
    migrated = skipped = 0
    for key, config in data.items():
        if not str(key).isdigit():
            continue
        result = await migrate_legacy_payload(int(key), config)
        if result == "migrated":
            migrated += 1
        else:
            skipped += 1
    return {"migrated": migrated, "skipped": skipped}
