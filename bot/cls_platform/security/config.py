"""Guild security configuration. ENFORCE writes are rejected."""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import select, update
from sqlalchemy.dialects.postgresql import insert as pg_insert

from cls_platform.database import session_scope
from cls_platform.security.constants import (
    ENFORCE_OPERATIONALLY_AVAILABLE,
    PROPOSED_GATEWAY_DEDUPE_S,
    PROPOSED_INCIDENT_INACTIVITY_S,
    PROPOSED_INCIDENT_MAX_LIFETIME_S,
    SecurityMode,
)
from cls_platform.security.models import SecurityActionPolicy, SecurityGuildConfig, SecurityGuildState
from cls_platform.security.response_protocol import EnforceUnavailable

# Development proposals (OD-13). Not production thresholds.
DEFAULT_POLICIES: tuple[dict, ...] = (
    {
        "action_class": "channel.delete",
        "threshold": 3,
        "window_s": 60,
        "containment_eligible": True,
        "rule_kind": "rate",
        "distinct_targets": True,
    },
    {
        "action_class": "role.delete",
        "threshold": 3,
        "window_s": 60,
        "containment_eligible": True,
        "rule_kind": "rate",
        "distinct_targets": True,
    },
    {
        "action_class": "member.ban_or_kick",
        "threshold": 5,
        "window_s": 60,
        "containment_eligible": True,
        "rule_kind": "rate",
        "distinct_targets": True,
    },
    {
        "action_class": "webhook.create",
        "threshold": 5,
        "window_s": 60,
        "containment_eligible": True,
        "rule_kind": "rate",
        "distinct_targets": True,
    },
    {
        "action_class": "aggregate.destructive",
        "threshold": 6,
        "window_s": 120,
        "containment_eligible": True,
        "rule_kind": "aggregate",
        "distinct_targets": False,
    },
    {
        "action_class": "single.everyone_critical_control",
        "threshold": 1,
        "window_s": 0,
        "containment_eligible": True,
        "rule_kind": "single",
        "distinct_targets": False,
        "tier_floor": "CRITICAL_CONTROL",
    },
    {
        "action_class": "single.critical_control_grant",
        "threshold": 1,
        "window_s": 0,
        "containment_eligible": False,
        "rule_kind": "single",
        "distinct_targets": False,
        "tier_floor": "CRITICAL_CONTROL",
    },
    {
        "action_class": "member.prune",
        "threshold": 1,
        "window_s": 0,
        "containment_eligible": False,
        "rule_kind": "single",
        "distinct_targets": False,
    },
    {
        "action_class": "sequence.self_escalation",
        "threshold": 1,
        "window_s": 120,
        "containment_eligible": True,
        "rule_kind": "sequence",
        "distinct_targets": False,
    },
    {
        "action_class": "sequence.platform_impairment",
        "threshold": 1,
        "window_s": 300,
        "containment_eligible": True,
        "rule_kind": "sequence",
        "distinct_targets": False,
    },
)


class ConfigConflict(RuntimeError):
    """Optimistic concurrency conflict (HTTP 409 at the API boundary)."""


def assert_mode_writable(mode: str) -> str:
    try:
        parsed = SecurityMode(mode)
    except ValueError as exc:
        raise ValueError(f"Unknown security mode {mode}") from exc
    if parsed is SecurityMode.ENFORCE or not ENFORCE_OPERATIONALLY_AVAILABLE and mode == "ENFORCE":
        raise EnforceUnavailable(
            "ENFORCE is not operational until containment is implemented. OBSERVE is the highest functional mode."
        )
    return parsed.value


def effective_mode(configured: str) -> str:
    """Highest functional mode in this pass is OBSERVE. ENFORCE never comes back as effective."""
    if configured == SecurityMode.OFF.value:
        return SecurityMode.OFF.value
    return SecurityMode.OBSERVE.value


async def ensure_guild_config(guild_id: int) -> SecurityGuildConfig:
    async with session_scope() as session:
        stmt = (
            pg_insert(SecurityGuildConfig)
            .values(
                guild_id=guild_id,
                human_mode="OBSERVE",
                bot_mode="OBSERVE",
                incident_inactivity_s=PROPOSED_INCIDENT_INACTIVITY_S,
                incident_max_lifetime_s=PROPOSED_INCIDENT_MAX_LIFETIME_S,
                gateway_dedupe_s=PROPOSED_GATEWAY_DEDUPE_S,
                version=1,
            )
            .on_conflict_do_nothing(index_elements=["guild_id"])
        )
        await session.execute(stmt)
        await session.execute(
            pg_insert(SecurityGuildState)
            .values(guild_id=guild_id, trust_version=0, ops_destination_ok=False)
            .on_conflict_do_nothing(index_elements=["guild_id"])
        )
        for policy in DEFAULT_POLICIES:
            await session.execute(
                pg_insert(SecurityActionPolicy)
                .values(
                    guild_id=guild_id,
                    enabled=True,
                    threshold_status="DEVELOPMENT_PROPOSAL",
                    tier_floor=policy.get("tier_floor"),
                    **{k: v for k, v in policy.items() if k != "tier_floor"},
                )
                .on_conflict_do_nothing(index_elements=["guild_id", "action_class"])
            )
        row = (
            await session.execute(
                select(SecurityGuildConfig).where(SecurityGuildConfig.guild_id == guild_id)
            )
        ).scalar_one()
        return row


async def set_subsystem_mode(
    *,
    guild_id: int,
    subsystem: str,
    mode: str,
    expected_version: int,
) -> SecurityGuildConfig:
    if subsystem not in {"human", "bot"}:
        raise ValueError("subsystem must be human or bot")
    writable = assert_mode_writable(mode)
    column = "human_mode" if subsystem == "human" else "bot_mode"
    async with session_scope() as session:
        await ensure_inside(session, guild_id)
        result = await session.execute(
            update(SecurityGuildConfig)
            .where(
                SecurityGuildConfig.guild_id == guild_id,
                SecurityGuildConfig.version == expected_version,
            )
            .values(**{column: writable, "version": expected_version + 1, "updated_at": datetime.now(timezone.utc)})
        )
        if result.rowcount != 1:
            raise ConfigConflict("security config version conflict")
        row = (
            await session.execute(
                select(SecurityGuildConfig).where(SecurityGuildConfig.guild_id == guild_id)
            )
        ).scalar_one()
        return row


async def ensure_inside(session, guild_id: int) -> None:
    await session.execute(
        pg_insert(SecurityGuildConfig)
        .values(guild_id=guild_id)
        .on_conflict_do_nothing(index_elements=["guild_id"])
    )


async def list_policies(guild_id: int) -> list[SecurityActionPolicy]:
    async with session_scope() as session:
        rows = (
            await session.execute(
                select(SecurityActionPolicy)
                .where(SecurityActionPolicy.guild_id == guild_id)
                .order_by(SecurityActionPolicy.action_class)
            )
        ).scalars().all()
        return list(rows)
