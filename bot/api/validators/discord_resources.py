"""Central Discord resource ownership validation for API mutations."""

from __future__ import annotations

import json
from typing import Any, Optional

from fastapi import HTTPException, Request


def _parse_snowflake(value: Any) -> Optional[int]:
    if value is None:
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, str) and value.isdigit():
        return int(value)
    return None


def _collect_resource_ids(obj: Any, found: dict[str, set[int]]) -> None:
    if isinstance(obj, dict):
        for key, val in obj.items():
            lk = key.lower()
            if lk in ("role_id", "staff_role_id", "autorole_id", "verified_role_id"):
                sid = _parse_snowflake(val)
                if sid:
                    found.setdefault("role", set()).add(sid)
            elif lk.endswith("_role_id") or lk.endswith("_role"):
                sid = _parse_snowflake(val)
                if sid:
                    found.setdefault("role", set()).add(sid)
            elif lk in ("channel_id", "log_channel_id", "category_id", "welcome_channel_id"):
                sid = _parse_snowflake(val)
                if sid:
                    found.setdefault("channel", set()).add(sid)
            elif lk.endswith("_channel_id") or lk == "channel":
                sid = _parse_snowflake(val)
                if sid:
                    found.setdefault("channel", set()).add(sid)
            elif lk == "roles" and isinstance(val, list):
                for item in val:
                    sid = _parse_snowflake(item)
                    if sid:
                        found.setdefault("role", set()).add(sid)
            else:
                _collect_resource_ids(val, found)
    elif isinstance(obj, list):
        for item in obj:
            _collect_resource_ids(item, found)


def validate_role_in_guild(bot, guild_id: int, role_id: int) -> None:
    guild = bot.get_guild(guild_id)
    if guild is None:
        raise HTTPException(status_code=404, detail="Guild not found")
    role = guild.get_role(role_id)
    if role is None:
        raise HTTPException(status_code=403, detail="Role does not belong to guild")


def validate_channel_in_guild(bot, guild_id: int, channel_id: int) -> None:
    guild = bot.get_guild(guild_id)
    if guild is None:
        raise HTTPException(status_code=404, detail="Guild not found")
    channel = guild.get_channel(channel_id)
    if channel is None:
        raise HTTPException(status_code=403, detail="Channel does not belong to guild")


async def validate_mutation_payload(request: Request, guild_id: int, bot) -> None:
    if request.method in ("GET", "HEAD", "OPTIONS"):
        return
    body = await request.body()
    if not body:
        return
    try:
        payload = json.loads(body)
    except (json.JSONDecodeError, UnicodeDecodeError):
        return
    if isinstance(payload, dict):
        body_gid = _parse_snowflake(payload.get("guild_id"))
        if body_gid is not None and body_gid != guild_id:
            raise HTTPException(status_code=403, detail="Guild ID mismatch")

    found: dict[str, set[int]] = {}
    _collect_resource_ids(payload, found)
    for role_id in found.get("role", set()):
        validate_role_in_guild(bot, guild_id, role_id)
    for channel_id in found.get("channel", set()):
        validate_channel_in_guild(bot, guild_id, channel_id)
