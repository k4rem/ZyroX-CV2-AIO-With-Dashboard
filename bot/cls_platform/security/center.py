"""Security Center reads Phase 2A rows. It does not enable ENFORCE."""

from __future__ import annotations

import re
import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy import BigInteger, Boolean, DateTime, String, func, select
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import Mapped, mapped_column

from cls_platform.database import session_scope
from cls_platform.discord_types import snowflake_to_str
from cls_platform.logging.store import list_events
from cls_platform.models import Base
from cls_platform.security.models import (
    SecurityIncident,
    SecurityIncidentEvent,
    SecurityObservation,
    SecurityResponseAction,
    SecurityTrustedActor,
)

_PHISH = re.compile(r"(discord[\-\.]?(gift|nitro)|free[\-\.]?nitro|discorcl|dlscord|disc0rd)", re.I)
PHISHING_ACTIONS = {"delete_only", "delete_timeout", "kick", "ban"}


class SecurityCenterSettings(Base):
    __tablename__ = "security_center_settings"

    guild_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    dashboard_locked: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    phishing_action: Mapped[str] = mapped_column(String(32), nullable=False, default="delete_timeout")
    trap_channel_ids: Mapped[list[int]] = mapped_column(ARRAY(BigInteger), nullable=False, default=list)
    honeypot_channel_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


def phishing_match(content: str) -> bool:
    return bool(_PHISH.search(content or ""))


def trap_action(*, author_is_bot: bool, webhook: bool, trusted: bool, mode: str, enforce_locked: bool) -> str:
    if webhook:
        return "record_webhook"
    if not author_is_bot or trusted:
        return "ignore"
    if mode == "ENFORCE" and not enforce_locked:
        return "ban"
    return "record"


async def get_settings(guild_id: int) -> dict:
    async with session_scope() as session:
        row = await session.get(SecurityCenterSettings, guild_id)
        if row is None:
            return {
                "dashboard_locked": False,
                "phishing_action": "delete_timeout",
                "trap_channel_ids": [],
                "honeypot_channel_id": None,
            }
        return {
            "dashboard_locked": bool(row.dashboard_locked),
            "phishing_action": row.phishing_action,
            "trap_channel_ids": [snowflake_to_str(item) for item in (row.trap_channel_ids or [])],
            "honeypot_channel_id": snowflake_to_str(row.honeypot_channel_id) if row.honeypot_channel_id else None,
        }


async def save_settings(
    *,
    guild_id: int,
    dashboard_locked: bool | None = None,
    phishing_action: str | None = None,
    trap_channel_ids: list[int] | None = None,
    honeypot_channel_id: int | None = None,
    honeypot_set: bool = False,
) -> dict:
    if phishing_action is not None and phishing_action not in PHISHING_ACTIONS:
        raise ValueError("invalid_phishing_action")
    async with session_scope() as session:
        row = await session.get(SecurityCenterSettings, guild_id)
        if row is None:
            row = SecurityCenterSettings(guild_id=guild_id, trap_channel_ids=[])
            session.add(row)
        if dashboard_locked is not None:
            row.dashboard_locked = dashboard_locked
        if phishing_action is not None:
            row.phishing_action = phishing_action
        if trap_channel_ids is not None:
            row.trap_channel_ids = trap_channel_ids
        if honeypot_set:
            row.honeypot_channel_id = honeypot_channel_id
        row.updated_at = datetime.now(timezone.utc)
    return await get_settings(guild_id)


async def dashboard_is_locked(guild_id: int) -> bool:
    settings = await get_settings(guild_id)
    return bool(settings["dashboard_locked"])


async def is_trusted(guild_id: int, subject_id: int) -> bool:
    from cls_platform.security.trust import active_trust

    return await active_trust(guild_id, subject_id) is not None


async def note_signal(
    *,
    guild_id: int,
    subject_id: int,
    engine: str,
    kind: str,
    detail: str,
    extra: dict | None = None,
) -> str:
    now = datetime.now(timezone.utc)
    created = False
    async with session_scope() as session:
        incident = (
            await session.execute(
                select(SecurityIncident).where(
                    SecurityIncident.guild_id == guild_id,
                    SecurityIncident.subject_id == subject_id,
                    SecurityIncident.engine == engine,
                    SecurityIncident.status == "ACTIVE",
                )
            )
        ).scalar_one_or_none()
        if incident is None:
            incident = SecurityIncident(
                guild_id=guild_id,
                subject_id=subject_id,
                engine=engine,
                status="ACTIVE",
                severity="H" if kind == "bot_trap" else "M",
                opened_at=now,
                last_activity_at=now,
                tier_map_version="center-v1",
            )
            session.add(incident)
            await session.flush()
            created = True
        else:
            incident.last_activity_at = now
        payload = {"detail": detail, "subject_id": snowflake_to_str(subject_id)}
        if extra:
            payload.update(extra)
        session.add(
            SecurityIncidentEvent(
                incident_id=incident.id,
                guild_id=guild_id,
                kind=kind,
                payload=payload,
            )
        )
        incident_id = str(incident.id)
    from cls_platform.logging.store import record_event
    from cls_platform.security.logbridge import security_event
    from cls_platform.security.product import detector_title

    outcome = (extra or {}).get("action_result", {}).get("outcome")
    if kind == "phishing":
        sentence = (
            "CLS deleted a phishing message."
            if outcome == "succeeded"
            else "CLS could not delete a phishing message."
        )
        await security_event(
            guild_id=guild_id,
            event_type="security.phishing_deleted",
            sentence=sentence,
            actor_id=subject_id,
            confidence="certain",
        )
    elif kind == "human_honeypot":
        await security_event(
            guild_id=guild_id,
            event_type="security.honeypot_triggered",
            sentence="Someone posted in the human honeypot.",
            actor_id=subject_id,
            confidence="certain",
        )
    if created:
        await security_event(
            guild_id=guild_id,
            event_type="security.incident_created",
            sentence=f"CLS opened an incident: {detector_title(kind)}.",
            actor_id=subject_id,
            confidence="certain",
        )

    await record_event(
        guild_id=guild_id,
        category="bot_actions" if engine == "bot" else "member_moderation",
        event_type=kind,
        actor_id=subject_id,
        actor_confidence="certain",
        target_id=subject_id,
        metadata={"detail": detail},
    )
    return incident_id


