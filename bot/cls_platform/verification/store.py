"""Persist verification config and member state. Guild scoped."""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import BigInteger, Boolean, DateTime, Integer, String, Text, func, select
from sqlalchemy.dialects.postgresql import ARRAY, insert as pg_insert
from sqlalchemy.orm import Mapped, mapped_column

from cls_platform.database import session_scope
from cls_platform.discord_types import snowflake_to_str
from cls_platform.models import Base
from cls_platform.services.audit import record_audit
from cls_platform.verification.engine import (
    VERIFICATION_ENABLE_BLOCK,
    grace_deadline,
    plan_member,
    validate_enable,
    verification_message_reachable,
)


class VerificationConfigRow(Base):
    __tablename__ = "verification_configs"

    guild_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    unverified_role_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    verified_role_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    channel_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    method: Mapped[str] = mapped_column(String(16), nullable=False, default="button")
    grace_seconds: Mapped[int] = mapped_column(Integer, nullable=False, default=604800)
    message: Mapped[str] = mapped_column(Text, nullable=False, default="")
    protected_category_ids: Mapped[list[int]] = mapped_column(ARRAY(BigInteger), nullable=False, default=list)
    enabled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)


class VerificationMemberRow(Base):
    __tablename__ = "verification_members"

    guild_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    user_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    state: Mapped[str] = mapped_column(String(16), nullable=False)
    grace_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class VerificationOverwriteBackup(Base):
    __tablename__ = "verification_overwrite_backups"

    guild_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    category_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    role_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    had_overwrite: Mapped[bool] = mapped_column(Boolean, nullable=False)
    allow_bits: Mapped[str] = mapped_column(Text, nullable=False, default="0")
    deny_bits: Mapped[str] = mapped_column(Text, nullable=False, default="0")


def _public(row: VerificationConfigRow, counts: dict) -> dict:
    reachable = verification_message_reachable(
        published_message_id=getattr(row, "published_message_id", None),
        channel_id=row.channel_id,
    )
    return {
        "guild_id": snowflake_to_str(row.guild_id),
        "enabled": bool(row.enabled and reachable),
        "can_enable": reachable,
        "stored_enabled": bool(row.enabled),
        "unverified_role_id": snowflake_to_str(row.unverified_role_id) if row.unverified_role_id else None,
        "verified_role_id": snowflake_to_str(row.verified_role_id) if row.verified_role_id else None,
        "channel_id": snowflake_to_str(row.channel_id) if row.channel_id else None,
        "method": row.method,
        "grace_seconds": row.grace_seconds,
        "message": row.message,
        "protected_category_ids": [snowflake_to_str(item) for item in (row.protected_category_ids or [])],
        "enabled_at": row.enabled_at.isoformat() if row.enabled_at else None,
        "counts": counts,
    }


async def _counts(session, guild_id: int) -> dict:
    rows = (
        await session.execute(
            select(VerificationMemberRow.state, func.count())
            .where(VerificationMemberRow.guild_id == guild_id)
            .group_by(VerificationMemberRow.state)
        )
    ).all()
    counts = {"grace": 0, "unverified": 0, "verified": 0, "exempt": 0}
    for state, count in rows:
        if state in counts:
            counts[state] = int(count)
    return counts


async def get_config(guild_id: int) -> dict:
    async with session_scope() as session:
        row = await session.get(VerificationConfigRow, guild_id)
        if row is None:
            row = VerificationConfigRow(guild_id=guild_id, enabled=False, protected_category_ids=[])
            session.add(row)
            await session.flush()
        return _public(row, await _counts(session, guild_id))


