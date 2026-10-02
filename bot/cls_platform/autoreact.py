"""Auto react rules. Matching is literal text, not regular expressions."""

from __future__ import annotations

import uuid

from sqlalchemy import BigInteger, Boolean, String, select
from sqlalchemy.dialects.postgresql import ARRAY, UUID
from sqlalchemy.orm import Mapped, mapped_column

from cls_platform.database import session_scope
from cls_platform.discord_types import snowflake_to_str
from cls_platform.models import Base

MODES = {"contains", "exact", "starts", "ends"}
SCOPES = {"all", "selected", "excluded"}


class AutoReactRule(Base):
    __tablename__ = "autoreact_rules_v2"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    guild_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    name: Mapped[str] = mapped_column(String(80), nullable=False)
    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    scope: Mapped[str] = mapped_column(String(16), nullable=False, default="all")
    channel_ids: Mapped[list[int]] = mapped_column(ARRAY(BigInteger), nullable=False, default=list)
    mode: Mapped[str] = mapped_column(String(16), nullable=False, default="contains")
    pattern: Mapped[str] = mapped_column(String(200), nullable=False, default="")
    emojis: Mapped[list[str]] = mapped_column(ARRAY(String(80)), nullable=False, default=list)


def text_matches(mode: str, pattern: str, content: str) -> bool:
    needle = pattern.strip().lower()
    if not needle:
        return False
    haystack = content.strip().lower()
    if mode == "exact":
        return haystack == needle
    if mode == "starts":
        return haystack.startswith(needle)
    if mode == "ends":
        return haystack.endswith(needle)
    return needle in haystack


def channel_matches(scope: str, channel_ids: list[int], channel_id: int) -> bool:
    selected = {int(item) for item in channel_ids}
    if scope == "selected":
        return channel_id in selected
    if scope == "excluded":
        return channel_id not in selected
    return True


def rule_health(rule: dict) -> str:
    if not rule["enabled"]:
        return "Off"
    if not str(rule["pattern"]).strip():
        return "Needs text"
    if not rule["emojis"]:
        return "Needs an emoji"
    if rule["scope"] != "all" and not rule["channel_ids"]:
        return "Needs a channel"
    return "Ready"


def _public(row: AutoReactRule) -> dict:
    payload = {
        "id": str(row.id),
        "name": row.name,
        "enabled": bool(row.enabled),
        "scope": row.scope if row.scope in SCOPES else "all",
        "channel_ids": [snowflake_to_str(item) for item in (row.channel_ids or [])],
        "mode": row.mode if row.mode in MODES else "contains",
        "pattern": row.pattern or "",
        "emojis": [str(item) for item in (row.emojis or []) if str(item).strip()],
    }
    payload["health"] = rule_health(payload)
    return payload


def _clean(data: dict, *, previous: AutoReactRule | None = None) -> dict:
    name = str(data.get("name", previous.name if previous else "")).strip()[:80]
    pattern = str(data.get("pattern", previous.pattern if previous else "")).strip()[:200]
    mode = str(data.get("mode", previous.mode if previous else "contains"))
    scope = str(data.get("scope", previous.scope if previous else "all"))
    if mode not in MODES:
        mode = "contains"
    if scope not in SCOPES:
        scope = "all"
    enabled = bool(data.get("enabled", previous.enabled if previous else True))
    channels = data.get("channel_ids", [str(item) for item in (previous.channel_ids or [])] if previous else [])
    emojis = data.get("emojis", list(previous.emojis or []) if previous else [])
    return {
        "name": name or "Untitled rule",
        "pattern": pattern,
        "mode": mode,
        "scope": scope,
        "enabled": enabled,
        "channel_ids": [int(item) for item in channels if str(item).isdigit()][:25],
        "emojis": [str(item).strip()[:80] for item in emojis if str(item).strip()][:8],
    }


async def _log(guild_id: int, actor_id: int | None, summary: str) -> None:
    try:
        from cls_platform.logging.store import record_event

        await record_event(
            guild_id=guild_id,
            category="bot_actions",
            event_type="autoreact",
            actor_id=actor_id,
            actor_confidence="certain" if actor_id else "unknown",
            metadata={"summary": summary},
        )
    except Exception:
        pass


async def list_rules(guild_id: int) -> list[dict]:
    async with session_scope() as session:
        rows = (
            await session.execute(select(AutoReactRule).where(AutoReactRule.guild_id == guild_id).order_by(AutoReactRule.name))
        ).scalars().all()
        return [_public(row) for row in rows]


async def matching_rules(guild_id: int, content: str, channel_id: int) -> list[dict]:
    rules = await list_rules(guild_id)
    return [
        rule
        for rule in rules
        if rule["enabled"] and channel_matches(rule["scope"], [int(item) for item in rule["channel_ids"]], channel_id) and text_matches(rule["mode"], rule["pattern"], content)
    ]


async def create_rule(guild_id: int, data: dict, *, actor_id: int | None = None) -> dict:
    cleaned = _clean(data)
    async with session_scope() as session:
        row = AutoReactRule(guild_id=guild_id, **cleaned)
        session.add(row)
        await session.flush()
        payload = _public(row)
    await _log(guild_id, actor_id, f"Auto react rule created: {payload['name']}")
    return payload


async def update_rule(guild_id: int, rule_id: str, data: dict, *, actor_id: int | None = None) -> dict:
    async with session_scope() as session:
        row = await session.get(AutoReactRule, uuid.UUID(rule_id))
        if row is None or row.guild_id != guild_id:
            raise ValueError("missing")
        cleaned = _clean(data, previous=row)
        for key, value in cleaned.items():
            setattr(row, key, value)
        payload = _public(row)
    await _log(guild_id, actor_id, f"Auto react rule updated: {payload['name']}")
    return payload


async def duplicate_rule(guild_id: int, rule_id: str, *, actor_id: int | None = None) -> dict:
    async with session_scope() as session:
        row = await session.get(AutoReactRule, uuid.UUID(rule_id))
        if row is None or row.guild_id != guild_id:
            raise ValueError("missing")
        copy = AutoReactRule(
            guild_id=guild_id,
            name=f"{row.name} copy"[:80],
            enabled=row.enabled,
            scope=row.scope,
            channel_ids=list(row.channel_ids or []),
            mode=row.mode,
            pattern=row.pattern,
            emojis=list(row.emojis or []),
        )
        session.add(copy)
        await session.flush()
        payload = _public(copy)
    await _log(guild_id, actor_id, f"Auto react rule duplicated: {payload['name']}")
    return payload


async def delete_rule(guild_id: int, rule_id: str, *, actor_id: int | None = None) -> None:
    async with session_scope() as session:
        row = await session.get(AutoReactRule, uuid.UUID(rule_id))
        if row is None or row.guild_id != guild_id:
            raise ValueError("missing")
        name = row.name
        await session.delete(row)
    await _log(guild_id, actor_id, f"Auto react rule deleted: {name}")
