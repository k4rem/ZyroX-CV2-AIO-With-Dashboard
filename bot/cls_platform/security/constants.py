"""Phase 2A security constants.

ENFORCE is part of the approved mode vocabulary and is not operationally
available until containment exists (step 2A.6).
"""

from __future__ import annotations

from enum import Enum

# Structural gate. Step 2A.6 is the only step allowed to turn this on.
ENFORCE_OPERATIONALLY_AVAILABLE = False

TIER_MAP_VERSION = "2026-10-01"

# PROPOSED timing defaults. Production values wait for OBSERVE review (OD-13).
PROPOSED_GATEWAY_DEDUPE_S = 10
GATEWAY_DEDUPE_MAX_S = 120
PROPOSED_T_PUSH_S = 2
PROPOSED_T_ATTR_S = 30
PROPOSED_T_LATE_S = 30
PROPOSED_SKEW_S = 15
PROPOSED_FETCH_DELAYS_S = (2, 5, 12)
PROPOSED_INCIDENT_INACTIVITY_S = 900
INCIDENT_INACTIVITY_MIN_S = 300
INCIDENT_INACTIVITY_MAX_S = 3600
PROPOSED_INCIDENT_MAX_LIFETIME_S = 6 * 60 * 60
PROPOSED_GATEWAY_RETENTION_S = 24 * 60 * 60
PROPOSED_ALERT_COALESCE_S = 30
PROPOSED_ALERT_GUILD_CAP = 20
PROPOSED_ALERT_CAP_WINDOW_S = 10 * 60
MAINTENANCE_MAX_S = 60 * 60

RETENTION_UNLINKED_OBSERVATIONS_S = 30 * 24 * 60 * 60
RETENTION_DELIVERED_OUTBOX_S = 30 * 24 * 60 * 60
RETENTION_INCIDENT_HISTORY_S = 365 * 24 * 60 * 60

FETCH_LIMIT = 25
AUDIT_BUCKET_PER_S = 1
AUDIT_BUCKET_BURST = 3


class SecurityMode(str, Enum):
    OFF = "OFF"
    OBSERVE = "OBSERVE"
    ENFORCE = "ENFORCE"


class AttributionState(str, Enum):
    CONFIRMED = "CONFIRMED"
    PROBABLE = "PROBABLE"
    AMBIGUOUS = "AMBIGUOUS"
    UNATTRIBUTED = "UNATTRIBUTED"
    SELF = "SELF"
    CLS_PROXIED = "CLS_PROXIED"


class SignalState(str, Enum):
    PENDING = "PENDING"
    LINKED = "LINKED"
    SUPERSEDED = "SUPERSEDED"
    EXPIRED_UNATTRIBUTED = "EXPIRED_UNATTRIBUTED"


class IncidentStatus(str, Enum):
    ACTIVE = "ACTIVE"
    CLOSED = "CLOSED"


class IncidentClosure(str, Enum):
    EXPIRED_INACTIVE = "EXPIRED_INACTIVE"
    EXPIRED_LIFETIME = "EXPIRED_LIFETIME"
    RESOLVED = "RESOLVED"
    FALSE_POSITIVE = "FALSE_POSITIVE"


class ResponseOutcome(str, Enum):
    WOULD_CONTAIN = "WOULD_CONTAIN"
    ACTIVE = "ACTIVE"
    PARTIAL_QUARANTINE = "PARTIAL_QUARANTINE"
    UNCONTAINABLE_HIERARCHY = "UNCONTAINABLE_HIERARCHY"
    FAILED_PERMISSION = "FAILED_PERMISSION"
    FAILED_DISCORD = "FAILED_DISCORD"
    NOT_ATTEMPTED_POLICY = "NOT_ATTEMPTED_POLICY"
    SKIPPED_TRUSTED = "SKIPPED_TRUSTED"
    SKIPPED_MODE = "SKIPPED_MODE"
    RELEASED = "RELEASED"
    RELEASE_PARTIAL = "RELEASE_PARTIAL"
    RELEASE_FAILED = "RELEASE_FAILED"


# Outcomes that mean Discord membership or roles were changed. Not writable yet.
MUTATION_OUTCOMES = frozenset(
    {
        ResponseOutcome.ACTIVE.value,
        ResponseOutcome.PARTIAL_QUARANTINE.value,
        ResponseOutcome.RELEASED.value,
        ResponseOutcome.RELEASE_PARTIAL.value,
        ResponseOutcome.RELEASE_FAILED.value,
    }
)

RECORD_ONLY_OUTCOMES = frozenset(
    {
        ResponseOutcome.WOULD_CONTAIN.value,
        ResponseOutcome.NOT_ATTEMPTED_POLICY.value,
        ResponseOutcome.SKIPPED_TRUSTED.value,
        ResponseOutcome.SKIPPED_MODE.value,
        ResponseOutcome.UNCONTAINABLE_HIERARCHY.value,
        ResponseOutcome.FAILED_PERMISSION.value,
        ResponseOutcome.FAILED_DISCORD.value,
    }
)


class AlertStatus(str, Enum):
    PENDING = "PENDING"
    CLAIMED = "CLAIMED"
    DEGRADED = "DEGRADED"
    DELIVERED = "DELIVERED"
    FAILED = "FAILED"
    UNDELIVERABLE_NO_DESTINATION = "UNDELIVERABLE_NO_DESTINATION"
    COALESCED = "COALESCED"


class Engine(str, Enum):
    HUMAN = "human"
    BOT = "bot"