async def incident_timeline(guild_id: int, incident_id: str) -> dict:
    async with session_scope() as session:
        incident = await session.get(SecurityIncident, uuid.UUID(incident_id))
        if incident is None or incident.guild_id != guild_id:
            raise ValueError("missing")
        events = (
            await session.execute(
                select(SecurityIncidentEvent)
                .where(SecurityIncidentEvent.incident_id == incident.id)
                .order_by(SecurityIncidentEvent.created_at)
            )
        ).scalars().all()
        return {
            "id": str(incident.id),
            "status": incident.status,
            "engine": incident.engine,
            "severity": incident.severity,
            "subject_id": snowflake_to_str(incident.subject_id) if incident.subject_id else None,
            "closure": incident.closure,
            "events": [
                {"kind": row.kind, "payload": row.payload, "created_at": row.created_at.isoformat()}
                for row in events
            ],
        }


async def analytics(guild_id: int) -> dict:
    empty = {
        "total": 0,
        "by_severity": {},
        "by_engine": {},
        "by_action_class": {},
        "by_outcome": {},
        "series": [],
        "heatmap": None,
        "event_stream": [],
    }
    async with session_scope() as session:
        total = (
            await session.execute(
                select(func.count()).select_from(SecurityIncident).where(SecurityIncident.guild_id == guild_id)
            )
        ).scalar_one()
        if int(total) == 0:
            stream = await list_events(guild_id, limit=20)
            empty["event_stream"] = [
                row for row in stream["events"] if row["category"] in {"member_moderation", "bot_actions"}
            ]
            return empty
        severities = (
            await session.execute(
                select(SecurityIncident.severity, func.count())
                .where(SecurityIncident.guild_id == guild_id)
                .group_by(SecurityIncident.severity)
            )
        ).all()
        engines = (
            await session.execute(
                select(SecurityIncident.engine, func.count())
                .where(SecurityIncident.guild_id == guild_id)
                .group_by(SecurityIncident.engine)
            )
        ).all()
        classes = (
            await session.execute(
                select(SecurityObservation.action_class, func.count())
                .where(SecurityObservation.guild_id == guild_id)
                .group_by(SecurityObservation.action_class)
                .order_by(func.count().desc())
                .limit(8)
            )
        ).all()
        outcomes = (
            await session.execute(
                select(SecurityResponseAction.outcome, func.count())
                .where(SecurityResponseAction.guild_id == guild_id)
                .group_by(SecurityResponseAction.outcome)
            )
        ).all()
        day = func.date_trunc("day", SecurityIncident.opened_at)
        series = (
            await session.execute(
                select(day, func.count()).where(SecurityIncident.guild_id == guild_id).group_by(day).order_by(day)
            )
        ).all()
        span = (
            await session.execute(
                select(func.min(SecurityIncident.opened_at), func.max(SecurityIncident.opened_at)).where(
                    SecurityIncident.guild_id == guild_id
                )
            )
        ).one()
        heatmap = None
        if span[0] and span[1] and (span[1] - span[0]) >= timedelta(days=7):
            hour = func.extract("hour", SecurityIncident.opened_at)
            weekday = func.extract("dow", SecurityIncident.opened_at)
            cells = (
                await session.execute(
                    select(weekday, hour, func.count())
                    .where(SecurityIncident.guild_id == guild_id)
                    .group_by(weekday, hour)
                )
            ).all()
            heatmap = [{"weekday": int(cell[0]), "hour": int(cell[1]), "count": int(cell[2])} for cell in cells]
    stream = await list_events(guild_id, limit=20)
    return {
        "total": int(total),
        "by_severity": {name: int(count) for name, count in severities},
        "by_engine": {name: int(count) for name, count in engines},
        "by_action_class": {name: int(count) for name, count in classes},
        "by_outcome": {name: int(count) for name, count in outcomes},
        "series": [{"day": row[0].date().isoformat(), "count": int(row[1])} for row in series],
        "heatmap": heatmap,
        "event_stream": [row for row in stream["events"] if row["category"] in {"member_moderation", "bot_actions"}],
    }
