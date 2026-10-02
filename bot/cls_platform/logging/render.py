"""Discord embed payload for a logging event. Delivery stays in the cog."""

from __future__ import annotations

from cls_platform.logging.present import COLORS, present

STYLES = ("compact", "balanced", "detailed")
FOOTER_MODES = ("cls", "custom", "off")
PRIMARY_FIELDS = {"Before", "After", "Roles added", "Roles removed", "Content", "Name", "Granted", "Revoked"}
MODERATOR_FIELDS = {"Moderator", "Deleted by"}


def default_appearance() -> dict:
    return {
        "style": "balanced",
        "show_avatars": True,
        "show_moderator": True,
        "show_jump": True,
        "show_timestamp": True,
        "show_ids": False,
        "footer_mode": "cls",
        "footer_text": None,
        "colors": {},
        "event_styles": {},
        "ignore_scope": "messages",
    }


def _embed_author(event: dict, view: dict) -> dict | None:
    actor = view.get("actor") if isinstance(view.get("actor"), dict) else None
    target = view.get("target") if isinstance(view.get("target"), dict) else None
    kind = str(event.get("event_type") or "")
    if kind.startswith("member") or kind.startswith("voice"):
        author = target or actor
    else:
        author = actor or target
    return author if isinstance(author, dict) else None


def _hex_color(value: str | None, fallback: int) -> int:
    if isinstance(value, str) and len(value) == 7 and value.startswith("#"):
        try:
            return int(value[1:], 16)
        except ValueError:
            return fallback
    return fallback


def _footer(event: dict, view: dict, appearance: dict) -> str:
    mode = appearance.get("footer_mode") or "cls"
    if mode == "off":
        brand = ""
    elif mode == "custom":
        brand = str(appearance.get("footer_text") or "").strip()[:80]
    else:
        brand = "CLS"
    label = str(view.get("title") or "Logged")
    parts = [part for part in (brand, label) if part]
    if appearance.get("show_ids"):
        parts.extend(view.get("identifiers") or [])
    if (event.get("metadata") or {}).get("test"):
        parts.append("Test log")
    return " • ".join(parts)[:2048]


def _fields(view: dict, appearance: dict) -> list[dict]:
    style = appearance.get("style") or "balanced"
    if style not in STYLES:
        style = "balanced"
    chosen = []
    for field in view.get("fields") or []:
        name = str(field.get("name") or "Detail")
        if name == "Jump to message":
            continue
        if name in MODERATOR_FIELDS and (style == "compact" or not appearance.get("show_moderator", True)):
            continue
        if style == "compact":
            continue
        if style == "balanced" and name not in PRIMARY_FIELDS and name not in MODERATOR_FIELDS:
            continue
        value = field.get("discord") or field.get("dashboard") or "—"
        chosen.append({"name": name[:256], "value": str(value)[:1024], "inline": bool(field.get("inline"))})
    return chosen


def render_discord(event: dict, appearance: dict | None = None) -> dict:
    settings = {**default_appearance(), **(appearance or {})}
    view = event.get("presentation") or present(event)
    author = _embed_author(event, view)
    kind = str(event.get("event_type") or "")
    title = str(view.get("title") or "Logged")
    if kind == "message_edit":
        title = "✏️ Message Edited"
    summary = str(view.get("summary") or title)
    if settings["style"] == "compact" and view.get("change_line"):
        summary = f"{summary}\n{view['change_line']}"
    icon = None
    if settings.get("show_avatars", True) and isinstance(author, dict):
        icon = author.get("avatar_url")
    name = None
    if isinstance(author, dict):
        name = author.get("display_name") or author.get("name")
    category = str(event.get("category") or "")
    fallback = int(view.get("color") or COLORS.get(category, 0x6B7280))
    style_row = (settings.get("event_styles") or {}).get(kind) or {}
    if isinstance(style_row, dict) and not style_row.get("use_default", True):
        if style_row.get("title"):
            title = str(style_row["title"])
        if style_row.get("color"):
            fallback = _hex_color(str(style_row["color"]), fallback)
            override_color = None
        else:
            override_color = (settings.get("colors") or {}).get(category)
    else:
        override_color = (settings.get("colors") or {}).get(category)
    override = override_color
    jump = (event.get("metadata") or {}).get("jump_url") if settings.get("show_jump", True) else None
    fields = _fields(view, settings)
    if not fields and settings["style"] != "compact":
        fields = [{"name": "Detail", "value": summary[:1024], "inline": False}]
    return {
        "title": title[:256],
        "description": summary[:4096],
        "color": _hex_color(override, fallback),
        "author_name": name,
        "author_icon": icon,
        "thumbnail": None,
        "fields": fields,
        "footer": _footer(event, view, settings),
        "timestamp": bool(settings.get("show_timestamp", True)),
        "jump_url": jump if isinstance(jump, str) and jump.startswith("https://") else None,
    }


