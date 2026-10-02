"""Private ticket channel permission map. IDs only, so tests do not need Discord."""

from __future__ import annotations


def access_overwrites(*, everyone_id: int, opener_id: int, staff_role_ids: list[int], bot_id: int, extra_user_ids: list[int] | None = None, deny_role_ids: list[int] | None = None) -> dict[int, dict]:
    """Who can see a ticket. @everyone is denied. Opener, staff, extras, and the bot are allowed."""
    overwrites: dict[int, dict] = {
        int(everyone_id): {"view": False, "send": False, "history": False, "manage": False},
        int(opener_id): {"view": True, "send": True, "history": True, "manage": False, "attach": True},
        int(bot_id): {"view": True, "send": True, "history": True, "manage": True, "attach": True},
    }
    for role_id in staff_role_ids:
        overwrites[int(role_id)] = {"view": True, "send": True, "history": True, "manage": False, "attach": True}
    for user_id in extra_user_ids or []:
        if int(user_id) in {int(opener_id), int(bot_id)}:
            continue
        overwrites[int(user_id)] = {"view": True, "send": True, "history": True, "manage": False, "attach": True}
    denied = {"view": False, "send": False, "history": False, "manage": False, "attach": False}
    for role_id in deny_role_ids or []:
        role_id = int(role_id)
        current = overwrites.get(role_id)
        if current and current.get("view"):
            continue
        overwrites[role_id] = denied
    return overwrites
