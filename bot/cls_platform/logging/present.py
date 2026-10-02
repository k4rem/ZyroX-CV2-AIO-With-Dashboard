"""Turn a stored log event into language a server admin can read."""

from __future__ import annotations

from cls_platform.logging.entities import channel_mention, display_name, role_mention, user_mention
from cls_platform.logging.permissions import overwrite_diff, permission_diff

CATEGORY_LABELS = {
    "message_events": "Messages",
    "join_leave_events": "Members",
    "member_moderation": "Members",
    "voice_events": "Voice",
    "role_events": "Roles",
    "channel_events": "Channels",
    "guild_events": "Server",
    "bot_actions": "Bot",
}

TITLES = {
    "message_edit": "Message edited",
    "message_delete": "Message deleted",
    "message_bulk_delete": "Messages deleted",
    "member_join": "Member joined",
    "member_leave": "Member left",
    "member_kick": "Member kicked",
    "member_ban": "Member banned",
    "member_unban": "Member unbanned",
    "member_timeout": "Timeout added",
    "member_timeout_removed": "Timeout removed",
    "member_nickname": "Nickname changed",
    "member_roles": "Member roles updated",
    "role_create": "Role created",
    "role_update": "Role updated",
    "role_delete": "Role deleted",
    "channel_create": "Channel created",
    "channel_update": "Channel updated",
    "channel_delete": "Channel deleted",
    "voice_join": "Member joined voice",
    "voice_leave": "Left voice",
    "voice_move": "Moved voice channel",
    "guild_update": "Server settings updated",
    "logging_test": "Logging test",
    "ticket_opened": "Ticket opened",
    "ticket_claimed": "Ticket claimed",
    "ticket_unclaimed": "Ticket unclaimed",
    "ticket_transferred": "Ticket transferred",
    "ticket_closed": "Ticket closed",
    "ticket_reopened": "Ticket reopened",
    "ticket_deleted": "Ticket deleted",
    "ticket_auto_closed": "Ticket auto-closed",
}

COLORS = {
    "message_events": 0x4F6BED,
    "join_leave_events": 0x2F9E6B,
    "member_moderation": 0xC44B4B,
    "voice_events": 0x6B7280,
    "role_events": 0xC4A15A,
    "channel_events": 0x4F6BED,
    "guild_events": 0x6B7280,
    "bot_actions": 0x6B7280,
}

def _category_for(event_type: str) -> str:
    if event_type.startswith("message"):
        return "message_events"
    if event_type in {"member_join", "member_leave"}:
        return "join_leave_events"
    if event_type == "member_roles":
        return "role_events"
    if event_type.startswith("member"):
        return "member_moderation"
    if event_type.startswith("voice"):
        return "voice_events"
    if event_type.startswith("role"):
        return "role_events"
    if event_type.startswith("channel"):
        return "channel_events"
    if event_type.startswith("ticket_"):
        return "bot_actions"
    return "guild_events"


EVENT_GROUPS = (
    ("message_events", "Messages", ("message_edit", "message_delete", "message_bulk_delete")),
    ("join_leave_events", "Joins and leaves", ("member_join", "member_leave")),
    (
        "member_moderation",
        "Members",
        ("member_kick", "member_ban", "member_unban", "member_timeout", "member_timeout_removed", "member_nickname"),
    ),
    ("role_events", "Roles", ("member_roles", "role_create", "role_update", "role_delete")),
    ("channel_events", "Channels", ("channel_create", "channel_update", "channel_delete")),
    ("voice_events", "Voice", ("voice_join", "voice_leave", "voice_move")),
    ("guild_events", "Server", ("guild_update",)),
    (
        "bot_actions",
        "Bot actions",
        (
            "logging_test",
            "ticket_opened",
            "ticket_claimed",
            "ticket_unclaimed",
            "ticket_transferred",
            "ticket_closed",
            "ticket_reopened",
            "ticket_deleted",
            "ticket_auto_closed",
        ),
    ),
)


def category_for_event(event_type: str) -> str:
    for category, _label, events in EVENT_GROUPS:
        if event_type in events:
            return category
    return _category_for(event_type)


