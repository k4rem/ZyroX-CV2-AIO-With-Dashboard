"""Automod V2 persistence. Postgres is the source of truth. Legacy files are only read."""

from __future__ import annotations

import time
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

from sqlalchemy import BigInteger, Boolean, DateTime, Integer, String, Text, and_, func, select
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from cls_platform.automod.engine import (
    RULE_NAMES,
    empty_exclusions,
    empty_scope,
    fresh_config,
    validate_config,
)
from cls_platform.database import session_scope
from cls_platform.discord_types import snowflake_to_str
from cls_platform.models import Base

_CACHE: dict[int, tuple[float, dict]] = {}
_TTL_SECONDS = 15


def invalidate(guild_id: int) -> None:
    _CACHE.pop(int(guild_id), None)


class AutomodConfigRow(Base):
    __tablename__ = "automod_v2_configs"

    guild_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    preset: Mapped[str] = mapped_column(String(16), nullable=False, default="balanced")
    exclusions: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    escalations: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    strike_ttl_seconds: Mapped[int] = mapped_column(Integer, nullable=False, default=604800)
    migrated: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    migration_notes: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class AutomodRuleRow(Base):
    __tablename__ = "automod_v2_rules"

    guild_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    rule_id: Mapped[str] = mapped_column(String(32), primary_key=True)
    name: Mapped[str] = mapped_column(String(80), nullable=False)
    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    engine: Mapped[str] = mapped_column(String(24), nullable=False, default="cls")
    mode: Mapped[str] = mapped_column(String(16), nullable=False, default="enforce")
    trigger: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    scope: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    message_action: Mapped[str] = mapped_column(String(16), nullable=False, default="keep")
    member_action: Mapped[str] = mapped_column(String(16), nullable=False, default="none")
    timeout_seconds: Mapped[int] = mapped_column(Integer, nullable=False, default=600)
    notify_action: Mapped[str] = mapped_column(String(16), nullable=False, default="none")
    points: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    last_triggered_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class AutomodViolationRow(Base):
    __tablename__ = "automod_v2_violations"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    guild_id: Mapped[int] = mapped_column(BigInteger, nullable=False, index=True)
    member_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    channel_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    message_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    rule_id: Mapped[str] = mapped_column(String(32), nullable=False)
    summary: Mapped[str] = mapped_column(Text, nullable=False, default="")
    excerpt: Mapped[str] = mapped_column(Text, nullable=False, default="")
    detail: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    false_positive: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    result_status: Mapped[str] = mapped_column(String(16), nullable=False, default="skipped")
    action_keys: Mapped[str] = mapped_column(String(120), nullable=False, default="")
    log_event_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class AutomodStrikeRow(Base):
    __tablename__ = "automod_v2_strikes"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    guild_id: Mapped[int] = mapped_column(BigInteger, nullable=False, index=True)
    member_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    rule_id: Mapped[str] = mapped_column(String(32), nullable=False)
    reason: Mapped[str] = mapped_column(Text, nullable=False, default="")
    points: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    source: Mapped[str] = mapped_column(String(16), nullable=False, default="automod")
    violation_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    moderator_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)


def _iso(value: datetime | None) -> str | None:
    if value is None:
        return None
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.isoformat()


def _sids(values: list) -> list[str]:
    return [str(item) for item in values or []]


def _rule_dict(row: AutomodRuleRow) -> dict[str, Any]:
    return {
        "id": row.rule_id,
        "name": row.name,
        "enabled": row.enabled,
        "engine": row.engine,
        "mode": row.mode,
        "trigger": row.trigger or {},
        "scope": {**empty_scope(), **(row.scope or {})},
        "message_action": row.message_action,
        "member_action": row.member_action,
        "timeout_seconds": row.timeout_seconds,
        "notify_action": row.notify_action,
        "points": row.points,
        "last_triggered_at": _iso(row.last_triggered_at),
    }


