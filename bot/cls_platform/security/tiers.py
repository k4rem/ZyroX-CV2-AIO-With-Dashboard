"""Permission tier map. Versioned; incidents record ``tier_map_version``.

View Audit Log is OBSERVABILITY. It is required for protection health and is
never an escalation or containment trigger.
"""

from __future__ import annotations

from collections.abc import Iterable

from cls_platform.security.constants import TIER_MAP_VERSION

TIER_RANK: dict[str, int] = {
    "OBSERVABILITY": 1,
    "ELEVATED": 2,
    "DESTRUCTIVE": 3,
    "CRITICAL_CONTROL": 4,
}

PERMISSION_TIERS: dict[str, str] = {
    "administrator": "CRITICAL_CONTROL",
    "manage_guild": "CRITICAL_CONTROL",
    "manage_roles": "CRITICAL_CONTROL",
    "manage_channels": "CRITICAL_CONTROL",
    "ban_members": "DESTRUCTIVE",
    "kick_members": "DESTRUCTIVE",
    "manage_webhooks": "DESTRUCTIVE",
    "moderate_members": "ELEVATED",
    "mention_everyone": "ELEVATED",
    "manage_threads": "ELEVATED",
    "manage_events": "ELEVATED",
    "manage_expressions": "ELEVATED",
    "view_audit_log": "OBSERVABILITY",
}

# Tiers that may feed containment-eligible rules. ELEVATED never does.
# OBSERVABILITY never does. A single action is containment-eligible only for
# CRITICAL_CONTROL added to @everyone (policy engine, OD-4).
CONTAINMENT_SIGNAL_TIERS = frozenset({"CRITICAL_CONTROL", "DESTRUCTIVE"})


def tier_for_permission(permission: str) -> str | None:
    return PERMISSION_TIERS.get(permission)


def highest_tier(permissions: Iterable[str]) -> str | None:
    best: str | None = None
    best_rank = 0
    for name in permissions:
        tier = PERMISSION_TIERS.get(name)
        if tier is None:
            continue
        rank = TIER_RANK[tier]
        if rank > best_rank:
            best = tier
            best_rank = rank
    return best


def tier_of_added_bits(added: Iterable[str]) -> str | None:
    """Highest tier among bits added. Removals are never escalation."""
    return highest_tier(added)


def is_containment_signal_tier(tier: str | None) -> bool:
    return tier in CONTAINMENT_SIGNAL_TIERS


def is_observability_permission(permission: str) -> bool:
    return PERMISSION_TIERS.get(permission) == "OBSERVABILITY"
