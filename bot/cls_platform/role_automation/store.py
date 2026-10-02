"""Role automation persistence. Snowflakes leave this module as strings."""

from __future__ import annotations

import sqlite3
import uuid
from pathlib import Path
from datetime import datetime, timezone

from sqlalchemy import BigInteger, Boolean, DateTime, Integer, String, select
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from cls_platform.database import session_scope
from cls_platform.discord_types import snowflake_to_str
from cls_platform.models import Base
from cls_platform.role_automation.logic import ACTIONS, KINDS, TRIGGERS, delay_seconds

class RuleError(Exception):
    pass


class RoleJoinConfig(Base):
    __tablename__ = "role_join_configs"

    guild_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    member_role_ids: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    bot_role_ids: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    delay_seconds: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    screening: Mapped[str] = mapped_column(String(16), nullable=False, default="immediate")
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))


class RoleAutomationRule(Base):
    __tablename__ = "role_automation_rules"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    guild_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    name: Mapped[str] = mapped_column(String(80), nullable=False)
    trigger: Mapped[str] = mapped_column(String(16), nullable=False)
    trigger_role_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    conditions: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    action: Mapped[str] = mapped_column(String(16), nullable=False)
    action_role_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    delay_seconds: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))


def _ids(values: list | None) -> list[str]:
    found = []
    for value in values or []:
        text = str(value)
        if text.isdigit() and text not in found:
            found.append(text)
    return found[:10]


def _conditions(values: list | None) -> list[dict]:
    cleaned = []
    for item in (values or [])[:8]:
        if not isinstance(item, dict) or item.get("kind") not in KINDS:
            continue
        row = {"kind": item["kind"]}
        if item["kind"] in {"has_role", "lacks_role"}:
            role = str(item.get("role_id") or "")
            if not role.isdigit():
                continue
            row["role_id"] = role
        if item["kind"] == "account_age":
            row["op"] = "gt" if item.get("op") == "gt" else "gte"
            row["amount"] = max(0, min(int(item.get("amount") or 0), 3650))
            row["unit"] = "hours" if item.get("unit") == "hours" else "days"
        cleaned.append(row)
    return cleaned


def _join(row: RoleJoinConfig | None, guild_id: int) -> dict:
    if row is None:
        return {"guild_id": snowflake_to_str(guild_id), "member_role_ids": [], "bot_role_ids": [], "delay_seconds": 0, "screening": "immediate"}
    return {
        "guild_id": snowflake_to_str(row.guild_id),
        "member_role_ids": [str(item) for item in row.member_role_ids or []],
        "bot_role_ids": [str(item) for item in row.bot_role_ids or []],
        "delay_seconds": row.delay_seconds or 0,
        "screening": row.screening or "immediate",
    }


def _rule(row: RoleAutomationRule) -> dict:
    return {
        "id": str(row.id),
        "guild_id": snowflake_to_str(row.guild_id),
        "name": row.name,
        "trigger": row.trigger,
        "trigger_role_id": snowflake_to_str(row.trigger_role_id) if row.trigger_role_id else None,
        "conditions": row.conditions or [],
        "action": row.action,
        "action_role_id": snowflake_to_str(row.action_role_id),
        "delay_seconds": row.delay_seconds or 0,
        "enabled": row.enabled,
    }


async def get_join(guild_id: int) -> dict:
    async with session_scope() as session:
        row = await session.get(RoleJoinConfig, guild_id)
        return _join(row, guild_id)


async def save_join(*, guild_id: int, member_role_ids: list, bot_role_ids: list, delay_seconds_value: int, screening: str) -> dict:
    if screening not in {"immediate", "screening"}:
        raise RuleError("invalid")
    try:
        delay = delay_seconds(delay_seconds_value)
    except ValueError as exc:
        raise RuleError("invalid") from exc
    async with session_scope() as session:
        row = await session.get(RoleJoinConfig, guild_id)
        if row is None:
            row = RoleJoinConfig(guild_id=guild_id)
            session.add(row)
        row.member_role_ids = _ids(member_role_ids)
        row.bot_role_ids = _ids(bot_role_ids)
        row.delay_seconds = delay
        row.screening = screening
        row.updated_at = datetime.now(timezone.utc)
        await session.flush()
        return _join(row, guild_id)


async def list_rules(guild_id: int) -> list[dict]:
    async with session_scope() as session:
        rows = (await session.execute(select(RoleAutomationRule).where(RoleAutomationRule.guild_id == guild_id).order_by(RoleAutomationRule.updated_at.desc()))).scalars().all()
        return [_rule(row) for row in rows]


async def rules_for(guild_id: int, trigger: str, role_id: int | None = None) -> list[dict]:
    async with session_scope() as session:
        query = select(RoleAutomationRule).where(RoleAutomationRule.guild_id == guild_id, RoleAutomationRule.trigger == trigger, RoleAutomationRule.enabled.is_(True))
        if trigger in {"role_add", "role_remove"}:
            query = query.where(RoleAutomationRule.trigger_role_id == int(role_id or 0))
        rows = (await session.execute(query)).scalars().all()
        return [_rule(row) for row in rows]