def _config_dict(config: AutomodConfigRow, rules: list[AutomodRuleRow]) -> dict[str, Any]:
    order = {rule_id: index for index, rule_id in enumerate(RULE_NAMES)}
    ordered = sorted(rules, key=lambda row: order.get(row.rule_id, 99))
    return {
        "guild_id": snowflake_to_str(config.guild_id),
        "enabled": config.enabled,
        "preset": config.preset,
        "schema_version": 2,
        "exclusions": {**empty_exclusions(), **{key: _sids(values) for key, values in (config.exclusions or {}).items()}},
        "escalations": config.escalations or [],
        "strike_ttl_seconds": config.strike_ttl_seconds,
        "rules": [_rule_dict(row) for row in ordered],
        "migrated": config.migrated,
        "migration_notes": list(config.migration_notes or []),
    }


async def _load(guild_id: int) -> dict[str, Any] | None:
    async with session_scope() as session:
        config = await session.get(AutomodConfigRow, guild_id)
        if config is None:
            return None
        rows = (
            await session.execute(select(AutomodRuleRow).where(AutomodRuleRow.guild_id == guild_id))
        ).scalars().all()
        return _config_dict(config, list(rows))


async def get_config(guild_id: int) -> dict[str, Any]:
    now = time.monotonic()
    cached = _CACHE.get(int(guild_id))
    if cached and cached[0] > now:
        return cached[1]
    loaded = await _load(guild_id)
    if loaded is None:
        loaded = await ensure_config(guild_id)
    _CACHE[int(guild_id)] = (now + _TTL_SECONDS, loaded)
    return loaded


async def ensure_config(guild_id: int) -> dict[str, Any]:
    existing = await _load(guild_id)
    if existing is not None:
        return existing
    from cls_platform.automod.migrate import legacy_seed

    seed, notes, migrated = await legacy_seed(guild_id)
    body = seed or fresh_config("balanced")
    await save_config(guild_id, body, notes=notes, migrated=migrated)
    loaded = await _load(guild_id)
    return loaded or body


async def save_config(
    guild_id: int,
    body: dict,
    *,
    notes: list[str] | None = None,
    migrated: bool | None = None,
) -> dict[str, Any]:
    cleaned = validate_config(body)
    async with session_scope() as session:
        config = await session.get(AutomodConfigRow, guild_id)
        if config is None:
            config = AutomodConfigRow(guild_id=guild_id, migration_notes=notes or [], migrated=bool(migrated))
            session.add(config)
        config.enabled = cleaned["enabled"]
        config.preset = cleaned["preset"]
        config.exclusions = cleaned["exclusions"]
        config.escalations = cleaned["escalations"]
        config.strike_ttl_seconds = cleaned["strike_ttl_seconds"]
        if notes is not None:
            config.migration_notes = notes
        if migrated is not None:
            config.migrated = migrated
        existing = {
            row.rule_id: row
            for row in (await session.execute(select(AutomodRuleRow).where(AutomodRuleRow.guild_id == guild_id))).scalars().all()
        }
        for rule in cleaned["rules"]:
            row = existing.get(rule["id"])
            if row is None:
                row = AutomodRuleRow(guild_id=guild_id, rule_id=rule["id"], name=rule["name"])
                session.add(row)
            row.name = rule["name"]
            row.enabled = rule["enabled"]
            row.engine = "cls"
            row.mode = rule["mode"]
            row.trigger = rule["trigger"]
            row.scope = rule["scope"]
            row.message_action = rule["message_action"]
            row.member_action = rule["member_action"]
            row.timeout_seconds = rule["timeout_seconds"]
            row.notify_action = rule["notify_action"]
            row.points = rule["points"]
        await session.flush()
    invalidate(guild_id)
    loaded = await _load(guild_id)
    assert loaded is not None
    return loaded


def result_status(actions: list[dict]) -> str:
    outcomes = [str(item.get("outcome")) for item in actions]
    if not outcomes:
        return "skipped"
    if any(item == "failed" for item in outcomes):
        return "failed" if all(item == "failed" for item in outcomes) else "mixed"
    if all(item == "skipped" for item in outcomes):
        return "skipped"
    if all(item == "succeeded" for item in outcomes):
        return "succeeded"
    return "mixed"