def catalog() -> list[dict]:
    return [
        {"id": key, "label": label, "category": _category_for(key)}
        for key, label in TITLES.items()
        if key != "logging_test"
    ]


def groups() -> list[dict]:
    return [
        {
            "category": category,
            "label": label,
            "events": [{"id": event_id, "label": TITLES[event_id]} for event_id in events],
        }
        for category, label, events in EVENT_GROUPS
    ]


def _clip(value, limit: int = 1000) -> str:
    text = "" if value is None else str(value)
    text = text.replace("```", "ʼʼʼ").strip()
    if not text:
        return "—"
    if len(text) <= limit:
        return text
    return text[: limit - 1] + "…"


def _fence(value) -> str:
    return f"```\n{_clip(value, 900)}\n```"


def _entities(event: dict) -> dict:
    raw = (event.get("metadata") or {}).get("entities") or {}
    return raw if isinstance(raw, dict) else {}


def _entity(event: dict, key: str) -> dict | None:
    value = _entities(event).get(key)
    return value if isinstance(value, dict) else None


def _roles(blob: dict | None) -> list[dict]:
    if not isinstance(blob, dict):
        return []
    rows = blob.get("roles")
    if isinstance(rows, list):
        return [row for row in rows if isinstance(row, dict)]
    return []


def _field(name: str, dashboard: str, discord: str | None = None, inline: bool = False) -> dict:
    shown = dashboard or "—"
    return {"name": name, "dashboard": shown, "discord": discord or shown, "inline": inline}


def _names(rows: list[dict], mention) -> tuple[str, str]:
    if not rows:
        return "—", "—"
    labels = [display_name(row, row.get("name") or "unknown") if "display_name" in row or "username" in row else (row.get("name") or "unknown") for row in rows]
    # roles use name
    pretty = ", ".join(row.get("name") or display_name(row, "unknown") for row in rows)
    linked = ", ".join(mention(row) for row in rows)
    return pretty, linked


def _identifiers(event: dict) -> list[str]:
    entities = _entities(event)
    target = entities.get("target") if isinstance(entities.get("target"), dict) else None
    actor = entities.get("actor") if isinstance(entities.get("actor"), dict) else None
    channel = entities.get("channel") if isinstance(entities.get("channel"), dict) else None
    kind = str(event.get("event_type") or "")
    parts: list[str] = []
    if kind.startswith("message"):
        if actor and actor.get("id"):
            parts.append(f"User ID: {actor['id']}")
        if event.get("target_id"):
            parts.append(f"Message ID: {event['target_id']}")
    elif target and target.get("id") and kind in {"role_create", "role_update", "role_delete"}:
        parts.append(f"Role ID: {target['id']}")
    elif channel and channel.get("id") and kind.startswith("channel"):
        parts.append(f"Channel ID: {channel['id']}")
    elif target and target.get("id"):
        parts.append(f"User ID: {target['id']}")
    elif event.get("target_id"):
        parts.append(f"ID: {event['target_id']}")
    return parts


def _base(event: dict, title: str, summary: str, fields: list[dict], change_line: str = "") -> dict:
    category = event.get("category") or "guild_events"
    entities = _entities(event)
    actor = entities.get("actor") if isinstance(entities.get("actor"), dict) else None
    target = entities.get("target") if isinstance(entities.get("target"), dict) else None
    channel = entities.get("channel") if isinstance(entities.get("channel"), dict) else None
    metadata = event.get("metadata") or {}
    return {
        "title": title,
        "summary": summary,
        "change_line": change_line,
        "category_label": CATEGORY_LABELS.get(category, "Server"),
        "color": COLORS.get(category, 0x6B7280),
        "actor": actor,
        "target": target,
        "channel": channel,
        "fields": fields,
        "changes": [{"label": field["name"], "value": field["dashboard"]} for field in fields],
        "footer": "",
        "identifiers": _identifiers(event),
        "jump_url": metadata.get("jump_url"),
        "incident_id": metadata.get("incident_id"),
        "thumbnail": bool(actor and actor.get("avatar_url") and str(event.get("event_type", "")).startswith("member")),
    }


