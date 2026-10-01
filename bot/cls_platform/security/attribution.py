"""Pure attribution rules. No Discord I/O and no newest-entry-wins."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta

from cls_platform.security.constants import (
    PROPOSED_SKEW_S,
    PROPOSED_T_ATTR_S,
    PROPOSED_T_LATE_S,
    AttributionState,
)
from cls_platform.security.taxonomy import action_spec

DISCORD_EPOCH_MS = 1_420_070_400_000


@dataclass(frozen=True)
class AuditCandidate:
    audit_entry_id: int
    discord_action: str
    action_class: str
    target_id: int | None
    actor_id: int | None
    entry_created_at: datetime
    change_digest: str = ""
    permission_diff: dict | None = None


def snowflake_from_time(moment: datetime) -> int:
    millis = int(moment.timestamp() * 1000) - DISCORD_EPOCH_MS
    if millis < 0:
        return 0
    return millis << 22


def correlation_key(guild_id: int, action_class: str, target_id: int | None, digest: str) -> str:
    return f"{int(guild_id)}:{action_class}:{int(target_id or 0)}:{digest}"


def is_late(*, received_at: datetime, entry_created_at: datetime | None, source: str) -> bool:
    if source == "reconciliation":
        return True
    if entry_created_at is None:
        return False
    return (received_at - entry_created_at).total_seconds() > PROPOSED_T_LATE_S


def within_match_window(entry_time: datetime, signal_time: datetime) -> bool:
    start = signal_time - timedelta(seconds=PROPOSED_SKEW_S)
    end = signal_time + timedelta(seconds=PROPOSED_T_ATTR_S)
    return start <= entry_time <= end


def signal_in_entry_window(signal_time: datetime, entry_time: datetime) -> bool:
    """§7.4: signal first_seen_at inside [entry_time − skew, entry_time + T_attr]."""
    start = entry_time - timedelta(seconds=PROPOSED_SKEW_S)
    end = entry_time + timedelta(seconds=PROPOSED_T_ATTR_S)
    return start <= signal_time <= end


def times_match(entry_time: datetime, signal_time: datetime) -> bool:
    """A link requires both the §7.4 signal window and the §8.2 entry window."""
    return within_match_window(entry_time, signal_time) and signal_in_entry_window(signal_time, entry_time)


def targets_comparable(action_class: str) -> bool:
    return action_spec(action_class).comparable_target


def confirmed_prerequisites(candidate: AuditCandidate) -> bool:
    if candidate.actor_id is None:
        return False
    if targets_comparable(candidate.action_class) and candidate.target_id is None:
        return False
    return True


def classify_targetless_candidates(candidates: list[AuditCandidate]) -> AttributionState:
    """Fallback path when Discord exposes no comparable target."""
    usable = [item for item in candidates if item.actor_id is not None]
    if len(usable) == 0:
        return AttributionState.UNATTRIBUTED
    if len(usable) == 1:
        return AttributionState.PROBABLE
    return AttributionState.AMBIGUOUS


def counts_for_containment(*, state: AttributionState, late: bool) -> bool:
    return state is AttributionState.CONFIRMED and not late
