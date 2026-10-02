"""Role-menu decisions that do not need Discord. The cog applies the result."""

from __future__ import annotations

import re

_CUSTOM = re.compile(r"^<a?:([^:>]+):(\d+)>$")
MODES = {"toggle", "add", "remove", "unique"}
TYPES = {"reaction", "button", "select"}
BUTTON_STYLES = {"pair", "toggle"}
DISCORD_BUTTON_CAP = 25


def emoji_token(value: str) -> str:
    return (value or "").strip()[:80]


def emoji_identity(value: str) -> str:
    token = emoji_token(value)
    match = _CUSTOM.fullmatch(token)
    if match:
        return f"{match.group(1)}:{match.group(2)}"
    return token


def same_emoji(stored: str, name: str, emoji_id: int | None = None) -> bool:
    token = emoji_identity(stored)
    if emoji_id:
        return token.endswith(f":{emoji_id}") or token == f"{name}:{emoji_id}"
    return token == (name or "")


def custom_emoji_id(value: str) -> str | None:
    match = _CUSTOM.fullmatch(emoji_token(value))
    return match.group(2) if match else None


def button_custom_id(menu_id: str, option_id: str, action: str | None = None) -> str:
    base = f"cls-rr:{menu_id}:{option_id}"
    if action in {"add", "remove"}:
        return f"{base}:{action}"
    return base


def button_option_limit(style: str, link_buttons: int = 0) -> int:
    """How many role options fit once message link buttons take their slots."""
    room = DISCORD_BUTTON_CAP - max(0, int(link_buttons or 0))
    per = 2 if style == "pair" else 1
    return max(0, room // per)


def button_faces(style: str, label: str) -> list[tuple[str | None, str]]:
    name = (label or "Role").strip() or "Role"
    if style == "pair":
        return [("add", f"Enable {name}"[:80]), ("remove", f"Disable {name}"[:80])]
    return [(None, f"Toggle {name}"[:80])]


def select_custom_id(menu_id: str) -> str:
    return f"cls-rr:{menu_id}"


def parse_custom_id(custom_id: str) -> tuple[str, str | None, str | None] | None:
    if not custom_id.startswith("cls-rr:"):
        return None
    parts = custom_id.split(":")
    if len(parts) == 2:
        return parts[1], None, None
    if len(parts) == 3:
        return parts[1], parts[2], None
    if len(parts) == 4 and parts[3] in {"add", "remove"}:
        return parts[1], parts[2], parts[3]
    return None


def role_block(*, exists: bool, managed: bool, bot_can_manage: bool, below_bot: bool) -> str | None:
    if not exists:
        return "That role is no longer on this server."
    if managed:
        return "That role is managed by an integration and cannot be assigned."
    if not bot_can_manage:
        return "CLS needs Manage Roles before it can assign that."
    if not below_bot:
        return "That role is above CLS, so it cannot be assigned."
    return None


def _result(add: set[int], remove: set[int], error: str | None = None, unchanged: bool = False) -> dict:
    return {"add": sorted(add), "remove": sorted(remove), "error": error, "unchanged": unchanged}


def plan_change(*, mode: str, intent: str, held: set[int], target: int, menu_roles: set[int], max_roles: int | None) -> dict:
    """intent is grant (reaction on), revoke (reaction off), or press (button/select)."""
    if mode not in MODES:
        return _result(set(), set(), "This menu mode is not available.")
    held_here = held.intersection(menu_roles)
    add: set[int] = set()
    remove: set[int] = set()

    if intent == "revoke":
        if mode in {"toggle", "unique"} and target in held:
            remove.add(target)
        return _result(add, remove)

    if mode == "remove":
        if target in held:
            remove.add(target)
        return _result(add, remove)

    if mode == "add":
        if target in held:
            return _result(set(), set(), unchanged=True)
        add.add(target)
    elif mode == "unique":
        remove.update(role_id for role_id in held_here if role_id != target)
        if target not in held:
            add.add(target)
    elif intent == "press" and target in held:
        remove.add(target)
    elif target not in held:
        add.add(target)

    if add and mode != "unique" and max_roles is not None and target not in held_here and len(held_here) >= int(max_roles):
        return _result(set(), set(), f"You already have the maximum of {max_roles} roles from this menu.")
    return _result(add, remove)
