"""Connect a stored observation to the pure policy engine. No Discord mutation."""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert

from cls_platform.config import ROOT_OWNER_ID
from cls_platform.database import session_scope
from cls_platform.security.alerts import enqueue_alert
from cls_platform.security.config import effective_mode
from cls_platform.security.maintenance import active_window
from cls_platform.security.models import (
    SecurityActionPolicy,
    SecurityGuildConfig,
    SecurityGuildState,
    SecurityIncidentEvent,
    SecurityObservation,
    SecurityResponseAction,
)
from cls_platform.security.owners import resolve_owner
from cls_platform.security.policy_engine import PolicyObservation, Subject, TrustSnapshot, evaluate
from cls_platform.security.trust import active_trust
from cls_platform.services.audit import _redact

_ALERT_STATES = {"PROBABLE", "AMBIGUOUS", "UNATTRIBUTED", "CLS_PROXIED"}


async def _load_runtime(guild_id: int, *, is_bot: bool, now: datetime) -> tuple[str, dict, bool, int]:
    async with session_scope() as session:
        config = (
            await session.execute(select(SecurityGuildConfig).where(SecurityGuildConfig.guild_id == guild_id))
        ).scalar_one_or_none()
        policies = (
            await session.execute(
                select(SecurityActionPolicy).where(SecurityActionPolicy.guild_id == guild_id)
            )
        ).scalars().all()
        state = (
            await session.execute(select(SecurityGuildState).where(SecurityGuildState.guild_id == guild_id))
        ).scalar_one_or_none()
        configured = "OBSERVE"
        if config is not None:
            configured = config.bot_mode if is_bot else config.human_mode
        loaded = {
            row.action_class: {
                "action_class": row.action_class,
                "threshold": int(row.threshold),
                "window_s": int(row.window_s),
                "containment_eligible": bool(row.containment_eligible),
                "rule_kind": row.rule_kind,
                "distinct_targets": bool(row.distinct_targets),
                "enabled": bool(row.enabled),
            }
            for row in policies
        }
        version = int(state.trust_version) if state is not None else 0
    maintenance = await active_window(guild_id, now)
    mode = effective_mode(configured)
    if maintenance is not None and mode != "OFF":
        mode = "OBSERVE"
    return mode, loaded, maintenance is not None, version


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
        if current is None or current.incident_id is None:
            return
        guild_id = int(current.guild_id)
        incident_id = current.incident_id
        actor_id = int(current.actor_id) if current.actor_id is not None else None
        state_name = current.attribution_state
        severity = current.severity
        action_class = current.action_class
        target_id = int(current.target_id) if current.target_id is not None else None
        actor_is_bot = bool(current.actor_is_bot)
        if action_class == "bot.add" and target_id is not None:
            subject_user = target_id
            is_bot = True
        else:
            subject_user = actor_id
            is_bot = actor_is_bot or action_class.startswith("bot.")
        rows = []
        if actor_id is not None:
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
                everyone_grant=bool(
                    row.target_id == row.guild_id and row.permission_tier == "CRITICAL_CONTROL"
                ),
            )
            for row in rows
            if row.entry_created_at is not None
        ]
        if action_class == "bot.add":
            mapped.append(
                PolicyObservation(
                    id=str(current.id),
                    guild_id=guild_id,
                    action_class=action_class,
                    audit_entry_id=current.audit_entry_id,
                    target_id=target_id,
                    actor_id=actor_id,
                    attribution_state=state_name,
                    late=bool(current.late),
                    at=current.entry_created_at or now,
                    permission_tier=current.permission_tier,
                    everyone_grant=False,
                )
            )
    if subject_user is None:
        if state_name in _ALERT_STATES and severity in {"H", "C"}:
            await enqueue_alert(
                guild_id=guild_id,
                incident_id=incident_id,
                kind=f"attribution:{state_name}",
                payload=_redact(
                    {
                        "attribution_state": state_name,
                        "severity": severity,
                        "action_class": action_class,
                        "guild_id": str(guild_id),
                        "would_contain": False,
                    }
                ),
                now=now,
            )
        return
    live_owner = (guild_owners or {}).get(guild_id)
    owner_id, owner_known = await resolve_owner(guild_id, live_owner)
    mode, policies, maintenance_active, trust_version = await _load_runtime(
        guild_id, is_bot=is_bot, now=now
    )
    trust_row = await active_trust(guild_id, subject_user, now=now)
    trust = TrustSnapshot(
        trusted=trust_row is not None,
        scopes=tuple(trust_row.scopes or []) if trust_row is not None else (),
    )
    decisions = evaluate(
        Subject(
            guild_id=guild_id,
            user_id=subject_user,
            is_bot=is_bot,
            is_root=ROOT_OWNER_ID is not None and subject_user == ROOT_OWNER_ID,
            is_guild_owner=owner_known and owner_id == subject_user,
            owner_known=owner_known,
        ),
        mapped,
        policies or None,
        trust,
        now,
        configured_mode=mode,
        maintenance_active=maintenance_active,
    )
    protected = (ROOT_OWNER_ID is not None and subject_user == ROOT_OWNER_ID) or (
        owner_known and owner_id == subject_user
    )
    if protected and severity in {"H", "C"}:
        await enqueue_alert(
            guild_id=guild_id,
            incident_id=incident_id,
            kind="protected_subject",
            payload=_redact(
                {
                    "severity": severity,
                    "action_class": action_class,
                    "subject_id": str(subject_user),
                    "guild_id": str(guild_id),
                    "would_contain": False,
                    "suppression_reason": "root" if subject_user == ROOT_OWNER_ID else "guild_owner",
                }
            ),
            now=now,
        )
    if not decisions and state_name in _ALERT_STATES and severity in {"H", "C"}:
        await enqueue_alert(
            guild_id=guild_id,
            incident_id=incident_id,
            kind=f"attribution:{state_name}",
            payload=_redact(
                {
                    "attribution_state": state_name,
                    "severity": severity,
                    "action_class": action_class,
                    "subject_id": str(subject_user),
                    "guild_id": str(guild_id),
                    "would_contain": False,
                    "trust_version": trust_version,
                }
            ),
            now=now,
        )
    for decision in decisions:
        if decision.would_contain and (not owner_known or decision.suppression_reason == "owner_unknown"):
            decision.would_contain = False
            decision.containment_eligible = False
            decision.suppression_reason = decision.suppression_reason or "owner_unknown"
        if mode == "OFF":
            decision.would_contain = False
        payload = _redact(
            {
                "rule_id": decision.rule_id,
                "explanation": decision.explanation,
                "would_contain": decision.would_contain,
                "late_excluded": decision.late_excluded,
                "suppression_reason": decision.suppression_reason,
                "severity": decision.severity,
                "attribution_state": state_name,
                "subject_id": str(subject_user),
                "guild_id": str(guild_id),
                "trust_version": trust_version,
                "maintenance_window": maintenance_active,
                "effective_mode": decision.effective_mode,
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
        if not decision.would_contain or decision.effective_mode != "OBSERVE":
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
                    subject_id=subject_user,
                    idempotency_key=f"would:{guild_id}:{subject_user}:{decision.rule_id}:{minute}",
                    outcome="WOULD_CONTAIN",
                    effective_mode="OBSERVE",
                    discord_mutation=False,
                    rule_id=decision.rule_id,
                    ledger_action_class=action_class,
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