def _check_rule(trigger: str, action: str, action_role_id: str, trigger_role_id: str | None) -> tuple[int | None, int]:
    if trigger not in TRIGGERS or action not in ACTIONS or not str(action_role_id).isdigit():
        raise RuleError("invalid")
    trigger_role = int(trigger_role_id) if trigger_role_id and str(trigger_role_id).isdigit() else None
    if trigger in {"role_add", "role_remove"} and trigger_role is None:
        raise RuleError("Choose the role that starts this rule.")
    return trigger_role, int(action_role_id)


async def create_rule(*, guild_id: int, name: str, trigger: str, trigger_role_id: str | None, conditions: list, action: str, action_role_id: str, delay_seconds_value: int, enabled: bool = True) -> dict:
    trigger_role, action_role = _check_rule(trigger, action, action_role_id, trigger_role_id)
    try:
        delay = delay_seconds(delay_seconds_value)
    except ValueError as exc:
        raise RuleError("invalid") from exc
    now = datetime.now(timezone.utc)
    async with session_scope() as session:
        row = RoleAutomationRule(
            guild_id=guild_id,
            name=(name or "Role rule")[:80],
            trigger=trigger,
            trigger_role_id=trigger_role,
            conditions=_conditions(conditions),
            action=action,
            action_role_id=action_role,
            delay_seconds=delay,
            enabled=enabled,
            created_at=now,
            updated_at=now,
        )
        session.add(row)
        await session.flush()
        return _rule(row)


def _uuid(rule_id: str) -> uuid.UUID:
    try:
        return uuid.UUID(str(rule_id))
    except ValueError as exc:
        raise RuleError("missing") from exc


async def update_rule(*, guild_id: int, rule_id: str, **fields) -> dict:
    async with session_scope() as session:
        row = await session.get(RoleAutomationRule, _uuid(rule_id))
        if row is None or row.guild_id != guild_id:
            raise RuleError("missing")
        if "name" in fields and fields["name"] is not None:
            row.name = str(fields["name"])[:80]
        if "enabled" in fields and fields["enabled"] is not None:
            row.enabled = bool(fields["enabled"])
        trigger = fields.get("trigger") or row.trigger
        action = fields.get("action") or row.action
        action_role = fields.get("action_role_id") or str(row.action_role_id)
        trigger_role = fields.get("trigger_role_id") if "trigger_role_id" in fields else (str(row.trigger_role_id) if row.trigger_role_id else None)
        if any(key in fields for key in ("trigger", "action", "action_role_id", "trigger_role_id")):
            trigger_role_id, action_role_id = _check_rule(trigger, action, str(action_role), None if trigger_role is None else str(trigger_role))
            row.trigger = trigger
            row.action = action
            row.action_role_id = action_role_id
            row.trigger_role_id = trigger_role_id
        if "conditions" in fields and fields["conditions"] is not None:
            row.conditions = _conditions(fields["conditions"])
        if "delay_seconds" in fields and fields["delay_seconds"] is not None:
            try:
                row.delay_seconds = delay_seconds(fields["delay_seconds"])
            except ValueError as exc:
                raise RuleError("invalid") from exc
        row.updated_at = datetime.now(timezone.utc)
        await session.flush()
        return _rule(row)


async def get_rule(guild_id: int, rule_id: str) -> dict:
    async with session_scope() as session:
        row = await session.get(RoleAutomationRule, _uuid(rule_id))
        if row is None or row.guild_id != guild_id:
            raise RuleError("missing")
        return _rule(row)


async def duplicate_rule(*, guild_id: int, rule_id: str) -> dict:
    source = await get_rule(guild_id, rule_id)
    return await create_rule(
        guild_id=guild_id,
        name=f"{source['name']} copy"[:80],
        trigger=source["trigger"],
        trigger_role_id=source["trigger_role_id"],
        conditions=source["conditions"],
        action=source["action"],
        action_role_id=source["action_role_id"],
        delay_seconds_value=source["delay_seconds"],
        enabled=False,
    )


async def delete_rule(*, guild_id: int, rule_id: str) -> None:
    async with session_scope() as session:
        row = await session.get(RoleAutomationRule, _uuid(rule_id))
        if row is None or row.guild_id != guild_id:
            raise RuleError("missing")
        await session.delete(row)


def read_legacy_join(path: str) -> list[tuple[int, list[str], list[str]]]:
    try:
        uri = f"file:{Path(path).as_posix()}?mode=ro"
        with sqlite3.connect(uri, uri=True) as conn:
            rows = []
            for guild_id, bots, humans in conn.execute("SELECT guild_id, bots, humans FROM autorole"):
                rows.append((int(guild_id), _split(humans), _split(bots)))
            return rows
    except sqlite3.Error:
        return []


def _split(value: str | None) -> list[str]:
    text = str(value or "").replace("[", "").replace("]", "")
    return [item.strip() for item in text.split(",") if item.strip().isdigit()]


async def migrate_legacy(path: str) -> int:
    """Copy sqlite join roles into V2. The sqlite file is not modified."""
    created = 0
    for guild_id, humans, bots in read_legacy_join(path):
        current = await get_join(guild_id)
        if current["member_role_ids"] or current["bot_role_ids"]:
            continue
        if not humans and not bots:
            continue
        await save_join(guild_id=guild_id, member_role_ids=humans, bot_role_ids=bots, delay_seconds_value=0, screening="immediate")
        created += 1
    return created
