"""Incident correlation. Closing an incident ends attachment immediately."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from cls_platform.database import session_scope
from cls_platform.security.config import ensure_guild_config
from cls_platform.security.constants import IncidentClosure, IncidentStatus
from cls_platform.security.feed import guild_lock
from cls_platform.security.models import SecurityIncident, SecurityIncidentEvent, SecurityObservation
from cls_platform.services.audit import _redact
from cls_platform.services.grants import user_has_capability
from cls_platform.discord_types import snowflake_to_str

_SEVERITY_RANK = {"L": 1, "M": 2, "H": 3, "C": 4}


def _now(moment: Optional[datetime]) -> datetime:
    current = moment or datetime.now(timezone.utc)
    if current.tzinfo is None:
        return current.replace(tzinfo=timezone.utc)
    return current


def _higher(left: str, right: str) -> str:
    return left if _SEVERITY_RANK.get(left, 0) >= _SEVERITY_RANK.get(right, 0) else right


def evidence_payload(observation: SecurityObservation) -> dict:
    """Minimal evidence. Snowflakes are strings. No message content and no secrets."""
    payload = {
        "what": observation.action_class,
        "when": {
            "entry_created_at": observation.entry_created_at.isoformat() if observation.entry_created_at else None,
            "received_at": observation.received_at.isoformat() if observation.received_at else None,
        },
        "where": {
            "guild_id": snowflake_to_str(observation.guild_id),
            "target_id": snowflake_to_str(observation.target_id),
        },
        "who": {
            "actor_id": snowflake_to_str(observation.actor_id),
            "attribution_state": observation.attribution_state,
        },
        "how": {
            "method": observation.attribution_method,
            "source": observation.source,
            "late": bool(observation.late),
            "corroborated": bool(observation.corroborated),
            "reason": observation.attribution_reason,
        },
        "why": {
            "rule_id": None,
            "explanation": None,
            "tier_map_version": None,
            "trust_snapshot": None,
            "would_contain": False,
            "late_excluded_from_containment": bool(observation.late),
        },
    }
    return _redact(payload)


def _subject_for(observation: SecurityObservation, engine: Optional[str]) -> tuple[Optional[int], str]:
    if observation.action_class == "bot.add" and observation.target_id is not None:
        return int(observation.target_id), "bot"
    if observation.attribution_state == "UNATTRIBUTED" or observation.actor_id is None:
        chosen = engine or ("bot" if observation.actor_is_bot else "human")
        return None, chosen
    if observation.actor_is_bot or observation.action_class.startswith("bot."):
        return int(observation.actor_id), engine or "bot"
    return int(observation.actor_id), engine or "human"


async def attach_observation(
    observation_id: uuid.UUID,
    *,
    now: Optional[datetime] = None,
    engine: Optional[str] = None,
) -> Optional[uuid.UUID]:
    moment = _now(now)
    async with session_scope() as session:
        preview = (
            await session.execute(
                select(SecurityObservation).where(SecurityObservation.id == observation_id)
            )
        ).scalar_one_or_none()
        if preview is None or preview.incident_id is not None:
            return preview.incident_id if preview else None
        guild_id = int(preview.guild_id)
    async with guild_lock(guild_id):
        async with session_scope() as session:
            observation = (
                await session.execute(
                    select(SecurityObservation)
                    .where(SecurityObservation.id == observation_id)
                    .with_for_update()
                )
            ).scalar_one()
            if observation.incident_id is not None:
                return observation.incident_id
            subject_id, chosen_engine = _subject_for(observation, engine)
            config = await ensure_guild_config(guild_id)
            opened_payload = evidence_payload(observation)
            incident_id, opened = await _correlate(
                session,
                guild_id=guild_id,
                subject_id=subject_id,
                engine=chosen_engine,
                severity=observation.severity,
                moment=moment,
                inactivity_s=int(config.incident_inactivity_s),
                lifetime_s=int(config.incident_max_lifetime_s),
                payload=opened_payload,
            )
            observation.incident_id = incident_id
        if opened:
            from cls_platform.security.alerts import enqueue_alert

            await enqueue_alert(
                guild_id=guild_id,
                incident_id=incident_id,
                kind="open",
                payload=opened_payload,
                now=moment,
                coalesce=False,
            )
        return incident_id


async def _correlate(
    session,
    *,
    guild_id: int,
    subject_id: Optional[int],
    engine: str,
    severity: str,
    moment: datetime,
    inactivity_s: int,
    lifetime_s: int,
    payload: dict,
) -> tuple[uuid.UUID, bool]:
    current = (
        await session.execute(
            select(SecurityIncident)
            .where(
                SecurityIncident.guild_id == guild_id,
                SecurityIncident.subject_id == subject_id if subject_id is not None else SecurityIncident.subject_id.is_(None),
                SecurityIncident.engine == engine,
                SecurityIncident.status == IncidentStatus.ACTIVE.value,
            )
            .with_for_update()
        )
    ).scalar_one_or_none()
    previous_id = None
    if current is not None:
        inactive = (moment - current.last_activity_at).total_seconds() > inactivity_s
        expired = (moment - current.opened_at).total_seconds() > lifetime_s
        if not inactive and not expired:
            current.last_activity_at = moment
            current.severity = _higher(current.severity, severity)
            session.add(
                SecurityIncidentEvent(
                    incident_id=current.id,
                    guild_id=guild_id,
                    kind="observation",
                    payload=payload,
                )
            )
            return current.id, False
        current.status = IncidentStatus.CLOSED.value
        current.closure = (
            IncidentClosure.EXPIRED_LIFETIME.value if expired else IncidentClosure.EXPIRED_INACTIVE.value
        )
        current.closed_at = moment
        previous_id = current.id
        await session.flush()
    created = SecurityIncident(
        guild_id=guild_id,
        subject_id=subject_id,
        engine=engine,
        status=IncidentStatus.ACTIVE.value,
        severity=severity,
        opened_at=moment,
        last_activity_at=moment,
        previous_incident_id=previous_id,
        tier_map_version="2026-10-01",
        trust_snapshot={},
    )
    try:
        async with session.begin_nested():
            session.add(created)
            await session.flush()
    except IntegrityError:
        current = (
            await session.execute(
                select(SecurityIncident)
                .where(
                    SecurityIncident.guild_id == guild_id,
                    SecurityIncident.subject_id == subject_id
                    if subject_id is not None
                    else SecurityIncident.subject_id.is_(None),
                    SecurityIncident.engine == engine,
                    SecurityIncident.status == IncidentStatus.ACTIVE.value,
                )
                .with_for_update()
            )
        ).scalar_one()
        current.last_activity_at = moment
        current.severity = _higher(current.severity, severity)
        session.add(
            SecurityIncidentEvent(
                incident_id=current.id,
                guild_id=guild_id,
                kind="observation",
                payload=payload,
            )
        )
        return current.id, False
    session.add(
        SecurityIncidentEvent(
            incident_id=created.id,
            guild_id=guild_id,
            kind="observation",
            payload=payload,
        )
    )
    return created.id, True


async def close_incident(
    *,
    guild_id: int,
    incident_id: uuid.UUID,
    closure: str,
    actor_user_id: int,
    now: Optional[datetime] = None,
) -> None:
    if closure not in {IncidentClosure.RESOLVED.value, IncidentClosure.FALSE_POSITIVE.value}:
        raise ValueError("manual closure must be RESOLVED or FALSE_POSITIVE")
    if not await user_has_capability(guild_id, actor_user_id, "security.incidents.manage"):
        raise PermissionError("security.incidents.manage required")
    moment = _now(now)
    async with session_scope() as session:
        row = (
            await session.execute(
                select(SecurityIncident)
                .where(SecurityIncident.id == incident_id, SecurityIncident.guild_id == guild_id)
                .with_for_update()
            )
        ).scalar_one_or_none()
        if row is None:
            return
        row.status = IncidentStatus.CLOSED.value
        row.closure = closure
        row.closed_at = moment
        row.closed_by = actor_user_id
        session.add(
            SecurityIncidentEvent(
                incident_id=row.id,
                guild_id=guild_id,
                kind="closure",
                payload=_redact({"closure": closure, "actor_id": snowflake_to_str(actor_user_id)}),
            )
        )


async def sweep_expired(now: Optional[datetime] = None) -> int:
    moment = _now(now)
    closed = 0
    async with session_scope() as session:
        rows = (
            await session.execute(
                select(SecurityIncident).where(SecurityIncident.status == IncidentStatus.ACTIVE.value)
            )
        ).scalars().all()
        for row in rows:
            config = await ensure_guild_config(int(row.guild_id))
            inactive = (moment - row.last_activity_at).total_seconds() > int(config.incident_inactivity_s)
            expired = (moment - row.opened_at).total_seconds() > int(config.incident_max_lifetime_s)
            if not inactive and not expired:
                continue
            row.status = IncidentStatus.CLOSED.value
            row.closure = (
                IncidentClosure.EXPIRED_LIFETIME.value if expired else IncidentClosure.EXPIRED_INACTIVE.value
            )
            row.closed_at = moment
            closed += 1
    return closed


async def list_incidents(guild_id: int) -> list[SecurityIncident]:
    async with session_scope() as session:
        rows = (
            await session.execute(
                select(SecurityIncident)
                .where(SecurityIncident.guild_id == guild_id)
                .order_by(SecurityIncident.opened_at.asc())
            )
        ).scalars().all()
        return list(rows)
