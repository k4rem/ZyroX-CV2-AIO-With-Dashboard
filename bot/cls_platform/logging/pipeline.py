"""Which logging cog is allowed to deliver Discord messages."""

from __future__ import annotations

LEGACY_COG = "Logging"
ACTIVE_COG = "LoggingV2"

# The legacy cog remains in the tree for its command UI history, but it must
# not post. Logging V2 is the only delivery pipeline.
LEGACY_DELIVERY_DISABLED = True


def message_ignored(
    *,
    channel_id: int | None,
    author_id: int | None,
    author_role_ids: list[int] | None,
    ignores: dict,
) -> bool:
    """Message-event ignores: channel, user, or any of the author's roles."""
    channels = {int(item) for item in ignores.get("channels", [])}
    users = {int(item) for item in ignores.get("users", [])}
    roles = {int(item) for item in ignores.get("roles", [])}
    if channel_id is not None and int(channel_id) in channels:
        return True
    if author_id is not None and int(author_id) in users:
        return True
    return any(int(role_id) in roles for role_id in (author_role_ids or []))


def delivery_state(
    *,
    enabled: bool,
    channel_id: str | int | None,
    channel_found: bool,
    can_send: bool,
    checked: bool,
) -> str:
    if not enabled:
        return "disabled"
    if channel_id is None or channel_id == "":
        return "stored_only"
    if not checked:
        return "unchecked"
    if not channel_found:
        return "channel_unavailable"
    if not can_send:
        return "missing_permission"
    return "delivering"
