"""Verification membership decisions. No Discord I/O."""

from __future__ import annotations

from datetime import datetime, timedelta


def plan_member(
    *,
    enabled: bool,
    user_id: int,
    owner_id: int | None,
    root_ids: set[int],
    joined_at: datetime | None,
    enabled_at: datetime | None,
    state: str | None,
    grace_until: datetime | None,
    grace_seconds: int,
    now: datetime,
) -> str:
    """Return exempt, disabled, verified, grace, start_grace, or assign_unverified."""
    if user_id in root_ids or (owner_id is not None and user_id == owner_id):
        return "exempt"
    if not enabled:
        return "disabled"
    if state == "verified":
        return "verified"
    if state == "exempt":
        return "exempt"
    if state == "grace":
        if grace_until is not None and now >= grace_until:
            return "assign_unverified"
        return "grace"
    if joined_at is not None and enabled_at is not None and joined_at < enabled_at and grace_seconds > 0:
        return "start_grace"
    return "assign_unverified"


def grace_deadline(now: datetime, grace_seconds: int) -> datetime:
    return now + timedelta(seconds=grace_seconds)


VERIFICATION_ENABLE_BLOCK = (
    "Verification cannot be enabled until a verification message is published."
)


def verification_message_reachable(*, published_message_id, channel_id) -> bool:
    """A channel choice is not a posted verify button. Joining members must be able to reach one."""
    return bool(published_message_id and channel_id)


def validate_enable(
    *,
    unverified_role_id: int | None,
    category_ids: list[int],
    bot_top: int,
    role_position: int | None,
    message_published: bool = False,
) -> str:
    if not unverified_role_id:
        return "role_missing"
    if role_position is None:
        return "role_missing"
    if not category_ids:
        return "category_missing"
    if role_position >= bot_top:
        return "hierarchy"
    if not message_published:
        return "message_unpublished"
    return "ok"
