"""One-way read of legacy Automod, blacklist, and media config into V2.

Legacy databases are not modified. A stored warn is recorded and is not treated
as a working member action from the legacy row.
"""

from __future__ import annotations

import os
from typing import Any

import aiosqlite

from cls_platform.automod.engine import RULE_NAMES, fresh_config
from cls_platform.sqlite_paths import sqlite_path

_LEGACY = {
    "anti spam": "flood",
    "anti caps": "caps",
    "anti link": "links",
    "anti invites": "invites",
    "anti mass mention": "mentions",
    "anti emoji spam": "emoji",
    "anti_spam": "flood",
    "anti_caps": "caps",
    "anti_links": "links",
    "anti_invites": "invites",
    "anti_mentions": "mentions",
    "anti_emoji_spam": "emoji",
}

_MINUTES = {"flood": 12, "caps": 1, "links": 7, "invites": 12, "mentions": 3, "emoji": 1}


def _paths(name: str) -> list[str]:
    found = []
    override = os.environ.get("AUTOMOD_DB") if name == "automod.db" else None
    for path in (override, sqlite_path(name), os.path.join("db", name)):
        if path and path not in found and os.path.isfile(path):
            found.append(path)
    return found


async def _rows(path: str, sql: str, args: tuple) -> list[tuple]:
    try:
        async with aiosqlite.connect(path) as db:
            cursor = await db.execute(sql, args)
            return await cursor.fetchall()
    except Exception:
        return []


async def legacy_seed(guild_id: int) -> tuple[dict | None, list[str], bool]:
    notes: list[str] = []
    body = fresh_config("custom")
    body["preset"] = "custom"
    body["enabled"] = False
    for rule in body["rules"]:
        rule["enabled"] = False
        rule["member_action"] = "none"
        rule["message_action"] = "keep"
    saw_legacy = False
    master = False
    for path in _paths("automod.db"):
        enabled_rows = await _rows(path, "SELECT enabled FROM automod WHERE guild_id = ?", (guild_id,))
        punishments = await _rows(path, "SELECT event, punishment FROM automod_punishments WHERE guild_id = ?", (guild_id,))
        ignored = await _rows(path, "SELECT type, id FROM automod_ignored WHERE guild_id = ?", (guild_id,))
        if not enabled_rows and not punishments and not ignored:
            continue
        saw_legacy = True
        master = bool(enabled_rows and enabled_rows[0][0])
        by_id = {rule["id"]: rule for rule in body["rules"]}
        for event, punishment in punishments:
            rule_id = _LEGACY.get(str(event).strip().lower())
            if rule_id is None or rule_id not in by_id:
                notes.append(f"Left '{event}' unmigrated.")
                continue
            action = str(punishment or "").strip().lower()
            if action == "warn":
                notes.append(f"{RULE_NAMES[rule_id]} had Warn stored. It was not enforcing, so it was not copied as a member action.")
                continue
            rule = by_id[rule_id]
            if action == "delete":
                rule["message_action"] = "delete"
                rule["enabled"] = True
            elif action in {"mute", "timeout"}:
                rule["message_action"] = "delete"
                rule["member_action"] = "timeout"
                rule["timeout_seconds"] = _MINUTES.get(rule_id, 10) * 60
                rule["enabled"] = True
            elif action in {"kick", "ban"}:
                rule["message_action"] = "delete"
                rule["member_action"] = action
                rule["enabled"] = True
            else:
                notes.append(f"{RULE_NAMES[rule_id]} action '{punishment}' was not copied.")
        for kind, raw_id in ignored:
            if not str(raw_id).isdigit():
                continue
            if kind == "channel":
                body["exclusions"]["channels"].append(str(raw_id))
            elif kind == "role":
                body["exclusions"]["roles"].append(str(raw_id))
        break

    for path in _paths("blword.db"):
        words = await _rows(path, "SELECT word FROM blacklist WHERE guild_id = ?", (str(guild_id),))
        if not words:
            words = await _rows(path, "SELECT word FROM blacklist WHERE guild_id = ?", (guild_id,))
        terms = [str(row[0]).strip() for row in words if row and str(row[0]).strip()]
        if not terms:
            continue
        saw_legacy = True
        rule = next(item for item in body["rules"] if item["id"] == "bad_words")
        rule["enabled"] = True
        rule["message_action"] = "delete"
        rule["trigger"] = {"terms": terms[:200], "mode": "contains", "exceptions": []}
        notes.append(f"Imported {len(terms[:200])} blacklist words into Bad words. The old list was left in place.")
        break

    for path in _paths("media.db"):
        channels = await _rows(path, "SELECT channel_id FROM media_channels WHERE guild_id = ?", (guild_id,))
        ids = [str(row[0]) for row in channels if str(row[0]).isdigit()]
        if not ids:
            continue
        saw_legacy = True
        rule = next(item for item in body["rules"] if item["id"] == "attachments")
        rule["enabled"] = True
        rule["message_action"] = "delete"
        rule["trigger"] = {"policy": "image_channel"}
        rule["scope"]["include_channels"] = ids
        notes.append("Imported the media channel as an image-only attachment rule.")
        break

    if not saw_legacy:
        return None, [], False
    body["enabled"] = master or any(rule["enabled"] for rule in body["rules"] if rule["id"] in {"bad_words", "attachments"})
    if master:
        notes.insert(0, "Migrated the legacy Automod master switch and enforcing rules. Behavior matches those rules.")
    elif body["enabled"]:
        notes.insert(0, "Legacy Automod was off. Imported blacklist or media still starts enabled.")
    else:
        notes.insert(0, "Legacy Automod had no enforcing rules. V2 starts off.")
    return body, notes, True
