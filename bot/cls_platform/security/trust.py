"""Guild-scoped V2 trust. Root only. Legacy whitelist and extra owners are not imported."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import select, update

from cls_platform.discord_types import snowflake_to_str
from cls_platform.services.audit import record_audit
from cls_platform.services.grants import is_root_user
from cls_platform.database import session_scope
from cls_platform.security.models import SecurityGuildState, SecurityTrustedActor
from cls_platform.security.taxonomy import ACTION_SPECS


class TrustRejected(Exception):
    def __init__(self, message: str, status_code: int = 422) -> None:
        super().__init__(message)
        self.status_code = status_code


def _require_root(actor_user_id: int) -> None:
    if not is_root_user(actor_user_id):
        raise TrustRejected("security.trust.manage is Root only", status_code=403)


def _parse_subject(subject_id: int) -> int:
    try:
        return int(snowflake_to_str(subject_id))
    except (TypeError, ValueError) as exc:
        raise TrustRejected("Invalid Discord snowflake", status_code=422) from exc


async def grant_trust(
    *,
    guild_id: int,
    subject_id: int,
    kind: str,
    scopes: list[str],
    actor_user_id: int,
    expires_at: Optional[datetime] = None,
) -> SecurityTrustedActor:
    _require_root(actor_user_id)
    if kind not in {"human", "bot"}:
        raise TrustRejected("kind must be human or bot", status_code=422)
    subject = _parse_subject(subject_id)
    guild = _parse_subject(guild_id)
    unknown = [scope for scope in scopes if scope not in ACTION_SPECS]
    if unknown:
        raise TrustRejected(f"Unknown trust scope: {unknown[0]}", status_code=422)
    async with session_scope() as session:
        existing = (
            await session.execute(
                select(SecurityTrustedActor).where(
                    SecurityTrustedActor.guild_id == guild,
                    SecurityTrustedActor.subject_id == subject,
                    SecurityTrustedActor.revoked_at.is_(None),
                )
            )
        ).scalar_one_or_none()
        before = None
        if existing is not None:
            before = {"scopes": list(existing.scopes or []), "kind": existing.kind}
            existing.scopes = list(scopes)
            existing.kind = kind
            existing.expires_at = expires_at
            row = existing
        else:
            row = SecurityTrustedActor(
                guild_id=guild,
                subject_id=subject,
                kind=kind,
                scopes=list(scopes),
                expires_at=expires_at,
                created_by=actor_user_id,
            )
            session.add(row)
        state = (
            await session.execute(select(SecurityGuildState).where(SecurityGuildState.guild_id == guild))
        ).scalar_one_or_none()
        if state is None:
            state = SecurityGuildState(guild_id=guild, trust_version=1)
            session.add(state)
        else:
            state.trust_version = int(state.trust_version or 0) + 1
        await session.flush()
        trust_id = row.id
    await record_audit(
        action="security.trust.grant",
        actor_user_id=actor_user_id,
        guild_id=guild,
        target=str(subject),
        before_state=before,
        after_state={"scopes": list(scopes), "kind": kind, "trust_id": str(trust_id)},
    )
    async with session_scope() as session:
        return (
            await session.execute(select(SecurityTrustedActor).where(SecurityTrustedActor.id == trust_id))
        ).scalar_one()


async def revoke_trust(*, guild_id: int, subject_id: int, actor_user_id: int) -> None:
    _require_root(actor_user_id)
    subject = _parse_subject(subject_id)
    guild = _parse_subject(guild_id)
    async with session_scope() as session:
        row = (
            await session.execute(
                select(SecurityTrustedActor).where(
                    SecurityTrustedActor.guild_id == guild,
                    SecurityTrustedActor.subject_id == subject,
                    SecurityTrustedActor.revoked_at.is_(None),
                )
            )
        ).scalar_one_or_none()
        if row is None:
            raise TrustRejected("Trusted actor not found", status_code=404)
        before = {"scopes": list(row.scopes or []), "kind": row.kind}
        row.revoked_at = datetime.now(timezone.utc)
        await session.execute(
            update(SecurityGuildState)
            .where(SecurityGuildState.guild_id == guild)
            .values(trust_version=SecurityGuildState.trust_version + 1)
        )
    await record_audit(
        action="security.trust.revoke",
        actor_user_id=actor_user_id,
        guild_id=guild,
        target=str(subject),
        before_state=before,
        after_state={"revoked": True},
    )


async def active_trust(guild_id: int, subject_id: int, *, now: Optional[datetime] = None) -> Optional[SecurityTrustedActor]:
    moment = now or datetime.now(timezone.utc)
    async with session_scope() as session:
        row = (
            await session.execute(
                select(SecurityTrustedActor).where(
                    SecurityTrustedActor.guild_id == guild_id,
                    SecurityTrustedActor.subject_id == subject_id,
                    SecurityTrustedActor.revoked_at.is_(None),
                )
            )
        ).scalar_one_or_none()
        if row is None:
            return None
        if row.expires_at is not None and row.expires_at <= moment:
            return None
        return row
