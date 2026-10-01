"""Snapshots of Discord users, roles, and channels.

Captured at event time so the log stays readable after a member leaves
or a role or channel is renamed or deleted. IDs are strings so they
survive JSON and JavaScript snowflake limits.
"""

from __future__ import annotations


def _text(value) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def snapshot_user(user) -> dict | None:
    if user is None:
        return None
    raw_id = getattr(user, "id", None)
    if raw_id is None:
        return None
    display = (
        _text(getattr(user, "display_name", None))
        or _text(getattr(user, "global_name", None))
        or _text(getattr(user, "name", None))
        or "Unknown"
    )
    avatar = getattr(user, "display_avatar", None)
    avatar_url = _text(getattr(avatar, "url", None)) if avatar is not None else None
    if avatar_url is None:
        avatar_url = _text(getattr(user, "avatar_url", None))
    return {
        "id": str(raw_id),
        "display_name": display,
        "username": _text(getattr(user, "name", None)),
        "avatar_url": avatar_url,
    }


def snapshot_role(role) -> dict | None:
    if role is None or getattr(role, "id", None) is None:
        return None
    color = getattr(role, "color", None)
    value = getattr(color, "value", None)
    hex_color = f"#{int(value):06x}" if isinstance(value, int) and value else None
    return {"id": str(role.id), "name": _text(getattr(role, "name", None)) or "role", "color": hex_color}


def snapshot_channel(channel) -> dict | None:
    if channel is None or getattr(channel, "id", None) is None:
        return None
    kind = getattr(channel, "type", None)
    type_name = _text(getattr(kind, "name", None)) or _text(kind) or "unknown"
    return {"id": str(channel.id), "name": _text(getattr(channel, "name", None)) or "channel", "type": type_name}


def display_name(entity: dict | None, fallback: str = "Someone") -> str:
    if not entity:
        return fallback
    return _text(entity.get("display_name")) or _text(entity.get("username")) or _text(entity.get("name")) or fallback


def user_mention(entity: dict | None) -> str:
    if not entity or not entity.get("id"):
        return display_name(entity, "Unknown")
    return f"<@{entity['id']}>"


def role_mention(entity: dict | None) -> str:
    if not entity:
        return "@role"
    if entity.get("id"):
        return f"<@&{entity['id']}>"
    name = entity.get("name") or "role"
    return name if str(name).startswith("@") else f"@{name}"


def channel_mention(entity: dict | None) -> str:
    if not entity:
        return "#channel"
    if entity.get("id"):
        return f"<#{entity['id']}>"
    name = entity.get("name") or "channel"
    return name if str(name).startswith("#") else f"#{name}"
