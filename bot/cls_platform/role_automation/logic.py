"""Role automation decisions. The cog applies them and talks to Discord."""

from __future__ import annotations

TRIGGERS = {"join", "screening", "role_add", "role_remove"}
ACTIONS = {"add", "remove"}
KINDS = {"human", "bot", "has_role", "lacks_role", "account_age"}
MAX_DEPTH = 3


def delay_seconds(value: int | None) -> int:
    seconds = int(value or 0)
    if seconds < 0 or seconds > 60 * 60 * 24 * 7:
        raise ValueError("delay")
    return seconds


def conditions_match(*, is_bot: bool, role_ids: set[int], account_age_seconds: int, conditions: list[dict]) -> bool:
    """Every condition must match. An empty list matches everyone."""
    for condition in conditions or []:
        kind = condition.get("kind")
        if kind == "human" and is_bot:
            return False
        if kind == "bot" and not is_bot:
            return False
        role_id = int(condition["role_id"]) if str(condition.get("role_id") or "").isdigit() else None
        if kind == "has_role" and role_id not in role_ids:
            return False
        if kind == "lacks_role" and role_id in role_ids:
            return False
        if kind == "account_age":
            unit = 3600 if condition.get("unit") == "hours" else 86400
            needed = int(condition.get("amount") or 0) * unit
            age = int(account_age_seconds)
            op = condition.get("op") or "gte"
            if op == "gt" and not age > needed:
                return False
            if op != "gt" and not age >= needed:
                return False
    return True


def allow_fire(chain: list[str], rule_id: str) -> str | None:
    """Return a reason when this rule must not run inside the current chain."""
    if rule_id in chain:
        return "This rule already ran for this member in the current chain."
    if len(chain) >= MAX_DEPTH:
        return "Role automation stopped at 3 steps so it cannot loop."
    return None


def should_assign_now(*, pending: bool, screening: str) -> bool:
    if screening == "screening" and pending:
        return False
    return True
