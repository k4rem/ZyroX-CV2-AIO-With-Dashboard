"""Guild security summary and Root controls. ENFORCE writes stay locked."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel
from sqlalchemy import func, select

from cls_platform.database import session_scope
from cls_platform.discord_types import snowflake_to_str
from cls_platform.security.config import ensure_guild_config, set_subsystem_mode
from cls_platform.security.models import (
    SecurityActionPolicy,
    SecurityAlertOutbox,
    SecurityGuildConfig,
    SecurityIncident,
    SecurityMaintenanceWindow,
    SecurityQuarantine,
    SecurityTrustedActor,
)
from cls_platform.security.response_protocol import EnforceUnavailable

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
async def security_summary(guild_id: int):
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
    return {
        "guild_id": snowflake_to_str(guild_id),
        "human_mode": config.human_mode,
        "bot_mode": config.bot_mode,
        "effective_human_mode": "OBSERVE" if config.human_mode == "ENFORCE" else config.human_mode,
        "effective_bot_mode": "OBSERVE" if config.bot_mode == "ENFORCE" else config.bot_mode,
        "enforce_locked": True,
        "version": config.version,
        "permission_health": "observability_only",
        "policies": [
            {
                "action_class": row.action_class,
                "enabled": row.enabled,
                "threshold": row.threshold,
                "window_s": row.window_s,
                "containment_eligible": row.containment_eligible,
                "threshold_status": row.threshold_status,
            }
            for row in policies
        ],
        "trusted_actors": [
            {"subject_id": snowflake_to_str(row.subject_id), "kind": row.kind, "scopes": row.scopes}
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
                "prior_role_ids": [snowflake_to_str(item) for item in (row.prior_role_ids or [])],
            }
            for row in quarantines
        ],
        "ops": {"pending_alerts": int(pending)},
    }


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


@router.post("/{guild_id}/security/quarantine/{user_id}/release")
async def release_quarantine_route(guild_id: int, user_id: int, request: Request):
    _root(request)
    raise HTTPException(
        status_code=409,
        detail="Quarantine release stays locked. ENFORCE is not enabled for live guilds.",
    )