async def save_config(*, guild_id: int, actor_id: int | None, fields: dict, gate_check: str) -> dict:
    if fields.get("enabled") is True and not verification_message_reachable(
        published_message_id=fields.get("published_message_id"),
        channel_id=fields.get("channel_id"),
    ):
        raise ValueError(VERIFICATION_ENABLE_BLOCK)
    if fields.get("enabled") and gate_check != "ok":
        raise ValueError(gate_check)
    async with session_scope() as session:
        row = await session.get(VerificationConfigRow, guild_id)
        if row is None:
            row = VerificationConfigRow(guild_id=guild_id, protected_category_ids=[])
            session.add(row)
            await session.flush()
        before = _public(row, {})
        for key in (
            "enabled",
            "unverified_role_id",
            "verified_role_id",
            "channel_id",
            "method",
            "grace_seconds",
            "message",
            "protected_category_ids",
        ):
            if key in fields and fields[key] is not None:
                setattr(row, key, fields[key])
        if fields.get("enabled") and not before["enabled"]:
            row.enabled_at = datetime.now(timezone.utc)
        if fields.get("enabled") is False:
            row.enabled_at = None
        row.version += 1
        after = _public(row, await _counts(session, guild_id))
    await record_audit(
        action="verification.config",
        actor_user_id=actor_id,
        guild_id=guild_id,
        target="verification",
        before_state=before,
        after_state=after,
    )
    return after


async def observe_member(
    *,
    guild_id: int,
    user_id: int,
    owner_id: int | None,
    root_ids: set[int],
    joined_at: datetime | None,
    now: datetime,
) -> str:
    async with session_scope() as session:
        config = await session.get(VerificationConfigRow, guild_id)
        member = await session.get(VerificationMemberRow, (guild_id, user_id))
        reachable = verification_message_reachable(
            published_message_id=getattr(config, "published_message_id", None) if config else None,
            channel_id=config.channel_id if config else None,
        )
        decision = plan_member(
            enabled=bool(config and config.enabled and reachable),
            user_id=user_id,
            owner_id=owner_id,
            root_ids=root_ids,
            joined_at=joined_at,
            enabled_at=config.enabled_at if config else None,
            state=member.state if member else None,
            grace_until=member.grace_until if member else None,
            grace_seconds=config.grace_seconds if config else 0,
            now=now,
        )
        if decision == "start_grace" and config is not None:
            until = grace_deadline(now, config.grace_seconds)
            session.add(VerificationMemberRow(guild_id=guild_id, user_id=user_id, state="grace", grace_until=until))
        elif decision == "assign_unverified":
            if member is None:
                session.add(VerificationMemberRow(guild_id=guild_id, user_id=user_id, state="unverified"))
            else:
                member.state = "unverified"
                member.grace_until = None
        elif decision == "exempt" and member is None:
            session.add(VerificationMemberRow(guild_id=guild_id, user_id=user_id, state="exempt"))
        elif decision == "verified":
            pass
        return decision


async def mark_verified(guild_id: int, user_id: int) -> None:
    async with session_scope() as session:
        member = await session.get(VerificationMemberRow, (guild_id, user_id))
        if member is None:
            session.add(VerificationMemberRow(guild_id=guild_id, user_id=user_id, state="verified"))
        else:
            member.state = "verified"
            member.grace_until = None


async def remember_overwrites(guild_id: int, backups: list[dict]) -> None:
    async with session_scope() as session:
        for item in backups:
            await session.execute(
                pg_insert(VerificationOverwriteBackup)
                .values(guild_id=guild_id, **item)
                .on_conflict_do_nothing(index_elements=["guild_id", "category_id"])
            )


async def stored_overwrites(guild_id: int) -> list[VerificationOverwriteBackup]:
    async with session_scope() as session:
        rows = (
            await session.execute(
                select(VerificationOverwriteBackup).where(VerificationOverwriteBackup.guild_id == guild_id)
            )
        ).scalars().all()
        return [
            {
                "category_id": row.category_id,
                "role_id": row.role_id,
                "had_overwrite": row.had_overwrite,
                "allow_bits": row.allow_bits,
                "deny_bits": row.deny_bits,
            }
            for row in rows
        ]


async def clear_overwrites(guild_id: int) -> None:
    async with session_scope() as session:
        rows = (
            await session.execute(
                select(VerificationOverwriteBackup).where(VerificationOverwriteBackup.guild_id == guild_id)
            )
        ).scalars().all()
        for row in rows:
            await session.delete(row)


def check_enable(role_id, categories, bot_top, role_position) -> str:
    return validate_enable(
        unverified_role_id=role_id,
        category_ids=list(categories or []),
        bot_top=bot_top,
        role_position=role_position,
    )