async def add_violation(
    *,
    guild_id: int,
    member_id: int,
    channel_id: int | None,
    message_id: int | None,
    rule_id: str,
    summary: str,
    excerpt: str,
    detail: dict,
    actions: list[dict],
    log_event_id: str | None,
    occurred_at: datetime | None = None,
) -> str:
    when = occurred_at or datetime.now(timezone.utc)
    status = result_status(actions)
    keys = ",".join(str(item.get("kind")) for item in actions)
    async with session_scope() as session:
        row = AutomodViolationRow(
            guild_id=guild_id,
            member_id=member_id,
            channel_id=channel_id,
            message_id=message_id,
            rule_id=rule_id,
            summary=summary,
            excerpt=excerpt,
            detail=detail,
            result_status=status,
            action_keys=keys,
            log_event_id=log_event_id,
            occurred_at=when,
        )
        session.add(row)
        rule = await session.get(AutomodRuleRow, (guild_id, rule_id))
        if rule is not None:
            rule.last_triggered_at = when
        await session.flush()
        violation_id = str(row.id)
    invalidate(guild_id)
    return violation_id


async def add_strike(
    *,
    guild_id: int,
    member_id: int,
    rule_id: str,
    reason: str,
    points: int,
    ttl_seconds: int,
    source: str,
    violation_id: str | None,
    moderator_id: int | None,
    now: datetime | None = None,
) -> dict[str, Any]:
    created = now or datetime.now(timezone.utc)
    if created.tzinfo is None:
        created = created.replace(tzinfo=timezone.utc)
    expires = created + timedelta(seconds=max(60, int(ttl_seconds)))
    async with session_scope() as session:
        row = AutomodStrikeRow(
            guild_id=guild_id,
            member_id=member_id,
            rule_id=rule_id,
            reason=reason,
            points=points,
            created_at=created,
            expires_at=expires,
            source=source,
            violation_id=uuid.UUID(violation_id) if violation_id else None,
            moderator_id=moderator_id,
        )
        session.add(row)
        await session.flush()
        return _strike_dict(row)


def _strike_dict(row: AutomodStrikeRow) -> dict[str, Any]:
    return {
        "id": str(row.id),
        "guild_id": snowflake_to_str(row.guild_id),
        "member_id": snowflake_to_str(row.member_id),
        "rule_id": row.rule_id,
        "rule_name": RULE_NAMES.get(row.rule_id, row.rule_id),
        "reason": row.reason,
        "points": row.points,
        "created_at": _iso(row.created_at),
        "expires_at": _iso(row.expires_at),
        "source": row.source,
        "violation_id": str(row.violation_id) if row.violation_id else None,
        "moderator_id": snowflake_to_str(row.moderator_id) if row.moderator_id else None,
    }


async def active_strikes(guild_id: int, member_id: int, now: datetime | None = None) -> list[dict]:
    moment = now or datetime.now(timezone.utc)
    async with session_scope() as session:
        rows = (
            await session.execute(
                select(AutomodStrikeRow).where(
                    AutomodStrikeRow.guild_id == guild_id,
                    AutomodStrikeRow.member_id == member_id,
                    AutomodStrikeRow.expires_at >= moment,
                )
            )
        ).scalars().all()
        return [
            {
                "points": row.points,
                "created_at": row.created_at.timestamp(),
                "expires_at": row.expires_at.timestamp(),
            }
            for row in rows
        ]


async def list_strikes(guild_id: int, *, member_id: int | None = None, limit: int = 50) -> list[dict]:
    async with session_scope() as session:
        stmt = select(AutomodStrikeRow).where(AutomodStrikeRow.guild_id == guild_id)
        if member_id:
            stmt = stmt.where(AutomodStrikeRow.member_id == member_id)
        rows = (await session.execute(stmt.order_by(AutomodStrikeRow.created_at.desc()).limit(limit))).scalars().all()
        return [_strike_dict(row) for row in rows]


