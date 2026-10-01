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
    resolution: str,
    can_view: bool = False,
    can_send: bool = False,
    can_embed: bool = False,
) -> str:
    """resolution is unchecked, missing, unavailable, forbidden, or found."""
    if not enabled:
        return "stored_only"
    if channel_id is None or channel_id == "":
        return "missing_channel"
    if resolution == "unchecked":
        return "unchecked"
    if resolution == "unavailable":
        return "channel_unavailable"
    if resolution == "forbidden" or not can_view:
        return "bot_cannot_view"
    if not can_send:
        return "bot_cannot_send"
    if not can_embed:
        return "bot_cannot_embed"
    return "delivering"


def resolve_delivery(
    *,
    category_enabled: bool,
    category_channel_id: str | int | None,
    mode: str = "inherit",
    event_channel_id: str | int | None = None,
) -> dict:
    """How one event type uses the category default.

    inherit follows the category route.
    custom delivers only to the event channel.
    stored_only is kept for the dashboard and is not posted.
    disabled is not captured.
    """
    if mode == "disabled":
        return {"capture": False, "deliver": False, "channel_id": None, "mode": "disabled"}
    if mode == "stored_only":
        return {"capture": True, "deliver": False, "channel_id": None, "mode": "stored_only"}
    if mode == "custom":
        channel = event_channel_id or None
        return {"capture": True, "deliver": bool(channel), "channel_id": channel, "mode": "custom"}
    channel = category_channel_id if category_enabled else None
    return {"capture": True, "deliver": bool(channel), "channel_id": channel, "mode": "inherit"}