def sample_event(category: str, *, actor: dict, channel: dict | None = None, event_type: str | None = None) -> dict:
    """A representative event used by Send test log. Not stored."""
    member = {
        "id": actor.get("id") or "0",
        "display_name": actor.get("display_name") or "Sample member",
        "username": actor.get("username") or "sample",
        "avatar_url": actor.get("avatar_url"),
    }
    vip = {"id": "1", "name": "VIP", "color": "#c4a15a"}
    muted = {"id": "2", "name": "Muted", "color": None}
    text = channel or {"id": "1", "name": "mod-log", "type": "text"}
    voice_a = {"id": "3", "name": "Lounge", "type": "voice"}
    voice_b = {"id": "4", "name": "Stage", "type": "voice"}
    common = {"metadata": {"entities": {"actor": member, "target": member, "channel": text}, "test": True, "sample_category": category}}
    if category == "message_events":
        event = {
            **common,
            "category": category,
            "event_type": "message_edit",
            "actor_id": member["id"],
            "target_id": "42",
            "channel_id": text.get("id"),
            "before": {"content": "welcome"},
            "after": {"content": "welcome everyone"},
            "metadata": {**common["metadata"], "jump_url": "https://discord.com/channels/@me"},
        }
    elif category == "join_leave_events":
        event = {**common, "category": category, "event_type": "member_join", "actor_id": member["id"], "target_id": member["id"], "metadata": {**common["metadata"], "member_count": 1}}
    elif category == "voice_events":
        event = {
            **common,
            "category": category,
            "event_type": "voice_move",
            "actor_id": member["id"],
            "target_id": member["id"],
            "before": {"channel": voice_a},
            "after": {"channel": voice_b},
        }
    elif category == "role_events":
        role = {"id": "9", "name": "VIP", "color": "#c4a15a"}
        event = {
            "category": category,
            "event_type": "role_update",
            "actor_id": member["id"],
            "target_id": role["id"],
            "before": {"name": "Member", "color": "#99aab5", "permissions": 0},
            "after": {"name": "VIP", "color": "#c4a15a", "permissions": (1 << 13) | (1 << 28)},
            "metadata": {"entities": {"actor": member, "target": role}, "test": True, "sample_category": category},
        }
    elif category == "channel_events":
        event = {
            **common,
            "category": category,
            "event_type": "channel_update",
            "channel_id": text.get("id"),
            "before": {"name": "general", "topic": "hello", "slowmode": 0, "overwrites": []},
            "after": {"name": text.get("name") or "mod-log", "topic": "staff notes", "slowmode": 10, "overwrites": []},
        }
    elif category == "guild_events":
        event = {
            **common,
            "category": category,
            "event_type": "guild_update",
            "before": {"name": "Old name", "verification_level": "low"},
            "after": {"name": "New name", "verification_level": "medium"},
        }
    elif category == "bot_actions":
        event = {**common, "category": category, "event_type": "logging_test"}
    else:
        event = {
            **common,
            "category": "member_moderation",
            "event_type": "member_roles",
            "actor_id": member["id"],
            "target_id": member["id"],
            "before": {"roles": [muted]},
            "after": {"roles": [vip]},
            "metadata": {**common["metadata"], "reason": "Test log"},
        }
    if event_type:
        event["event_type"] = event_type
    return event