def _actor_target(event: dict) -> tuple[str, str]:
    actor = display_name(_entity(event, "actor"), "A moderator" if event.get("actor_id") else "Someone")
    target = display_name(_entity(event, "target"), "a member")
    return actor, target


def _moderator_fields(event: dict, fields: list[dict]) -> None:
    actor = _entity(event, "actor")
    target = _entity(event, "target")
    if not actor:
        return
    if target and actor.get("id") and actor.get("id") == target.get("id"):
        return
    fields.append(_field("Moderator", display_name(actor, "Moderator"), user_mention(actor), True))
    reason = (event.get("metadata") or {}).get("reason")
    if reason:
        fields.append(_field("Reason", _clip(reason, 500)))


def present_member_roles(event: dict) -> dict:
    before = {row.get("id"): row for row in _roles(event.get("before"))}
    after = {row.get("id"): row for row in _roles(event.get("after"))}
    added = [row for key, row in after.items() if key not in before]
    removed = [row for key, row in before.items() if key not in after]
    actor, target = _actor_target(event)
    summary = f"{actor} updated {target}'s roles" if event.get("actor_id") else f"{target}'s roles were updated"
    bits = []
    if added:
        bits.append("+ " + ", ".join(row.get("name") or "role" for row in added))
    if removed:
        bits.append("− " + ", ".join(row.get("name") or "role" for row in removed))
    fields = []
    if added:
        pretty, linked = _names(added, role_mention)
        fields.append(_field("Roles added", pretty, linked))
    if removed:
        pretty, linked = _names(removed, role_mention)
        fields.append(_field("Roles removed", pretty, linked))
    if not fields:
        fields.append(_field("Roles", "No named role change was captured"))
    _moderator_fields(event, fields)
    return _base(event, TITLES["member_roles"], summary, fields, " ".join(bits))


def present_message_edit(event: dict) -> dict:
    author = display_name(_entity(event, "actor"), "Someone")
    channel = _entity(event, "channel")
    channel_name = f"#{channel.get('name')}" if channel and channel.get("name") else "a channel"
    old = (event.get("before") or {}).get("content")
    new = (event.get("after") or {}).get("content")
    fields = [
        _field("Channel", channel_name, channel_mention(channel), True),
        _field("Before", _clip(old, 500), _fence(old)),
        _field("After", _clip(new, 500), _fence(new)),
    ]
    old_bit = _clip(old, 42)
    new_bit = _clip(new, 42)
    change = ""
    if old_bit != "—" or new_bit != "—":
        change = f"\"{'' if old_bit == '—' else old_bit}\" → \"{'' if new_bit == '—' else new_bit}\""
    return _base(event, TITLES["message_edit"], f"{author} edited a message in {channel_name}", fields, change)


def present_message_delete(event: dict) -> dict:
    author_entity = _entity(event, "target") or _entity(event, "author")
    author = display_name(author_entity, "Someone")
    channel = _entity(event, "channel")
    channel_name = f"#{channel.get('name')}" if channel and channel.get("name") else "a channel"
    content = (event.get("metadata") or {}).get("content")
    if content is None and isinstance(event.get("before"), dict):
        content = event["before"].get("content")
    fields = [_field("Channel", channel_name, channel_mention(channel), True)]
    if author_entity:
        fields.append(_field("Author", display_name(author_entity, "Unknown"), user_mention(author_entity), True))
    if content:
        fields.append(_field("Content", _clip(content, 500), _fence(content)))
    attachments = (event.get("metadata") or {}).get("attachments") or []
    if isinstance(attachments, list) and attachments:
        names = ", ".join(str(item.get("filename") or "file") for item in attachments if isinstance(item, dict))
        fields.append(_field("Attachments", names or "Files attached"))
    actor = _entity(event, "actor")
    if actor and (not author_entity or actor.get("id") != author_entity.get("id")):
        fields.append(_field("Deleted by", display_name(actor, "A moderator"), user_mention(actor), True))
    summary = f"{author}'s message was deleted in {channel_name}"
    if actor and (not author_entity or actor.get("id") != author_entity.get("id")):
        summary = f"{display_name(actor, 'A moderator')} deleted {author}'s message in {channel_name}"
    return _base(event, TITLES["message_delete"], summary, fields, _clip(content, 80) if content else "")


