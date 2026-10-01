"""Permission diffs from Discord before/after state. Action name alone is not a tier."""

from __future__ import annotations

from cls_platform.security.tiers import highest_tier, tier_of_added_bits


def permission_names(permissions) -> set[str]:
    if permissions is None:
        return set()
    try:
        return {name for name, value in permissions if value}
    except TypeError:
        return set()


def diff_permissions(before, after) -> dict | None:
    before_perms = getattr(before, "permissions", None)
    after_perms = getattr(after, "permissions", None)
    before_pos = getattr(before, "position", None)
    after_pos = getattr(after, "position", None)
    if before_perms is None and after_perms is None and before_pos is None and after_pos is None:
        return None
    added = permission_names(after_perms) - permission_names(before_perms)
    removed = permission_names(before_perms) - permission_names(after_perms)
    position_delta = 0
    if before_pos is not None and after_pos is not None:
        position_delta = int(after_pos) - int(before_pos)
    if not added and not removed and position_delta == 0:
        return None
    return {
        "added": sorted(added),
        "removed": sorted(removed),
        "position_delta": position_delta,
    }


def classify_role_change(
    *,
    guild_id: int,
    role_id: int,
    managed: bool,
    before,
    after,
    cls_role_ids: set[int],
) -> dict | None:
    diff = diff_permissions(before, after)
    if diff is None:
        return None
    tier = tier_of_added_bits(diff["added"])
    impaired = int(role_id) in cls_role_ids and (bool(diff["removed"]) or diff["position_delta"] < 0)
    everyone = int(role_id) == int(guild_id)
    if impaired:
        return {
            "action_class": "cls.impairment",
            "permission_diff": diff,
            "permission_tier": tier,
            "everyone_grant": False,
        }
    if managed and tier:
        return {
            "action_class": "bot.privilege_change",
            "permission_diff": diff,
            "permission_tier": tier,
            "everyone_grant": False,
        }
    if tier is None:
        return None
    return {
        "action_class": "role.permission_escalation",
        "permission_diff": diff,
        "permission_tier": tier,
        "everyone_grant": everyone and tier == "CRITICAL_CONTROL",
    }


def classify_member_grant(
    *,
    target_is_bot: bool,
    target_is_cls: bool,
    added_permissions: set[str],
    removed: bool,
) -> dict | None:
    if target_is_cls and removed:
        return {
            "action_class": "cls.impairment",
            "permission_diff": {"added": [], "removed": sorted(added_permissions), "position_delta": 0},
            "permission_tier": None,
            "everyone_grant": False,
        }
    tier = highest_tier(added_permissions)
    if tier is None:
        return None
    action = "bot.privilege_change" if target_is_bot else "member.privileged_role_grant"
    return {
        "action_class": action,
        "permission_diff": {"added": sorted(added_permissions), "removed": [], "position_delta": 0},
        "permission_tier": tier,
        "everyone_grant": False,
    }
