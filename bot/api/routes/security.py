"""Guild security summary and Root controls. ENFORCE writes stay locked."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel
from sqlalchemy import func, select

from cls_platform.database import session_scope
from cls_platform.discord_types import snowflake_to_str
from cls_platform.security.center import analytics, get_settings, save_settings
from cls_platform.security.config import effective_mode, ensure_guild_config, set_subsystem_mode
from cls_platform.security.enforce_lock import enforce_unlocked
from cls_platform.security.models import (
    SecurityActionPolicy,
    SecurityAlertOutbox,
    SecurityGuildConfig,
    SecurityIncident,
    SecurityMaintenanceWindow,
    SecurityObservation,
    SecurityQuarantine,
    SecurityTrustedActor,
)
from cls_platform.security.product import (
    behavior,
    channel_in_guild,
    group_detectors,
    join_signal,
    posture,
    scope_options,
    scope_title,
)
from cls_platform.security.workflows import close_incident, list_incidents, present_incident
from api.dependencies import get_bot
from cls_platform.config import OPS_GUILD_ID, OPS_SECURITY_ALERT_CHANNEL_ID
from cls_platform.health.contract import runtime_snapshot
from cls_platform.security.maintenance import MaintenanceRejected, end_window, start_window
from cls_platform.security.quarantine import restore_quarantine
from cls_platform.security.response_protocol import EnforceUnavailable
from cls_platform.security.trust import TrustRejected, grant_trust, revoke_trust
from cls_platform.snapshots import list_snapshots

router = APIRouter()

OPEN_QUARANTINE = ("APPLYING", "ACTIVE", "PARTIAL_QUARANTINE")


class ModeBody(BaseModel):
    subsystem: str
    mode: str
    expected_version: int


def _root(request: Request) -> None:
    auth = getattr(request.state, "dashboard_auth", None)
    if auth is None or not auth.is_root:
        raise HTTPException(status_code=403, detail="Root access required")


@router.get("/{guild_id}/security")
async def security_summary(guild_id: int, bot=Depends(get_bot)):
    await ensure_guild_config(guild_id)
    async with session_scope() as session:
        config = (
            await session.execute(select(SecurityGuildConfig).where(SecurityGuildConfig.guild_id == guild_id))
        ).scalar_one()
        policies = (
            await session.execute(
                select(SecurityActionPolicy).where(SecurityActionPolicy.guild_id == guild_id)
            )
        ).scalars().all()
        incidents = (
            await session.execute(
                select(SecurityIncident)
                .where(SecurityIncident.guild_id == guild_id)
                .order_by(SecurityIncident.opened_at.desc())
                .limit(20)
            )
        ).scalars().all()
        quarantines = (
            await session.execute(
                select(SecurityQuarantine).where(
                    SecurityQuarantine.guild_id == guild_id,
                    SecurityQuarantine.status.in_(OPEN_QUARANTINE),
                )
            )
        ).scalars().all()
        trusted = (
            await session.execute(
                select(SecurityTrustedActor).where(
                    SecurityTrustedActor.guild_id == guild_id,
                    SecurityTrustedActor.revoked_at.is_(None),
                )
            )
        ).scalars().all()
        window = (
            await session.execute(
                select(SecurityMaintenanceWindow).where(
                    SecurityMaintenanceWindow.guild_id == guild_id,
                    SecurityMaintenanceWindow.ended_at.is_(None),
                )
            )
        ).scalar_one_or_none()
        pending = (
            await session.execute(
                select(func.count())
                .select_from(SecurityAlertOutbox)
                .where(
                    SecurityAlertOutbox.guild_id == guild_id,
                    SecurityAlertOutbox.status.in_(("PENDING", "CLAIMED", "DEGRADED")),
                )
            )
        ).scalar_one()
        latest_alert = (
            await session.execute(
                select(SecurityAlertOutbox)
                .where(SecurityAlertOutbox.guild_id == guild_id)
                .order_by(SecurityAlertOutbox.created_at.desc())
                .limit(1)
            )
        ).scalar_one_or_none()
        alert_view = None
        if latest_alert is not None:
            alert_view = {
                "status": latest_alert.status,
                "at": (latest_alert.delivered_at or latest_alert.created_at).isoformat(),
                "error": latest_alert.last_error,
            }
        window_start = datetime.now(timezone.utc) - timedelta(days=30)
        counts = dict(
            (
                await session.execute(
                    select(SecurityObservation.action_class, func.count())
                    .where(
                        SecurityObservation.guild_id == guild_id,
                        SecurityObservation.created_at >= window_start,
                    )
                    .group_by(SecurityObservation.action_class)
                )
            ).all()
        )
        last_rows = (
            await session.execute(
                select(SecurityObservation.action_class, func.max(SecurityObservation.created_at))
                .where(SecurityObservation.guild_id == guild_id)
                .group_by(SecurityObservation.action_class)
            )
        ).all()
        open_high = (
            await session.execute(
                select(func.count())
                .select_from(SecurityIncident)
                .where(
                    SecurityIncident.guild_id == guild_id,
                    SecurityIncident.status == "ACTIVE",
                    SecurityIncident.severity.in_(("H", "C")),
                )
            )
        ).scalar_one()
    last_at = {name: moment.isoformat() if moment else None for name, moment in last_rows}
    policy_rows = [
        {
            "action_class": row.action_class,
            "enabled": row.enabled,
            "threshold": row.threshold,
            "window_s": row.window_s,
            "containment_eligible": row.containment_eligible,
            "threshold_status": row.threshold_status,
        }
        for row in policies
    ]
    settings = await get_settings(guild_id)
    locked = not enforce_unlocked()
    joins = _join_rows(bot.get_guild(int(guild_id)) if bot is not None else None)
    signal = join_signal(joins["rows"])
    signal["cached_members"] = joins["cached"]
    signal["note"] = joins["note"]
    snapshots = await list_snapshots(guild_id)
    latest = snapshots[0] if snapshots else None
    return {
        "guild_id": snowflake_to_str(guild_id),
        "human_mode": config.human_mode,
        "bot_mode": config.bot_mode,
        "effective_human_mode": effective_mode(config.human_mode),
        "effective_bot_mode": effective_mode(config.bot_mode),
        "enforce_locked": locked,
        "posture": posture(open_high=int(open_high), join_elevated=bool(signal["elevated"])),
        "behavior": behavior(enforce_locked=locked, honeypot_configured=bool(settings.get("honeypot_channel_id"))),
        "join_signal": signal,
        "version": config.version,
        "permission_health": runtime_snapshot(bot.get_guild(int(guild_id)) if bot is not None else None),
        "policies": policy_rows,
        "detectors": group_detectors(policy_rows, {name: int(count) for name, count in counts.items()}, last_at),
        "scope_options": scope_options(),
        "trusted_actors": [
            {
                "subject_id": snowflake_to_str(row.subject_id),
                "kind": row.kind,
                "tier": "Trusted Bot" if row.kind == "bot" else "Trusted Admin",
                "scopes": row.scopes,
                "scope_label": scope_title(list(row.scopes or [])),
                "granted_by": snowflake_to_str(row.created_by),
                "granted_at": row.created_at.isoformat() if row.created_at else None,
                "expires_at": row.expires_at.isoformat() if row.expires_at else None,
                "reason": row.reason,
                "active": row.expires_at is None or row.expires_at > datetime.now(timezone.utc),
            }
            for row in trusted
        ],
        "maintenance": None
        if window is None
        else {"reason": window.reason, "ends_at": window.expires_at.isoformat()},
        "incidents": [
            {
                "id": str(row.id),
                "status": row.status,
                "engine": row.engine,
                "severity": row.severity,
                "subject_id": snowflake_to_str(row.subject_id) if row.subject_id else None,
            }
            for row in incidents
        ],
        "quarantines": [
            {
                "user_id": snowflake_to_str(row.user_id),
                "status": row.status,
                "status_label": {"ACTIVE": "Quarantined", "PARTIAL_QUARANTINE": "Partially quarantined", "APPLYING": "Applying"}.get(row.status, row.status),
                "incident_id": str(row.incident_id) if row.incident_id else None,
                "prior_role_ids": [snowflake_to_str(item) for item in (row.prior_role_ids or [])],
                "removed_role_ids": [snowflake_to_str(item) for item in (row.removed_role_ids or [])],
                "quarantined_at": row.created_at.isoformat() if row.created_at else None,
                "reason": (row.residual or {}).get("reason") if isinstance(row.residual, dict) else None,
            }
            for row in quarantines
        ],
        "recovery": {
            "latest_snapshot_at": latest.get("created_at") if latest else None,
            "latest_snapshot_id": latest.get("id") if latest else None,
            "snapshot_count": len(snapshots),
            "restore_locked": True,
        },
        "ops": {
            "pending_alerts": int(pending),
            "destination_configured": OPS_GUILD_ID is not None and OPS_SECURITY_ALERT_CHANNEL_ID is not None,
            "destination_label": "Ops security channel" if OPS_GUILD_ID is not None and OPS_SECURITY_ALERT_CHANNEL_ID is not None else "Not configured",
            "last": alert_view,
        },
        "analytics": await analytics(guild_id),
        "center": await get_settings(guild_id),
    }


class CenterBody(BaseModel):
    phishing_action: str | None = None
    trap_channel_ids: list[str] | None = None
    honeypot_channel_id: str | None = None
    honeypot_set: bool = False


class LockBody(BaseModel):
    locked: bool


class CloseBody(BaseModel):
    closure: str
    note: str | None = None


class TrustBody(BaseModel):
    subject_id: str
    kind: str = "human"
    scopes: list[str]
    expires_at: str | None = None
    reason: str | None = None


class RevokeBody(BaseModel):
    subject_id: str


class MaintenanceBody(BaseModel):
    reason: str
    duration_s: int


class MaintenanceEndBody(BaseModel):
    reason: str


def _known_channels(bot, guild_id: int) -> set[int] | None:
    if bot is None:
        return None
    guild = bot.get_guild(int(guild_id))
    if guild is None:
        return set()
    return {int(channel.id) for channel in getattr(guild, "channels", []) or []}


def _require_channels(bot, guild_id: int, channel_ids: list[int]) -> None:
    known = _known_channels(bot, guild_id)
    if known is None:
        return
    for channel_id in channel_ids:
        if not channel_in_guild(known, channel_id):
            raise HTTPException(status_code=422, detail="Channel is not in this server")


def _join_rows(guild) -> dict:
    if guild is None:
        return {"rows": [], "cached": 0, "note": "Join activity appears when CLS is online in this server."}
    rows = []
    members = list(getattr(guild, "members", []) or [])
    for member in members:
        if getattr(member, "bot", False):
            continue
        rows.append({"joined_at": getattr(member, "joined_at", None), "created_at": getattr(member, "created_at", None)})
    note = None
    member_count = getattr(guild, "member_count", None)
    if member_count and member_count > len(members):
        note = "Based on members CLS has cached."
    return {"rows": rows, "cached": len(members), "note": note}


@router.get("/{guild_id}/security/incidents")
async def security_incidents(
    guild_id: int,
    status: str | None = None,
    severity: str | None = None,
    detector: str | None = None,
    actor: str | None = None,
    target: str | None = None,
    confidence: str | None = None,
    start: str | None = None,
    end: str | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(25),
):
    def _moment(value: str | None) -> datetime | None:
        if not value:
            return None
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        return parsed

    return await list_incidents(
        guild_id,
        status=status,
        severity=severity,
        detector=detector,
        actor=actor,
        target=target,
        confidence=confidence,
        start=_moment(start),
        end=_moment(end),
        page=page,
        page_size=page_size,
    )


@router.get("/{guild_id}/security/incidents/{incident_id}")
async def security_incident(guild_id: int, incident_id: str):
    try:
        return await present_incident(guild_id, incident_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/{guild_id}/security/incidents/{incident_id}/close")
async def security_close(guild_id: int, incident_id: str, body: CloseBody, request: Request):
    auth = getattr(request.state, "dashboard_auth", None)
    actor = int(auth.user_id) if auth is not None and getattr(auth, "user_id", None) else 0
    try:
        return await close_incident(
            guild_id=guild_id,
            incident_id=incident_id,
            actor_user_id=actor,
            closure=body.closure,
            note=body.note,
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.put("/{guild_id}/security/center")
async def security_center(guild_id: int, body: CenterBody, bot=Depends(get_bot)):
    trap_ids = [int(item) for item in body.trap_channel_ids] if body.trap_channel_ids is not None else None
    honeypot = int(body.honeypot_channel_id) if body.honeypot_channel_id else None
    check = list(trap_ids or [])
    if body.honeypot_set and honeypot:
        check.append(honeypot)
    _require_channels(bot, guild_id, check)
    try:
        return await save_settings(
            guild_id=guild_id,
            phishing_action=body.phishing_action,
            trap_channel_ids=trap_ids,
            honeypot_channel_id=honeypot,
            honeypot_set=body.honeypot_set,
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.post("/{guild_id}/security/lock")
async def security_lock(guild_id: int, body: LockBody, request: Request):
    _root(request)
    return await save_settings(guild_id=guild_id, dashboard_locked=body.locked)


@router.post("/{guild_id}/security/mode")
async def set_mode(guild_id: int, body: ModeBody, request: Request):
    _root(request)
    if body.mode == "ENFORCE":
        raise HTTPException(status_code=409, detail="ENFORCE stays locked on this API")
    try:
        row = await set_subsystem_mode(
            guild_id=guild_id,
            subsystem=body.subsystem,
            mode=body.mode,
            expected_version=body.expected_version,
        )
    except EnforceUnavailable as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {"human_mode": row.human_mode, "bot_mode": row.bot_mode, "version": row.version}


@router.post("/{guild_id}/security/trust")
async def security_trust_grant(guild_id: int, body: TrustBody, request: Request):
    _root(request)
    auth = request.state.dashboard_auth
    expires = None
    if body.expires_at:
        expires = datetime.fromisoformat(body.expires_at.replace("Z", "+00:00"))
        if expires.tzinfo is None:
            expires = expires.replace(tzinfo=timezone.utc)
    try:
        row = await grant_trust(
            guild_id=guild_id,
            subject_id=int(body.subject_id),
            kind=body.kind,
            scopes=body.scopes,
            actor_user_id=int(auth.user_id),
            expires_at=expires,
            reason=body.reason,
        )
    except TrustRejected as exc:
        raise HTTPException(status_code=exc.status_code, detail=str(exc)) from exc
    return {
        "subject_id": snowflake_to_str(row.subject_id),
        "kind": row.kind,
        "scopes": row.scopes,
        "scope_label": scope_title(list(row.scopes or [])),
        "expires_at": row.expires_at.isoformat() if row.expires_at else None,
        "reason": row.reason,
    }


@router.post("/{guild_id}/security/trust/revoke")
async def security_trust_revoke(guild_id: int, body: RevokeBody, request: Request):
    _root(request)
    auth = request.state.dashboard_auth
    try:
        await revoke_trust(guild_id=guild_id, subject_id=int(body.subject_id), actor_user_id=int(auth.user_id))
    except TrustRejected as exc:
        raise HTTPException(status_code=exc.status_code, detail=str(exc)) from exc
    return {"status": "revoked", "subject_id": body.subject_id}


@router.post("/{guild_id}/security/maintenance")
async def security_maintenance_start(guild_id: int, body: MaintenanceBody, request: Request):
    _root(request)
    auth = request.state.dashboard_auth
    try:
        row = await start_window(
            guild_id=guild_id,
            actor_user_id=int(auth.user_id),
            reason=body.reason,
            duration_s=body.duration_s,
        )
    except MaintenanceRejected as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return {"reason": row.reason, "ends_at": row.expires_at.isoformat(), "effective_mode": "OBSERVE"}


@router.post("/{guild_id}/security/maintenance/end")
async def security_maintenance_end(guild_id: int, body: MaintenanceEndBody, request: Request):
    _root(request)
    auth = request.state.dashboard_auth
    try:
        await end_window(guild_id=guild_id, actor_user_id=int(auth.user_id), reason=body.reason)
    except MaintenanceRejected as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return {"status": "ended", "effective_mode": "OBSERVE"}


@router.post("/{guild_id}/security/alerts/test")
async def security_alert_test(guild_id: int, request: Request, bot=Depends(get_bot)):
    _root(request)
    from cls_platform.security.alerts import destination_is_valid
    from cls_platform.security.ops_sender import DiscordOpsSender

    sender = DiscordOpsSender(bot) if bot is not None else None
    channel = await sender.resolve() if sender is not None else None
    if not destination_is_valid(channel):
        return {"outcome": "failed", "reason": "Ops alert channel is not configured for this deployment"}
    try:
        await sender.send(channel, {"kind": "test", "guild_id": snowflake_to_str(guild_id), "summary": "CLS security alert test"})
    except Exception as exc:
        return {"outcome": "failed", "reason": "Delivery failed", "discord_error": type(exc).__name__}
    return {"outcome": "succeeded", "reason": "Test alert delivered to the Ops channel"}


@router.post("/{guild_id}/security/quarantine/{user_id}/release")
async def release_quarantine_route(guild_id: int, user_id: int, request: Request, bot=Depends(get_bot)):
    _root(request)
    guild = bot.get_guild(int(guild_id)) if bot is not None else None
    member = guild.get_member(int(user_id)) if guild is not None else None
    me = getattr(guild, "me", None) if guild is not None else None
    top = getattr(getattr(me, "top_role", None), "position", 0) if me is not None else 0
    roles = list(getattr(guild, "roles", []) or []) if guild is not None else []
    try:
        return await restore_quarantine(
            guild_id=guild_id,
            user_id=user_id,
            member=member,
            actor_is_root=True,
            roles=roles,
            bot_top_position=int(top or 0),
        )
    except EnforceUnavailable as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
