"""Append-only internal audit log."""

from __future__ import annotations

import uuid
from typing import Any, Optional

from cls_platform.database import session_scope
from cls_platform.models import AuditEvent

_SECRET_KEYS = frozenset({"password", "token", "secret", "authorization", "api_key"})


def _redact(obj: Any) -> Any:
    if isinstance(obj, dict):
        out = {}
        for k, v in obj.items():
            if str(k).lower() in _SECRET_KEYS:
                out[k] = "[REDACTED]"
            else:
                out[k] = _redact(v)
        return out
    if isinstance(obj, list):
        return [_redact(x) for x in obj]
    return obj


async def record_audit(
    *,
    action: str,
    actor_user_id: Optional[int] = None,
    guild_id: Optional[int] = None,
    session_id: Optional[uuid.UUID] = None,
    target: Optional[str] = None,
    before_state: Optional[dict[str, Any]] = None,
    after_state: Optional[dict[str, Any]] = None,
    context: Optional[dict[str, Any]] = None,
) -> None:
    row = AuditEvent(
        actor_user_id=actor_user_id,
        guild_id=guild_id,
        session_id=session_id,
        action=action,
        target=target,
        before_state=_redact(before_state) if before_state else None,
        after_state=_redact(after_state) if after_state else None,
        context=_redact(context) if context else None,
    )
    async with session_scope() as session:
        session.add(row)
