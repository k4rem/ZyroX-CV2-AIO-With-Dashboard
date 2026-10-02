"""CLS config bundle shape. Version 1 is the only format this build imports."""

from __future__ import annotations

import re
from datetime import datetime, timezone

FORMAT = "cls-config"
VERSION = 1
MAX_BYTES = 1_500_000

SECRET_KEYS = {
    "token",
    "secret",
    "password",
    "cookie",
    "session",
    "authorization",
    "api_key",
    "signing_key",
    "client_secret",
    "access_token",
    "refresh_token",
}

MODULES = (
    {"id": "welcome", "label": "Welcome", "group": "messaging"},
    {"id": "welcome_dm", "label": "Welcome DM", "group": "messaging"},
    {"id": "goodbye", "label": "Goodbye", "group": "messaging"},
    {"id": "messages", "label": "Message templates", "group": "messaging"},
    {"id": "logging", "label": "Logging", "group": "moderation"},
    {"id": "automod", "label": "Automod", "group": "moderation"},
    {"id": "tickets", "label": "Tickets", "group": "support"},
    {"id": "role_menus", "label": "Role Menus", "group": "roles"},
    {"id": "join_roles", "label": "Join Roles", "group": "roles"},
    {"id": "role_automation", "label": "Role Automation", "group": "roles"},
    {"id": "commands", "label": "Commands", "group": "system"},
    {"id": "j2c", "label": "Join to Create", "group": "engagement"},
    {"id": "autoreact", "label": "Auto React", "group": "engagement"},
)

GROUPS = (
    {"id": "messaging", "label": "Messaging"},
    {"id": "moderation", "label": "Moderation"},
    {"id": "support", "label": "Support"},
    {"id": "roles", "label": "Roles"},
    {"id": "engagement", "label": "Engagement"},
    {"id": "system", "label": "System"},
)

MODULE_IDS = {item["id"] for item in MODULES}
PRIVATE_MEDIA = re.compile(r"/guilds/\d+/media|storage_key|cls-media", re.I)
EMOJI = re.compile(r"<a?:([a-zA-Z0-9_]+):(\d+)>")


class TransferError(Exception):
    pass


def module_label(module_id: str) -> str:
    for item in MODULES:
        if item["id"] == module_id:
            return item["label"]
    return module_id


def ref(kind: str, source_id, name: str = "") -> dict | None:
    text = str(source_id or "")
    if not text.isdigit():
        return None
    return {"source_id": text, "name": name or "", "type": kind}


def snowflake(value) -> str | None:
    if isinstance(value, dict) and str(value.get("source_id") or "").isdigit():
        return str(value["source_id"])
    text = str(value or "")
    return text if text.isdigit() else None


def find_secret(value) -> str | None:
    if isinstance(value, dict):
        for key, item in value.items():
            if str(key).lower() in SECRET_KEYS:
                return str(key)
            found = find_secret(item)
            if found:
                return found
    elif isinstance(value, list):
        for item in value:
            found = find_secret(item)
            if found:
                return found
    return None


def strip_secrets(value):
    if isinstance(value, dict):
        return {key: strip_secrets(item) for key, item in value.items() if str(key).lower() not in SECRET_KEYS}
    if isinstance(value, list):
        return [strip_secrets(item) for item in value]
    return value


def scrub_private_media(value, *, cross_guild: bool, notes: list[str]):
    """Drop another guild's private media. External URLs stay."""
    if not cross_guild:
        return value
    if isinstance(value, dict):
        return {key: scrub_private_media(item, cross_guild=True, notes=notes) for key, item in value.items()}
    if isinstance(value, list):
        return [scrub_private_media(item, cross_guild=True, notes=notes) for item in value]
    if isinstance(value, str) and PRIVATE_MEDIA.search(value):
        if "Uploaded media needs replacement" not in notes:
            notes.append("Uploaded media needs replacement")
        return ""
    return value


def validate_bundle(data) -> dict:
    if not isinstance(data, dict):
        raise TransferError("This file is not a CLS config backup.")
    if find_secret(data):
        raise TransferError("This file contains a secret field and cannot be imported.")
    if data.get("format") != FORMAT:
        raise TransferError("This file is not a CLS config backup.")
    version = data.get("version")
    if not isinstance(version, int):
        raise TransferError("This file is not a CLS config backup.")
    if version > VERSION:
        raise TransferError(f"This file uses config format v{version}. This CLS OS build imports version {VERSION}.")
    if version < 1:
        raise TransferError("This file is not a CLS config backup.")
    upgraded = _upgrade(data)
    source = upgraded.get("source")
    if not isinstance(source, dict) or not str(source.get("guild_id") or "").isdigit():
        raise TransferError("The backup is missing its source server.")
    modules = upgraded.get("modules")
    if not isinstance(modules, dict):
        raise TransferError("The backup has no configuration modules.")
    for key, body in modules.items():
        if key not in MODULE_IDS:
            raise TransferError(f"Unknown module '{key}' is not part of this backup format.")
        if not isinstance(body, dict):
            raise TransferError(f"{module_label(key)} is not a valid configuration block.")
    return upgraded


def _upgrade(data: dict) -> dict:
    """Future v1 → v2 conversion starts here. v1 is returned unchanged."""
    if int(data["version"]) == 1:
        return data
    raise TransferError(f"This file uses config format v{data['version']}. This CLS OS build imports version {VERSION}.")


def empty_bundle(guild_id: int, guild_name: str) -> dict:
    return {
        "format": FORMAT,
        "version": VERSION,
        "exported_at": datetime.now(timezone.utc).isoformat(),
        "source": {"guild_id": str(guild_id), "guild_name": guild_name or ""},
        "modules": {},
    }


def selected(requested: list[str] | None) -> list[str]:
    if not requested:
        return [item["id"] for item in MODULES]
    chosen = []
    for module_id in requested:
        if module_id not in MODULE_IDS:
            raise TransferError(f"Unknown module '{module_id}'.")
        if module_id not in chosen:
            chosen.append(module_id)
    return chosen
