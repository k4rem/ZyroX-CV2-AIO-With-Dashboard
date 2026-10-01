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
            referenced = set(
                (
                    await session.execute(
                        select(SecurityIncident.previous_incident_id).where(
                            SecurityIncident.previous_incident_id.in_(old_ids),
                            SecurityIncident.id.notin_(old_ids),
                        )
                    )
                ).scalars().all()
            )
            live_outbox = set(
                (
                    await session.execute(
                        select(SecurityAlertOutbox.incident_id).where(
                            SecurityAlertOutbox.incident_id.in_(old_ids),
                            SecurityAlertOutbox.status != "DELIVERED",
                        )
                    )
                ).scalars().all()
            )
            delete_ids = [item for item in old_ids if item not in referenced and item not in live_outbox]
            if not delete_ids:
                return counts
            await session.execute(text("SELECT set_config('app.allow_security_purge', 'on', true)"))
            obs_ids = (
                await session.execute(
                    select(SecurityObservation.id).where(SecurityObservation.incident_id.in_(delete_ids))
                )
            ).scalars().all()
            if obs_ids:
                await session.execute(
                    SecurityObservation.__table__.update()
                    .where(SecurityObservation.superseded_by_observation_id.in_(obs_ids))
                    .values(superseded_by_observation_id=None)
                )
                await session.execute(
                    SecurityGatewaySignal.__table__.update()
                    .where(SecurityGatewaySignal.linked_observation_id.in_(obs_ids))
                    .values(linked_observation_id=None)
                )
            await session.execute(
                SecurityIncident.__table__.update()
                .where(SecurityIncident.previous_incident_id.in_(delete_ids))
                .values(previous_incident_id=None)
            )
            await session.execute(
                delete(SecurityAlertOutbox).where(SecurityAlertOutbox.incident_id.in_(delete_ids))
            )
            await session.execute(
                delete(SecurityObservation).where(SecurityObservation.incident_id.in_(delete_ids))
            )
            await session.execute(
                delete(SecurityIncidentEvent).where(SecurityIncidentEvent.incident_id.in_(delete_ids))
            )
            await session.execute(
                delete(SecurityResponseAction).where(SecurityResponseAction.incident_id.in_(delete_ids))
            )
            await session.execute(
                delete(SecurityQuarantine).where(
                    SecurityQuarantine.incident_id.in_(delete_ids),
                    SecurityQuarantine.status.notin_(_OPEN_QUARANTINE),
                )
            )
            removed = await session.execute(delete(SecurityIncident).where(SecurityIncident.id.in_(delete_ids)))
            counts["incidents"] = removed.rowcount or 0
    return counts