async def expire_member_strikes(guild_id: int, member_id: int) -> int:
    moment = datetime.now(timezone.utc)
    async with session_scope() as session:
        rows = (
            await session.execute(
                select(AutomodStrikeRow).where(
                    AutomodStrikeRow.guild_id == guild_id,
                    AutomodStrikeRow.member_id == member_id,
                    AutomodStrikeRow.expires_at > moment,
                )
            )
        ).scalars().all()
        for row in rows:
            row.expires_at = moment
        return len(rows)


def _violation_dict(row: AutomodViolationRow) -> dict[str, Any]:
    detail = row.detail or {}
    return {
        "id": str(row.id),
        "guild_id": snowflake_to_str(row.guild_id),
        "member_id": snowflake_to_str(row.member_id),
        "channel_id": snowflake_to_str(row.channel_id) if row.channel_id else None,
        "message_id": snowflake_to_str(row.message_id) if row.message_id else None,
        "rule_id": row.rule_id,
        "rule_name": RULE_NAMES.get(row.rule_id, row.rule_id),
        "summary": row.summary,
        "excerpt": row.excerpt,
        "threshold": detail.get("threshold") or {},
        "detector": detail.get("detector") or {},
        "scope": detail.get("scope") or {},
        "engine": detail.get("engine") or "cls",
        "actions": detail.get("actions") or [],
        "strike": detail.get("strike"),
        "false_positive": row.false_positive,
        "result_status": row.result_status,
        "log_event_id": row.log_event_id,
        "occurred_at": _iso(row.occurred_at),
    }


