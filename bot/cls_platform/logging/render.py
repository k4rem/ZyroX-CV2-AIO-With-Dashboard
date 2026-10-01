"""Discord embed payload for a logging event. Delivery stays in the cog."""

from __future__ import annotations

from cls_platform.logging.present import present


def _embed_author(event: dict, view: dict) -> dict | None:
    actor = view.get("actor") if isinstance(view.get("actor"), dict) else None
    target = view.get("target") if isinstance(view.get("target"), dict) else None
    kind = str(event.get("event_type") or "")
    # Member and voice logs are about the member. The moderator stays a field.
    if kind.startswith("member") or kind.startswith("voice"):
        author = target or actor
    else:
        author = actor or target
    return author if isinstance(author, dict) else None


def render_discord(event: dict) -> dict:
    view = event.get("presentation") or present(event)
    author = _embed_author(event, view)
    fields = []
    for field in view.get("fields") or []:
        value = field.get("discord") or field.get("dashboard") or "—"
        name = field.get("name") or "Detail"
        if field.get("discord_name"):
            name = field["discord_name"]
        fields.append({"name": str(name)[:256], "value": str(value)[:1024], "inline": bool(field.get("inline"))})
    if not fields:
        fields.append({"name": "Detail", "value": view.get("summary") or view.get("title") or "Logged", "inline": False})
    icon = None
    if isinstance(author, dict):
        icon = author.get("avatar_url")
    return {
        "title": str(view.get("title") or "Server event")[:256],
        "color": int(view.get("color") or 0x6B7280),
        "author_name": (author or {}).get("display_name") if isinstance(author, dict) else None,
        "author_icon": icon,
        "thumbnail": icon if view.get("thumbnail") else None,
        "fields": fields,
        "footer": str(view.get("footer") or "")[:2048],
    }


def sample_event(category: str, *, actor: dict, channel: dict | None = None) -> dict:
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
        return {
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
    if category == "join_leave_events":
        return {**common, "category": category, "event_type": "member_join", "actor_id": member["id"], "target_id": member["id"], "metadata": {**common["metadata"], "member_count": 1}}
    if category == "voice_events":
        return {
            **common,
            "category": category,
            "event_type": "voice_move",
            "actor_id": member["id"],
            "target_id": member["id"],
            "before": {"channel": voice_a},
            "after": {"channel": voice_b},
        }
    if category == "role_events":
        role = {"id": "9", "name": "VIP", "color": "#c4a15a"}
        return {
            "category": category,
            "event_type": "role_update",
            "actor_id": member["id"],
            "target_id": role["id"],
            "before": {"name": "Member", "color": "#99aab5", "permissions": 0},
            "after": {"name": "VIP", "color": "#c4a15a", "permissions": (1 << 13) | (1 << 28)},
            "metadata": {"entities": {"actor": member, "target": role}, "test": True, "sample_category": category},
        }
    if category == "channel_events":
        return {
            **common,
            "category": category,
            "event_type": "channel_update",
            "channel_id": text.get("id"),
            "before": {"name": "general", "topic": "hello", "slowmode": 0, "overwrites": []},
            "after": {"name": text.get("name") or "mod-log", "topic": "staff notes", "slowmode": 10, "overwrites": []},
        }
    if category == "guild_events":
        return {
            **common,
            "category": category,
            "event_type": "guild_update",
            "before": {"name": "Old name", "verification_level": "low"},
            "after": {"name": "New name", "verification_level": "medium"},
        }
    if category == "bot_actions":
        return {**common, "category": category, "event_type": "logging_test"}
    return {
        **common,
        "category": "member_moderation",
        "event_type": "member_roles",
        "actor_id": member["id"],
        "target_id": member["id"],
        "before": {"roles": [muted]},
        "after": {"roles": [vip]},
        "metadata": {**common["metadata"], "reason": "Test log"},
    }
