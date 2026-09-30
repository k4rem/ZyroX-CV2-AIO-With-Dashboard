"""Internal identity JWT verification."""

from __future__ import annotations

import uuid
from typing import Any

import jwt
from fastapi import HTTPException

from cls_platform.config import (
    INTERNAL_IDENTITY_AUDIENCE,
    INTERNAL_IDENTITY_SIGNING_KEY,
)
from cls_platform.services import sessions as session_service


def verify_internal_identity_token(token: str) -> dict[str, Any]:
    if not INTERNAL_IDENTITY_SIGNING_KEY:
        raise HTTPException(status_code=503, detail="Identity signing is not configured")
    try:
        payload = jwt.decode(
            token,
            INTERNAL_IDENTITY_SIGNING_KEY,
            algorithms=["HS256"],
            audience=INTERNAL_IDENTITY_AUDIENCE,
            options={"require": ["exp", "iat", "sub", "sid", "jti"]},
        )
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Invalid identity token")
    return payload


async def resolve_auth_from_token(token: str):
    from api.auth.context import DashboardAuthContext
    from cls_platform.services.grants import is_root_user

    payload = verify_internal_identity_token(token)
    try:
        session_id = uuid.UUID(str(payload["sid"]))
        user_id = int(payload["sub"])
    except (ValueError, TypeError, KeyError):
        raise HTTPException(status_code=401, detail="Invalid identity token claims")

    row = await session_service.get_session(session_id)
    if row is None or not session_service.session_is_valid(row):
        raise HTTPException(status_code=401, detail="Session invalid or expired")
    if row.discord_user_id != user_id:
        raise HTTPException(status_code=401, detail="Session subject mismatch")

    await session_service.touch_session(session_id)
    return DashboardAuthContext(
        user_id=user_id,
        session_id=session_id,
        is_root=is_root_user(user_id),
    )
