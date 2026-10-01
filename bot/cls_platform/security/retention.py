"""Retention purge. Active quarantines are never deleted."""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy import delete, select, text

from cls_platform.database import session_scope
from cls_platform.security.constants import (
    PROPOSED_GATEWAY_RETENTION_S,
    RETENTION_DELIVERED_OUTBOX_S,
    RETENTION_INCIDENT_HISTORY_S,
    RETENTION_UNLINKED_OBSERVATIONS_S,
)
from cls_platform.security.models import (
    SecurityAlertOutbox,
    SecurityGatewaySignal,
    SecurityIncident,
    SecurityIncidentEvent,
    SecurityObservation,
    SecurityQuarantine,
    SecurityResponseAction,
)

_OPEN_QUARANTINE = ("APPLYING", "ACTIVE", "PARTIAL_QUARANTINE")


def uuid_nil() -> uuid.UUID:
    return uuid.UUID(int=0)


async def purge_expired(now: datetime | None = None) -> dict[str, int]:
    moment = now or datetime.now(timezone.utc)
    counts = {"signals": 0, "observations": 0, "outbox": 0, "incidents": 0}
    async with session_scope() as session:
        signals = await session.execute(
            delete(SecurityGatewaySignal).where(
                SecurityGatewaySignal.first_seen_at < moment - timedelta(seconds=PROPOSED_GATEWAY_RETENTION_S)
            )
        )
        counts["signals"] = signals.rowcount or 0
        observations = await session.execute(
            delete(SecurityObservation).where(
                SecurityObservation.incident_id.is_(None),
                SecurityObservation.received_at < moment - timedelta(seconds=RETENTION_UNLINKED_OBSERVATIONS_S),
            )
        )
        counts["observations"] = observations.rowcount or 0
        outbox = await session.execute(
            delete(SecurityAlertOutbox).where(
                SecurityAlertOutbox.status == "DELIVERED",
                SecurityAlertOutbox.delivered_at.is_not(None),
                SecurityAlertOutbox.delivered_at < moment - timedelta(seconds=RETENTION_DELIVERED_OUTBOX_S),
            )
        )
        counts["outbox"] = outbox.rowcount or 0
        protected = (
            await session.execute(
                select(SecurityQuarantine.incident_id).where(
                    SecurityQuarantine.status.in_(_OPEN_QUARANTINE),
                    SecurityQuarantine.incident_id.is_not(None),
                )
            )
        ).scalars().all()
        old_ids = (
            await session.execute(
                select(SecurityIncident.id).where(
                    SecurityIncident.status == "CLOSED",
                    SecurityIncident.closed_at.is_not(None),
                    SecurityIncident.closed_at < moment - timedelta(seconds=RETENTION_INCIDENT_HISTORY_S),
                    SecurityIncident.id.notin_(protected or [uuid_nil()]),
                )
            )
        ).scalars().all()
        if old_ids:
            await session.execute(text("SELECT set_config('app.allow_security_purge', 'on', true)"))
            await session.execute(
                delete(SecurityObservation).where(SecurityObservation.incident_id.in_(old_ids))
            )
            await session.execute(
                delete(SecurityIncidentEvent).where(SecurityIncidentEvent.incident_id.in_(old_ids))
            )
            await session.execute(
                delete(SecurityResponseAction).where(SecurityResponseAction.incident_id.in_(old_ids))
            )
            await session.execute(
                delete(SecurityQuarantine).where(
                    SecurityQuarantine.incident_id.in_(old_ids),
                    SecurityQuarantine.status.notin_(_OPEN_QUARANTINE),
                )
            )
            removed = await session.execute(delete(SecurityIncident).where(SecurityIncident.id.in_(old_ids)))
            counts["incidents"] = removed.rowcount or 0
    return counts