def present_bulk(event: dict) -> dict:
    channel = _entity(event, "channel")
    channel_name = f"#{channel.get('name')}" if channel and channel.get("name") else "a channel"
    count = (event.get("metadata") or {}).get("count") or (event.get("after") or {}).get("count") or 0
    fields = [
        _field("Channel", channel_name, channel_mention(channel), True),
        _field("Messages", str(count), inline=True),
    ]
    _moderator_fields(event, fields)
    return _base(event, TITLES["message_bulk_delete"], f"{count} messages deleted in {channel_name}", fields, f"{count} messages")


def present_join(event: dict) -> dict:
    target = display_name(_entity(event, "target") or _entity(event, "actor"), "A member")
    fields = [_field("Member", target, user_mention(_entity(event, "target") or _entity(event, "actor")), True)]
    created = (event.get("metadata") or {}).get("account_created")
    created_unix = (event.get("metadata") or {}).get("account_created_unix")
    if created or created_unix:
        discord_value = f"<t:{int(created_unix)}:D>" if created_unix else str(created)
        fields.append(_field("Account created", str(created or "—"), discord_value, True))
    count = (event.get("metadata") or {}).get("member_count")
    if count is not None:
        fields.append(_field("Member count", str(count), inline=True))
    return _base(event, TITLES["member_join"], f"{target} joined", fields, "")


def present_leave(event: dict) -> dict:
    target = display_name(_entity(event, "target"), "A member")
    fields = [_field("Member", target, user_mention(_entity(event, "target")), True)]
    roles = _roles(event.get("before"))
    if roles:
        pretty, linked = _names(roles, role_mention)
        fields.append(_field("Roles", pretty, linked))
    return _base(event, TITLES["member_leave"], f"{target} left", fields, "")


def present_moderation(event: dict, title: str, verb: str, past: str) -> dict:
    actor, target = _actor_target(event)
    fields = [_field("Member", target, user_mention(_entity(event, "target")), True)]
    _moderator_fields(event, fields)
    until = (event.get("after") or {}).get("until") or (event.get("before") or {}).get("until")
    if until:
        fields.append(_field("Until", str(until), inline=True))
    summary = f"{actor} {verb} {target}" if event.get("actor_id") else f"{target} {past}"
    return _base(event, title, summary, fields, "")


def present_nickname(event: dict) -> dict:
    target = display_name(_entity(event, "target"), "A member")
    before = (event.get("before") or {}).get("nickname") or "No nickname"
    after = (event.get("after") or {}).get("nickname") or "No nickname"
    fields = [
        _field("Member", target, user_mention(_entity(event, "target")), True),
        _field("Old", _clip(before, 200), inline=True),
        _field("New", _clip(after, 200), inline=True),
    ]
    _moderator_fields(event, fields)
    return _base(event, TITLES["member_nickname"], f"{target}'s nickname changed", fields, f"{_clip(before, 40)} → {_clip(after, 40)}")


def present_role_object(event: dict, title: str, summary: str) -> dict:
    role = _entity(event, "target")
    name = (role or {}).get("name") or (event.get("after") or event.get("before") or {}).get("name") or "a role"
    fields = [_field("Role", f"@{name}", role_mention(role) if role else f"@{name}", True)]
    color = (event.get("after") or event.get("before") or {}).get("color") or (role or {}).get("color")
    if color:
        fields.append(_field("Color", str(color), inline=True))
    _moderator_fields(event, fields)
    return _base(event, title, summary, fields, f"@{name}")


