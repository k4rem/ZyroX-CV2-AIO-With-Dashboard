"""Connect a stored observation to the pure policy engine. No Discord mutation."""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert

from cls_platform.config import ROOT_OWNER_ID
from cls_platform.database import session_scope
from cls_platform.security.alerts import enqueue_alert
from cls_platform.security.models import SecurityIncidentEvent, SecurityObservation, SecurityResponseAction
from cls_platform.security.policy_engine import PolicyObservation, Subject, TrustSnapshot, evaluate
from cls_platform.security.trust import active_trust
from cls_platform.services.audit import _redact


async def apply_policy(
    observation_id: uuid.UUID,
    *,
    now: datetime,
    guild_owners: dict[int, int] | None = None,
) -> None:
    async with session_scope() as session:
        current = (
            await session.execute(select(SecurityObservation).where(SecurityObservation.id == observation_id))
        ).scalar_one_or_none()
        if current is None or current.actor_id is None or current.incident_id is None:
            return
        guild_id = int(current.guild_id)
        actor_id = int(current.actor_id)
        incident_id = current.incident_id
        rows = (
            await session.execute(
                select(SecurityObservation).where(
                    SecurityObservation.guild_id == guild_id,
                    SecurityObservation.actor_id == actor_id,
                    SecurityObservation.entry_created_at.is_not(None),
                    SecurityObservation.entry_created_at >= now - timedelta(minutes=10),
                )
            )
        ).scalars().all()
        mapped = [
            PolicyObservation(
                id=str(row.id),
                guild_id=int(row.guild_id),
                action_class=row.action_class,
                audit_entry_id=row.audit_entry_id,
                target_id=row.target_id,
                actor_id=row.actor_id,
                attribution_state=row.attribution_state,
                late=bool(row.late),
                at=row.entry_created_at,
                permission_tier=row.permission_tier,
                everyone_grant=bool(row.target_id == row.guild_id and row.permission_tier == "CRITICAL_CONTROL"),
            )
            for row in rows
            if row.entry_created_at is not None
        ]
    trust_row = await active_trust(guild_id, actor_id, now=now)
    trust = TrustSnapshot(
        trusted=trust_row is not None,
        scopes=tuple(trust_row.scopes or []) if trust_row is not None else (),
    )
    decisions = evaluate(
        Subject(
            guild_id=guild_id,
            user_id=actor_id,
            is_root=ROOT_OWNER_ID is not None and actor_id == ROOT_OWNER_ID,
            is_guild_owner=(guild_owners or {}).get(guild_id) == actor_id,
        ),
        mapped,
        None,
        trust,
        now,
    )
    for decision in decisions:
        if decision.effective_mode != "OBSERVE":
            continue
        payload = _redact(
            {
                "rule_id": decision.rule_id,
                "explanation": decision.explanation,
                "would_contain": decision.would_contain,
                "late_excluded": decision.late_excluded,
                "suppression_reason": decision.suppression_reason,
                "replayable": False,
            }
        )
        async with session_scope() as session:
            session.add(
                SecurityIncidentEvent(
                    incident_id=incident_id,
                    guild_id=guild_id,
                    kind="policy",
                    payload=payload,
                )
            )
        if not decision.would_contain:
            await enqueue_alert(
                guild_id=guild_id,
                incident_id=incident_id,
                kind=f"policy:{decision.rule_id}",
                payload=payload,
                now=now,
            )
            continue
        minute = int(now.timestamp()) // 60
        async with session_scope() as session:
            await session.execute(
                pg_insert(SecurityResponseAction)
                .values(
                    id=uuid.uuid4(),
                    guild_id=guild_id,
                    incident_id=incident_id,
                    subject_id=actor_id,
                    idempotency_key=f"would:{guild_id}:{actor_id}:{decision.rule_id}:{minute}",
                    outcome="WOULD_CONTAIN",
                    effective_mode="OBSERVE",
                    discord_mutation=False,
                    rule_id=decision.rule_id,
                    explanation=decision.explanation,
                )
                .on_conflict_do_nothing(index_elements=["idempotency_key"])
            )
        await enqueue_alert(
            guild_id=guild_id,
            incident_id=incident_id,
            kind=f"would_contain:{decision.rule_id}",
            payload=payload,
            now=now,
        )
