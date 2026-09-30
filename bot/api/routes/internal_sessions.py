"""Internal session creation (Next.js server only)."""

from __future__ import annotations

import httpx
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from api.auth.policy import mark_internal
from cls_platform.config import POSTGRES_ENABLED
from cls_platform.services import sessions as session_service

router = APIRouter()


class SessionCreateRequest(BaseModel):
    discord_access_token: str = Field(min_length=10)


class SessionCreateResponse(BaseModel):
    session_id: str
    discord_user_id: str


@router.post("/sessions", response_model=SessionCreateResponse)
@mark_internal
async def create_dashboard_session(body: SessionCreateRequest):
    if not POSTGRES_ENABLED:
        raise HTTPException(status_code=503, detail="PostgreSQL is disabled")

    async with httpx.AsyncClient(timeout=10.0) as client:
        resp = await client.get(
            "https://discord.com/api/v10/users/@me",
            headers={"Authorization": f"Bearer {body.discord_access_token}"},
        )
    if resp.status_code != 200:
        raise HTTPException(status_code=401, detail="Discord identity verification failed")

    data = resp.json()
    try:
        user_id = int(data["id"])
    except (KeyError, TypeError, ValueError):
        raise HTTPException(status_code=401, detail="Invalid Discord user payload")

    session_id = await session_service.create_session(user_id)
    return SessionCreateResponse(session_id=str(session_id), discord_user_id=str(user_id))


class SessionRevokeRequest(BaseModel):
    session_id: str


@router.post("/sessions/revoke")
@mark_internal
async def revoke_dashboard_session(body: SessionRevokeRequest):
    import uuid

    try:
        sid = uuid.UUID(body.session_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid session id")
    ok = await session_service.revoke_session(sid, reason="logout")
    return {"revoked": ok}
