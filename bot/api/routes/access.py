"""Root-only Dashboard access / RBAC management."""

from __future__ import annotations

import uuid
from typing import List, Optional

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field

from cls_platform.capabilities import ROOT_ONLY, SYSTEM_ROLE_TEMPLATES
from cls_platform.services import audit as audit_service
from cls_platform.services import grants as grant_service
from cls_platform.services import sessions as session_service
from cls_platform.database import session_scope
from cls_platform.models import DashboardRole
from sqlalchemy import select

router = APIRouter()


class GrantCreateBody(BaseModel):
    guild_id: int
    discord_user_id: int
    template_key: str = Field(description="admin|moderator|support|custom")
    custom_role_id: Optional[str] = None


class CustomRoleBody(BaseModel):
    name: str
    capabilities: List[str]


@router.get("/grants")
async def list_grants(request: Request, guild_id: Optional[int] = None):
    auth = request.state.dashboard_auth
    if not auth.is_root:
        raise HTTPException(status_code=403, detail="Root access required")
    if guild_id is not None:
        grants = await grant_service.list_grants_for_guild(guild_id)
    else:
        from cls_platform.models import DashboardGrant
        from sqlalchemy import select
        from sqlalchemy.orm import selectinload

        async with session_scope() as session:
            result = await session.execute(
                select(DashboardGrant)
                .options(selectinload(DashboardGrant.role))
                .where(DashboardGrant.revoked_at.is_(None))
                .order_by(DashboardGrant.created_at.desc())
            )
            grants = list(result.scalars().all())
    return [
        {
            "id": str(g.id),
            "guild_id": str(g.guild_id),
            "discord_user_id": str(g.discord_user_id),
            "role": g.role.name if g.role else None,
            "template_key": g.role.template_key if g.role else None,
        }
        for g in grants
    ]


@router.post("/grants")
async def create_grant(request: Request, body: GrantCreateBody):
    auth = request.state.dashboard_auth
    if not auth.is_root:
        raise HTTPException(status_code=403, detail="Root access required")

    if body.template_key == "custom":
        if not body.custom_role_id:
            raise HTTPException(status_code=400, detail="custom_role_id required")
        role_id = uuid.UUID(body.custom_role_id)
    else:
        role = await grant_service.get_role_by_template(body.template_key)
        if not role:
            raise HTTPException(status_code=400, detail="Unknown template")
        role_id = role.id

    async with session_scope() as session:
        result = await session.execute(select(DashboardRole).where(DashboardRole.id == role_id))
        role_row = result.scalar_one_or_none()
        if not role_row:
            raise HTTPException(status_code=404, detail="Role not found")
        if any(c in ROOT_ONLY for c in (role_row.capabilities or [])):
            raise HTTPException(status_code=400, detail="Cannot assign root-only role")

    grant = await grant_service.create_grant(body.guild_id, body.discord_user_id, role_id)
    await audit_service.record_audit(
        action="dashboard.grant.create",
        actor_user_id=auth.user_id,
        guild_id=body.guild_id,
        session_id=auth.session_id,
        target=str(body.discord_user_id),
        after_state={"grant_id": str(grant.id), "role_id": str(role_id)},
    )
    return {"id": str(grant.id)}


@router.delete("/grants/{grant_id}")
async def revoke_grant_route(request: Request, grant_id: str):
    auth = request.state.dashboard_auth
    if not auth.is_root:
        raise HTTPException(status_code=403, detail="Root access required")
    ok = await grant_service.revoke_grant(uuid.UUID(grant_id))
    if not ok:
        raise HTTPException(status_code=404, detail="Grant not found")
    await audit_service.record_audit(
        action="dashboard.grant.revoke",
        actor_user_id=auth.user_id,
        session_id=auth.session_id,
        target=grant_id,
    )
    return {"revoked": True}


@router.get("/roles")
async def list_roles(request: Request):
    auth = request.state.dashboard_auth
    if not auth.is_root:
        raise HTTPException(status_code=403, detail="Root access required")
    roles = await grant_service.list_roles()
    return [
        {
            "id": str(r.id),
            "name": r.name,
            "template_key": r.template_key,
            "capabilities": r.capabilities,
        }
        for r in roles
    ]


@router.post("/roles/custom")
async def create_custom_role(request: Request, body: CustomRoleBody):
    auth = request.state.dashboard_auth
    if not auth.is_root:
        raise HTTPException(status_code=403, detail="Root access required")
    if any(c in ROOT_ONLY for c in body.capabilities):
        raise HTTPException(status_code=400, detail="Root-only capabilities not allowed")
    async with session_scope() as session:
        row = DashboardRole(name=body.name, template_key="custom", capabilities=body.capabilities)
        session.add(row)
        await session.flush()
        role_id = str(row.id)
    await audit_service.record_audit(
        action="dashboard.role.create",
        actor_user_id=auth.user_id,
        session_id=auth.session_id,
        after_state={"role_id": role_id, "capabilities": body.capabilities},
    )
    return {"id": role_id}


@router.post("/sessions/{session_id}/revoke")
async def revoke_session_route(request: Request, session_id: str):
    auth = request.state.dashboard_auth
    if not auth.is_root:
        raise HTTPException(status_code=403, detail="Root access required")
    ok = await session_service.revoke_session(uuid.UUID(session_id), reason="root_revoke")
    await audit_service.record_audit(
        action="dashboard.session.revoke",
        actor_user_id=auth.user_id,
        session_id=auth.session_id,
        target=session_id,
    )
    return {"revoked": ok}