def present_role_update(event: dict) -> dict:
    before = event.get("before") or {}
    after = event.get("after") or {}
    role = _entity(event, "target")
    name = (after.get("name") or (role or {}).get("name") or "a role")
    fields = [_field("Role", f"@{name}", role_mention({"id": (role or {}).get("id"), "name": name}) if (role or {}).get("id") else f"@{name}", True)]
    bits = []
    if before.get("name") and after.get("name") and before.get("name") != after.get("name"):
        fields.append(_field("Name", f"{before['name']} → {after['name']}"))
        bits.append(f"name → {after['name']}")
    if before.get("color") != after.get("color") and (before.get("color") or after.get("color")):
        fields.append(_field("Color", f"{before.get('color') or 'none'} → {after.get('color') or 'none'}"))
        bits.append("color")
    diff = permission_diff(before.get("permissions"), after.get("permissions"))
    if diff["granted"]:
        fields.append(_field("Granted", ", ".join(diff["granted"])))
        bits.append("granted " + ", ".join(diff["granted"]))
    if diff["revoked"]:
        fields.append(_field("Revoked", ", ".join(diff["revoked"])))
        bits.append("revoked " + ", ".join(diff["revoked"]))
    _moderator_fields(event, fields)
    return _base(event, TITLES["role_update"], f"@{name} was updated", fields, " · ".join(bits))


def present_channel(event: dict, title: str, summary_verb: str) -> dict:
    channel = _entity(event, "channel") or _entity(event, "target")
    name = (channel or {}).get("name") or (event.get("after") or event.get("before") or {}).get("name") or "channel"
    fields = [_field("Channel", f"#{name}", channel_mention(channel), True)]
    kind = (channel or {}).get("type")
    if kind:
        fields.append(_field("Type", str(kind).replace("_", " "), inline=True))
    _moderator_fields(event, fields)
    return _base(event, title, f"#{name} was {summary_verb}", fields, f"#{name}")


def present_channel_update(event: dict) -> dict:
    before = event.get("before") or {}
    after = event.get("after") or {}
    channel = _entity(event, "channel")
    name = after.get("name") or (channel or {}).get("name") or "channel"
    fields = [_field("Channel", f"#{name}", channel_mention(channel), True)]
    bits = []
    if before.get("name") and after.get("name") and before.get("name") != after.get("name"):
        fields.append(_field("Name", f"#{before['name']} → #{after['name']}"))
        bits.append(f"#{before['name']} → #{after['name']}")
    if before.get("topic") != after.get("topic") and ("topic" in before or "topic" in after):
        fields.append(_field("Topic", f"{_clip(before.get('topic') or 'none', 180)} → {_clip(after.get('topic') or 'none', 180)}"))
        bits.append("topic")
    if before.get("slowmode") != after.get("slowmode") and ("slowmode" in before or "slowmode" in after):
        fields.append(_field("Slowmode", f"{before.get('slowmode') or 0}s → {after.get('slowmode') or 0}s"))
        bits.append("slowmode")
    for line in overwrite_diff(before.get("overwrites"), after.get("overwrites")):
        fields.append(
            {
                "name": line["name"],
                "dashboard": line["dashboard"],
                "discord": line["discord"],
                "discord_name": line["discord_name"],
                "inline": False,
            }
        )
        bits.append(line["dashboard"])
    _moderator_fields(event, fields)
    return _base(event, TITLES["channel_update"], f"#{name} was updated", fields, " · ".join(bits[:3]))


def present_voice(event: dict) -> dict:
    member = display_name(_entity(event, "actor") or _entity(event, "target"), "Someone")
    before = (event.get("before") or {}).get("channel") if isinstance(event.get("before"), dict) else None
    after = (event.get("after") or {}).get("channel") if isinstance(event.get("after"), dict) else None
    kind = event.get("event_type")
    fields = [_field("Member", member, user_mention(_entity(event, "actor")), True)]
    if kind == "voice_move":
        fields.append(_field("From", f"#{(before or {}).get('name', 'voice')}", channel_mention(before), True))
        fields.append(_field("To", f"#{(after or {}).get('name', 'voice')}", channel_mention(after), True))
        summary = f"{member} moved from #{(before or {}).get('name', 'voice')} to #{(after or {}).get('name', 'voice')}"
        change = f"#{(before or {}).get('name', 'voice')} → #{(after or {}).get('name', 'voice')}"
        title = TITLES["voice_move"]
    elif kind == "voice_join":
        fields.append(_field("Channel", f"#{(after or {}).get('name', 'voice')}", channel_mention(after), True))
        summary = f"{member} joined #{(after or {}).get('name', 'voice')}"
        change = f"#{(after or {}).get('name', 'voice')}"
        title = TITLES["voice_join"]
    else:
        fields.append(_field("Channel", f"#{(before or {}).get('name', 'voice')}", channel_mention(before), True))
        summary = f"{member} left #{(before or {}).get('name', 'voice')}"
        change = f"#{(before or {}).get('name', 'voice')}"
        title = TITLES["voice_leave"]
    return _base(event, title, summary, fields, change)


