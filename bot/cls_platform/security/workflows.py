"""Security Center workflows. ENFORCE stays locked. Message deletion is the live OBSERVE action."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import func, or_, select

from cls_platform.database import session_scope
from cls_platform.discord_types import snowflake_to_str
from cls_platform.security.center import get_settings, note_signal, phishing_match, trap_action
from cls_platform.security.enforce_lock import enforce_unlocked
from cls_platform.security.logbridge import security_event
from cls_platform.security.models import (
    SecurityIncident,
    SecurityIncidentEvent,
    SecurityObservation,
    SecurityResponseAction,
)
from cls_platform.security.product import (
    LABELS,
    MESSAGE_KINDS,
    confidence_label,
    delete_failure_detail,
    detector_description,
    detector_title,
    honeypot_exempt,
    incident_heading,
    severity_label,
    status_label,
)

PAGE_SIZES = {25, 50, 100}


def _page_size(value: int) -> int:
    return value if value in PAGE_SIZES else 25


async def _delete(delete_message) -> dict:
    try:
        await delete_message()
    except Exception as exc:
        detail = delete_failure_detail(exc)
        return {"outcome": "failed", "reason": detail, "discord_error": detail}
    return {"outcome": "succeeded", "reason": "Message deleted"}


async def handle_center_message(
    *,
    guild_id: int,
    channel_id: int,
    author_id: int,
    content: str,
    author_is_bot: bool,
    webhook: bool,
    trusted: bool,
    staff: bool,
    eligible: bool,
    delete_message,
) -> dict:
    if not eligible:
        return {"handled": False, "reason": "ineligible"}
    settings = await get_settings(guild_id)
    honeypot = settings.get("honeypot_channel_id")
    traps = {int(item) for item in settings.get("trap_channel_ids") or []}

    if honeypot and int(honeypot) == int(channel_id) and not honeypot_exempt(
        author_is_bot=author_is_bot, webhook=webhook, staff=staff, trusted=trusted
    ):
        result = await _delete(delete_message)
        incident_id = await note_signal(
            guild_id=guild_id,
            subject_id=author_id,
            engine="human",
            kind="human_honeypot",
            detail=result["reason"],
            extra={"action_result": result, "channel_id": snowflake_to_str(channel_id)},
        )
        return {"handled": True, "kind": "human_honeypot", "incident_id": incident_id, "action": result}

    if int(channel_id) in traps and (author_is_bot or webhook):
        action = trap_action(
            author_is_bot=author_is_bot,
            webhook=webhook,
            trusted=trusted,
            mode="ENFORCE",
            enforce_locked=not enforce_unlocked(),
        )
        if action == "ignore":
            return {"handled": False, "reason": "exempt"}
        result = (
            {"outcome": "skipped", "reason": "The bot trap recorded this. It did not ban the bot."}
            if action == "ban"
            else {"outcome": "succeeded", "reason": "Recorded"}
        )
        kind = "webhook_activity" if action == "record_webhook" else "bot_trap"
        incident_id = await note_signal(
            guild_id=guild_id,
            subject_id=author_id,
            engine="bot",
            kind=kind,
            detail=result["reason"],
            extra={"action_result": result, "decision": action},
        )
        return {"handled": True, "kind": kind, "incident_id": incident_id, "action": result}

    if not phishing_match(content or ""):
        return {"handled": False, "reason": "no_match"}
    result = await _delete(delete_message)
    results = [result]
    punishment = settings.get("phishing_action")
    if punishment in {"delete_timeout", "kick", "ban"}:
        reason = (
            "Member punishment stays locked until ENFORCE is available."
            if not enforce_unlocked()
            else "Member punishment is not executed from message detection."
        )
        results.append({"outcome": "skipped", "reason": reason})
    incident_id = await note_signal(
        guild_id=guild_id,
        subject_id=author_id,
        engine="human",
        kind="phishing",
        detail=result["reason"],
        extra={"action_result": result, "results": results, "channel_id": snowflake_to_str(channel_id)},
    )
    return {"handled": True, "kind": "phishing", "incident_id": incident_id, "action": result, "results": results}


def _action_of(kind: str | None, payload: dict | None) -> str | None:
    body = payload or {}
    what = body.get("what")
    if isinstance(what, str) and what in LABELS:
        return what
    if kind in LABELS:
        return kind
    return kind


def _row_view(incident: SecurityIncident, kind: str | None, detail: str | None, state: str | None) -> dict:
    title, subtitle = incident_heading(kind, detail)
    if kind in MESSAGE_KINDS:
        confidence = "Confirmed"
        source = "message"
    else:
        confidence = confidence_label(state)
        source = "audit" if state else "none"
    return {
        "id": str(incident.id),
        "title": title,
        "subtitle": subtitle,
        "status": incident.status,
        "status_label": status_label(incident.status, incident.closure),
        "closure": incident.closure,
        "severity": incident.severity,
        "severity_label": severity_label(incident.severity),
        "actor_id": snowflake_to_str(incident.subject_id) if incident.subject_id else None,
        "detector": detector_title(kind or incident.engine),
        "detector_id": kind or incident.engine,
        "confidence_label": confidence,
        "confidence_source": source,
        "opened_at": incident.opened_at.isoformat() if incident.opened_at else None,
        "engine": incident.engine,
    }


async def list_incidents(
    guild_id: int,
    *,
    status: str | None = None,
    severity: str | None = None,
    detector: str | None = None,
    actor: str | None = None,
    target: str | None = None,
    confidence: str | None = None,
    start: datetime | None = None,
    end: datetime | None = None,
    page: int = 1,
    page_size: int = 25,
) -> dict:
    size = _page_size(page_size)
    page = max(1, page)
    async with session_scope() as session:
        query = select(SecurityIncident).where(SecurityIncident.guild_id == guild_id)
        if status:
            query = query.where(SecurityIncident.status == status)
        if severity:
            query = query.where(SecurityIncident.severity == severity)
        if start:
            query = query.where(SecurityIncident.opened_at >= start)
        if end:
            query = query.where(SecurityIncident.opened_at <= end)
        if actor:
            query = query.where(SecurityIncident.subject_id == int(actor))
        if detector:
            event_ids = select(SecurityIncidentEvent.incident_id).where(SecurityIncidentEvent.kind == detector)
            obs_ids = select(SecurityObservation.incident_id).where(
                SecurityObservation.guild_id == guild_id,
                SecurityObservation.action_class == detector,
                SecurityObservation.incident_id.is_not(None),
            )
            query = query.where(or_(SecurityIncident.id.in_(event_ids), SecurityIncident.id.in_(obs_ids)))
        if target:
            target_ids = select(SecurityObservation.incident_id).where(
                SecurityObservation.guild_id == guild_id,
                SecurityObservation.target_id == int(target),
                SecurityObservation.incident_id.is_not(None),
            )
            query = query.where(SecurityIncident.id.in_(target_ids))
        if confidence:
            wanted = confidence.upper()
            if wanted == "CONFIRMED":
                kinds = select(SecurityIncidentEvent.incident_id).where(SecurityIncidentEvent.kind.in_(MESSAGE_KINDS))
                states = select(SecurityObservation.incident_id).where(
                    SecurityObservation.attribution_state == "CONFIRMED",
                    SecurityObservation.incident_id.is_not(None),
                )
                query = query.where(or_(SecurityIncident.id.in_(kinds), SecurityIncident.id.in_(states)))
            else:
                states = select(SecurityObservation.incident_id).where(
                    SecurityObservation.guild_id == guild_id,
                    SecurityObservation.attribution_state == wanted,
                    SecurityObservation.incident_id.is_not(None),
                )
                query = query.where(SecurityIncident.id.in_(states))
        total = (
            await session.execute(select(func.count()).select_from(query.subquery()))
        ).scalar_one()
        rows = (
            await session.execute(
                query.order_by(SecurityIncident.opened_at.desc()).offset((page - 1) * size).limit(size)
            )
        ).scalars().all()
        ids = [row.id for row in rows]
        events = []
        observations = []
        if ids:
            events = (
                await session.execute(
                    select(SecurityIncidentEvent)
                    .where(SecurityIncidentEvent.incident_id.in_(ids))
                    .order_by(SecurityIncidentEvent.created_at.desc())
                )
            ).scalars().all()
            observations = (
                await session.execute(
                    select(SecurityObservation).where(SecurityObservation.incident_id.in_(ids))
                )
            ).scalars().all()
    latest_event: dict = {}
    labeled_event: dict = {}
    action_counts: dict = {}
    for event in events:
        latest_event.setdefault(event.incident_id, event)
        action = _action_of(event.kind, event.payload)
        if action in LABELS:
            labeled_event.setdefault(event.incident_id, event)
        if action:
            action_counts[(event.incident_id, action)] = action_counts.get((event.incident_id, action), 0) + 1
    latest_state: dict = {}
    for obs in observations:
        latest_state.setdefault(obs.incident_id, obs.attribution_state)
    pages = max(1, (int(total) + size - 1) // size)
    return {
        "rows": [
            _row_view(
                row,
                *(
                    (
                        _action_of(labeled_event[row.id].kind, labeled_event[row.id].payload),
                        (
                            f"{action_counts.get((row.id, _action_of(labeled_event[row.id].kind, labeled_event[row.id].payload)), 1)} recorded"
                            if action_counts.get((row.id, _action_of(labeled_event[row.id].kind, labeled_event[row.id].payload)), 1) > 1
                            else (labeled_event[row.id].payload or {}).get("detail")
                        ),
                    )
                    if row.id in labeled_event
                    else (
                        latest_event[row.id].kind if row.id in latest_event else None,
                        (latest_event[row.id].payload or {}).get("detail") if row.id in latest_event else None,
                    )
                ),
                latest_state.get(row.id),
            )
            for row in rows
        ],
        "page": page,
        "page_size": size,
        "pages": pages,
        "total": int(total),
    }


async def present_incident(guild_id: int, incident_id: str) -> dict:
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
        observations = (
            await session.execute(
                select(SecurityObservation)
                .where(SecurityObservation.incident_id == incident.id)
                .order_by(SecurityObservation.created_at)
            )
        ).scalars().all()
        actions = (
            await session.execute(
                select(SecurityResponseAction)
                .where(SecurityResponseAction.incident_id == incident.id)
                .order_by(SecurityResponseAction.created_at)
            )
        ).scalars().all()
    labeled = [event for event in events if _action_of(event.kind, event.payload) in LABELS]
    chosen = labeled[-1] if labeled else (events[-1] if events else None)
    kind = _action_of(chosen.kind, chosen.payload) if chosen else None
    detail = (chosen.payload or {}).get("detail") if chosen else None
    if chosen and not detail:
        same = sum(1 for event in events if _action_of(event.kind, event.payload) == kind)
        if same > 1:
            detail = f"{same} recorded"
    state = observations[-1].attribution_state if observations else None
    view = _row_view(incident, kind, detail, state)
    timeline = []
    results = []
    for event in events:
        payload = event.payload or {}
        action = _action_of(event.kind, payload)
        why = payload.get("why") if isinstance(payload.get("why"), dict) else {}
        title, subtitle = incident_heading(action, payload.get("detail") or why.get("explanation"))
        timeline.append(
            {
                "sentence": f"{title}. {subtitle}",
                "at": event.created_at.isoformat() if event.created_at else None,
                "confidence_label": confidence_label((payload.get("who") or {}).get("attribution_state")) if isinstance(payload.get("who"), dict) else view["confidence_label"],
            }
        )
        if payload.get("action_result"):
            results.append(payload["action_result"])
        for item in payload.get("results") or []:
            if item not in results:
                results.append(item)
    evidence = []
    for obs in observations:
        evidence.append(
            {
                "summary": detector_description(obs.action_class),
                "detector": detector_title(obs.action_class),
                "confidence_label": confidence_label(obs.attribution_state),
                "source": obs.source,
                "at": obs.entry_created_at.isoformat() if obs.entry_created_at else None,
            }
        )
    for event in events:
        if event.kind in {"observation", "policy"}:
            continue
        payload = event.payload or {}
        evidence.append(
            {
                "summary": payload.get("detail") or detector_description(event.kind),
                "detector": detector_title(event.kind),
                "confidence_label": "Confirmed" if event.kind in MESSAGE_KINDS else "Unknown",
                "source": "message" if event.kind in MESSAGE_KINDS else "incident",
                "at": event.created_at.isoformat() if event.created_at else None,
            }
        )
    would = []
    if not enforce_unlocked():
        would = [
            "Ban the actor",
            "Kick the actor",
            "Strip roles",
            "Quarantine the actor",
        ]
    return {
        **view,
        "summary": view["subtitle"],
        "timeline": timeline,
        "evidence": evidence,
        "response": {
            "did": results,
            "would_enforce": would,
            "enforce_locked": not enforce_unlocked(),
        },
        "events": [
            {"kind": row.kind, "payload": row.payload, "created_at": row.created_at.isoformat()}
            for row in events
        ],
        "developer": {
            "incident_id": str(incident.id),
            "engine": incident.engine,
            "subject_id": view["actor_id"],
            "detector_id": view["detector_id"],
            "events": [row.payload for row in events],
            "actions": [
                {"outcome": row.outcome, "explanation": row.explanation, "discord_mutation": row.discord_mutation}
                for row in actions
            ],
        },
    }


async def close_incident(
    *,
    guild_id: int,
    incident_id: str,
    actor_user_id: int,
    closure: str,
    note: str | None = None,
) -> dict:
    if closure not in {"RESOLVED", "FALSE_POSITIVE"}:
        raise ValueError("closure must be RESOLVED or FALSE_POSITIVE")
    async with session_scope() as session:
        incident = await session.get(SecurityIncident, uuid.UUID(incident_id))
        if incident is None or incident.guild_id != guild_id:
            raise ValueError("missing")
        if incident.status != "ACTIVE":
            raise ValueError("incident is already closed")
        now = datetime.now(timezone.utc)
        incident.status = "CLOSED"
        incident.closure = closure
        incident.closed_at = now
        incident.closed_by = actor_user_id
        incident.last_activity_at = now
        session.add(
            SecurityIncidentEvent(
                incident_id=incident.id,
                guild_id=guild_id,
                kind="resolution",
                payload={
                    "detail": note.strip() if note else status_label("CLOSED", closure),
                    "closure": closure,
                    "actor_id": snowflake_to_str(actor_user_id),
                },
            )
        )
    body = await present_incident(guild_id, incident_id)
    body["offer_trust"] = closure == "FALSE_POSITIVE"
    return body
