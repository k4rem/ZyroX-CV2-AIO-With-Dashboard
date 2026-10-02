"""Human-readable Discord permission diffs. Bits stay out of the primary UI."""

from __future__ import annotations

# Discord permission flags. Names match the client, not the raw bitfield.
PERMISSIONS: tuple[tuple[int, str], ...] = (
    (1 << 0, "Create Invite"),
    (1 << 1, "Kick Members"),
    (1 << 2, "Ban Members"),
    (1 << 3, "Administrator"),
    (1 << 4, "Manage Channels"),
    (1 << 5, "Manage Server"),
    (1 << 6, "Add Reactions"),
    (1 << 7, "View Audit Log"),
    (1 << 8, "Priority Speaker"),
    (1 << 9, "Video"),
    (1 << 10, "View Channel"),
    (1 << 11, "Send Messages"),
    (1 << 12, "Send Text-to-Speech"),
    (1 << 13, "Manage Messages"),
    (1 << 14, "Embed Links"),
    (1 << 15, "Attach Files"),
    (1 << 16, "Read Message History"),
    (1 << 17, "Mention Everyone"),
    (1 << 18, "Use External Emoji"),
    (1 << 19, "View Server Insights"),
    (1 << 20, "Connect"),
    (1 << 21, "Speak"),
    (1 << 22, "Mute Members"),
    (1 << 23, "Deafen Members"),
    (1 << 24, "Move Members"),
    (1 << 25, "Use Voice Activity"),
    (1 << 26, "Change Nickname"),
    (1 << 27, "Manage Nicknames"),
    (1 << 28, "Manage Roles"),
    (1 << 29, "Manage Webhooks"),
    (1 << 30, "Manage Expressions"),
    (1 << 31, "Use Application Commands"),
    (1 << 32, "Request to Speak"),
    (1 << 33, "Manage Events"),
    (1 << 34, "Manage Threads"),
    (1 << 35, "Create Public Threads"),
    (1 << 36, "Create Private Threads"),
    (1 << 37, "Use External Stickers"),
    (1 << 38, "Send Messages in Threads"),
    (1 << 39, "Use Activities"),
    (1 << 40, "Timeout Members"),
    (1 << 41, "View Creator Analytics"),
    (1 << 42, "Use Soundboard"),
    (1 << 43, "Create Expressions"),
    (1 << 45, "Use External Sounds"),
    (1 << 46, "Send Voice Messages"),
    (1 << 49, "Send Polls"),
)


def _bits(value) -> int:
    try:
        return int(value or 0)
    except (TypeError, ValueError):
        return 0


def permission_names(value) -> list[str]:
    bits = _bits(value)
    return [label for flag, label in PERMISSIONS if bits & flag]


def permission_diff(before, after) -> dict[str, list[str]]:
    before_bits = _bits(before)
    after_bits = _bits(after)
    granted = [label for flag, label in PERMISSIONS if (after_bits & flag) and not (before_bits & flag)]
    revoked = [label for flag, label in PERMISSIONS if (before_bits & flag) and not (after_bits & flag)]
    return {"granted": granted, "revoked": revoked}


def _by_id(rows: list | None) -> dict[str, dict]:
    found: dict[str, dict] = {}
    for row in rows or []:
        if isinstance(row, dict) and row.get("id"):
            found[str(row["id"])] = row
    return found


def _target_label(row: dict) -> str:
    name = row.get("name") or "someone"
    if row.get("kind") == "role":
        return name if str(name).startswith("@") else f"@{name}"
    return str(name)


def _target_mention(row: dict) -> str:
    if row.get("kind") == "role" and row.get("id"):
        return f"<@&{row['id']}>"
    if row.get("id"):
        return f"<@{row['id']}>"
    return _target_label(row)


def _stance(allow: int, deny: int, flag: int) -> str:
    if allow & flag:
        return "Allow"
    if deny & flag:
        return "Deny"
    return "Neutral"


def overwrite_diff(before: list | None, after: list | None) -> list[dict]:
    """Readable allow/deny changes for channel permission overwrites."""
    old = _by_id(before)
    new = _by_id(after)
    lines: list[dict] = []
    for target_id in list(dict.fromkeys([*old.keys(), *new.keys()])):
        previous = old.get(target_id, {})
        current = new.get(target_id, {})
        label = _target_label(current or previous)
        mention = _target_mention(current or previous)
        before_allow = _bits(previous.get("allow"))
        before_deny = _bits(previous.get("deny"))
        after_allow = _bits(current.get("allow"))
        after_deny = _bits(current.get("deny"))
        for flag, name in PERMISSIONS:
            previous_state = _stance(before_allow, before_deny, flag)
            current_state = _stance(after_allow, after_deny, flag)
            if previous_state == current_state:
                continue
            shown = f"{name}: {previous_state} → {current_state}"
            lines.append(_line(label, shown, mention, shown))
    return lines


def _line(label: str, dashboard: str, discord_label: str, discord_value: str) -> dict:
    return {
        "name": label,
        "dashboard": dashboard,
        "discord_name": discord_label,
        "discord": discord_value,
        "inline": False,
    }