def present_guild(event: dict) -> dict:
    before = event.get("before") or {}
    after = event.get("after") or {}
    fields = []
    bits = []
    labels = {
        "name": "Name",
        "description": "Description",
        "verification_level": "Verification",
        "explicit_content_filter": "Content filter",
        "afk_timeout": "AFK timeout",
        "afk_channel": "AFK channel",
        "system_channel": "System channel",
    }
    keys = [key for key in labels if before.get(key) != after.get(key) and (key in before or key in after)]
    for key in keys:
        fields.append(_field(labels[key], f"{_clip(before.get(key) or 'none', 180)} → {_clip(after.get(key) or 'none', 180)}"))
        bits.append(labels[key].lower())
    if not fields:
        fields.append(_field("Changes", "Server settings were updated"))
    _moderator_fields(event, fields)
    return _base(event, TITLES["guild_update"], "Server settings were updated", fields, ", ".join(bits))


def present_test(event: dict) -> dict:
    label = CATEGORY_LABELS.get((event.get("metadata") or {}).get("sample_category") or event.get("category"), "Logging")
    fields = [
        _field("Category", label, inline=True),
        _field("Note", "This is a test log from CLS OS."),
    ]
    return _base(event, "Logging test", f"Test log for {label}", fields, "Test")


HANDLERS = {
    "message_edit": present_message_edit,
    "message_delete": present_message_delete,
    "message_bulk_delete": present_bulk,
    "member_join": present_join,
    "member_leave": present_leave,
    "member_kick": lambda event: present_moderation(event, TITLES["member_kick"], "kicked", "was kicked"),
    "member_ban": lambda event: present_moderation(event, TITLES["member_ban"], "banned", "was banned"),
    "member_unban": lambda event: present_moderation(event, TITLES["member_unban"], "unbanned", "was unbanned"),
    "member_timeout": lambda event: present_moderation(event, TITLES["member_timeout"], "timed out", "was timed out"),
    "member_timeout_removed": lambda event: present_moderation(event, TITLES["member_timeout_removed"], "removed a timeout from", "is no longer timed out"),
    "member_nickname": present_nickname,
    "member_roles": present_member_roles,
    "role_create": lambda event: present_role_object(event, TITLES["role_create"], f"@{( _entity(event, 'target') or {}).get('name', 'role')} was created"),
    "role_update": present_role_update,
    "role_delete": lambda event: present_role_object(event, TITLES["role_delete"], f"@{( _entity(event, 'target') or {}).get('name', 'role')} was deleted"),
    "channel_create": lambda event: present_channel(event, TITLES["channel_create"], "created"),
    "channel_update": present_channel_update,
    "channel_delete": lambda event: present_channel(event, TITLES["channel_delete"], "deleted"),
    "voice_join": present_voice,
    "voice_leave": present_voice,
    "voice_move": present_voice,
    "guild_update": present_guild,
    "logging_test": present_test,
}


def present(event: dict) -> dict:
    kind = str(event.get("event_type") or "")
    if kind.startswith("automod."):
        sentence = str((event.get("metadata") or {}).get("sentence") or "Automod event")
        return _base(event, "Automod", sentence, [])
    handler = HANDLERS.get(kind)
    if handler is None:
        title = kind.replace("_", " ").strip().capitalize() or "Server event"
        return _base(event, title, title, [])
    view = handler(event)
    # Primary lines never fall back to a bare snowflake.
    for key in ("summary", "change_line", "title"):
        text = str(view.get(key) or "")
        if event.get("actor_id") and text.strip() == str(event.get("actor_id")):
            view[key] = view["title"]
        if event.get("target_id") and text.strip() == str(event.get("target_id")):
            view[key] = view["title"]
    return view
