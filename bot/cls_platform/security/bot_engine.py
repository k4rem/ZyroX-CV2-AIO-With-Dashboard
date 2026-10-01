"""Bot policy evaluation. Adding a bot alerts only. Later destructive acts may would_contain."""

from __future__ import annotations

from datetime import datetime

from cls_platform.security.policy_engine import (
    Decision,
    PolicyObservation,
    Subject,
    TrustSnapshot,
    evaluate,
)


def evaluate_bot(
    subject: Subject,
    observations: list[PolicyObservation],
    trust_snapshot: TrustSnapshot,
    now: datetime,
    *,
    maintenance_active: bool = False,
) -> list[Decision]:
    if not subject.is_bot:
        raise ValueError("bot engine subjects must be bots")
    return evaluate(
        subject,
        observations,
        None,
        trust_snapshot,
        now,
        maintenance_active=maintenance_active,
    )