async def list_violations(
    guild_id: int,
    *,
    page: int,
    page_size: int,
    rule_id: str | None = None,
    member_id: int | None = None,
    channel_id: int | None = None,
    action: str | None = None,
    result: str | None = None,
    since: datetime | None = None,
    until: datetime | None = None,
) -> dict[str, Any]:
    page = max(1, page)
    filters = [AutomodViolationRow.guild_id == guild_id]
    if rule_id:
        filters.append(AutomodViolationRow.rule_id == rule_id)
    if member_id:
        filters.append(AutomodViolationRow.member_id == member_id)
    if channel_id:
        filters.append(AutomodViolationRow.channel_id == channel_id)
    if result:
        filters.append(AutomodViolationRow.result_status == result)
    if action:
        filters.append(AutomodViolationRow.action_keys.contains(action))
    if since:
        filters.append(AutomodViolationRow.occurred_at >= since)
    if until:
        filters.append(AutomodViolationRow.occurred_at <= until)
    where = and_(*filters)
    async with session_scope() as session:
        total = int(await session.scalar(select(func.count()).select_from(AutomodViolationRow).where(where)) or 0)
        rows = (
            await session.execute(
                select(AutomodViolationRow)
                .where(where)
                .order_by(AutomodViolationRow.occurred_at.desc())
                .offset((page - 1) * page_size)
                .limit(page_size)
            )
        ).scalars().all()
    pages = max(1, (total + page_size - 1) // page_size)
    return {"rows": [_violation_dict(row) for row in rows], "total": total, "page": page, "pages": pages, "page_size": page_size}


async def get_violation(guild_id: int, violation_id: str) -> dict | None:
    async with session_scope() as session:
        row = await session.get(AutomodViolationRow, uuid.UUID(violation_id))
        if row is None or row.guild_id != guild_id:
            return None
        return _violation_dict(row)


async def mark_false_positive(guild_id: int, violation_id: str) -> dict | None:
    async with session_scope() as session:
        row = await session.get(AutomodViolationRow, uuid.UUID(violation_id))
        if row is None or row.guild_id != guild_id:
            return None
        row.false_positive = True
        await session.flush()
        return _violation_dict(row)


async def overview(guild_id: int) -> dict[str, Any]:
    config = await get_config(guild_id)
    start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    async with session_scope() as session:
        rows = (
            await session.execute(
                select(AutomodViolationRow).where(
                    AutomodViolationRow.guild_id == guild_id,
                    AutomodViolationRow.occurred_at >= start,
                )
            )
        ).scalars().all()
        recent_rows = (
            await session.execute(
                select(AutomodViolationRow)
                .where(AutomodViolationRow.guild_id == guild_id)
                .order_by(AutomodViolationRow.occurred_at.desc())
                .limit(8)
            )
        ).scalars().all()
    taken = 0
    failed = 0
    for row in rows:
        for action in (row.detail or {}).get("actions") or []:
            if action.get("outcome") == "succeeded" and action.get("kind") not in {"dm", "notice"}:
                taken += 1
            if action.get("outcome") == "failed":
                failed += 1
    enabled_rules = [rule for rule in config["rules"] if rule["enabled"] and config["enabled"] and rule["mode"] == "enforce"]
    return {
        "enabled": config["enabled"],
        "enabled_rules": len(enabled_rules),
        "observe_rules": len([rule for rule in config["rules"] if rule["enabled"] and rule["mode"] == "observe"]),
        "violations_today": len(rows),
        "actions_taken": taken,
        "failed_actions": failed,
        "recent": [_violation_dict(row) for row in recent_rows],
        "migrated": config["migrated"],
        "migration_notes": config["migration_notes"],
    }


def legacy_projection(config: dict) -> dict[str, Any]:
    """Old dashboard shape, derived from V2. Warn is included only because the ledger exists."""
    keys = {
        "flood": "anti_spam",
        "caps": "anti_caps",
        "links": "anti_links",
        "invites": "anti_invites",
        "mentions": "anti_mentions",
        "emoji": "anti_emoji_spam",
    }
    punishments: dict[str, str] = {}
    if config.get("enabled"):
        for rule in config.get("rules") or []:
            if not rule.get("enabled") or rule.get("mode") == "observe":
                continue
            member = rule.get("member_action")
            if member == "timeout":
                action = "mute"
            elif member in {"kick", "ban", "warn"}:
                action = member
            elif rule.get("message_action") == "delete":
                action = "delete"
            else:
                continue
            punishments[keys.get(rule["id"], rule["id"])] = action
    exclusions = config.get("exclusions") or {}
    return {
        "guild_id": str(config.get("guild_id")),
        "enabled": bool(config.get("enabled")),
        "punishments": punishments,
        "ignored_roles": list(exclusions.get("roles") or []) + list(exclusions.get("staff_roles") or []),
        "ignored_channels": list(exclusions.get("channels") or []),
        "logging_channel": None,
    }


async def apply_followup(guild_id: int, violation_id: str, kind: str, value: str) -> dict:
    current = await get_config(guild_id)
    violation = await get_violation(guild_id, violation_id)
    if violation is None:
        raise ValueError("That violation is not in this server.")
    token = str(value).strip()
    if not token:
        raise ValueError("Choose a value to add.")
    rules = current["rules"]
    target = next((rule for rule in rules if rule["id"] == violation["rule_id"]), None)
    if kind == "channel_exclusion":
        if not token.isdigit():
            raise ValueError("Channel id must be a snowflake.")
        target["scope"]["exclude_channels"] = list(dict.fromkeys([*target["scope"]["exclude_channels"], token]))
    elif kind == "role_exclusion":
        if not token.isdigit():
            raise ValueError("Role id must be a snowflake.")
        target["scope"]["exclude_roles"] = list(dict.fromkeys([*target["scope"]["exclude_roles"], token]))
    elif kind == "keyword_exception":
        if target["id"] == "bad_words":
            target["trigger"]["exceptions"] = list(dict.fromkeys([*(target["trigger"].get("exceptions") or []), token]))
        elif target["id"] == "keyword":
            phrases = [item for item in target["trigger"].get("phrases") or [] if item != token]
            target["trigger"]["phrases"] = phrases
        else:
            raise ValueError("This rule has no keyword exception.")
    elif kind == "domain_allowlist":
        if target["id"] != "links":
            raise ValueError("This rule has no domain allowlist.")
        target["trigger"]["allow"] = list(dict.fromkeys([*(target["trigger"].get("allow") or []), token.lower()]))
    else:
        raise ValueError("Unknown follow-up.")
    current["preset"] = "custom"
    return await save_config(guild_id, current)
