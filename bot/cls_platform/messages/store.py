"""Guild-scoped message templates and the sent-message registry."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import BigInteger, Boolean, DateTime, String, select
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from cls_platform.database import session_scope
from cls_platform.discord_types import snowflake_to_str
from cls_platform.messages.schema import validate_payload
from cls_platform.models import Base


class MessageError(ValueError):
    pass


class MessageTemplate(Base):
    __tablename__ = "message_templates"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    guild_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    name: Mapped[str] = mapped_column(String(80), nullable=False)
    payload: Mapped[dict] = mapped_column(JSONB, nullable=False)
    created_by: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class SentMessage(Base):
    __tablename__ = "sent_messages"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    guild_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    channel_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    message_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    template_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    payload: Mapped[dict] = mapped_column(JSONB, nullable=False)
    sent_by: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    sent_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    edited_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    missing: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _template(row: MessageTemplate) -> dict:
    return {
        "id": str(row.id),
        "guild_id": snowflake_to_str(row.guild_id),
        "name": row.name,
        "payload": row.payload,
        "created_by": snowflake_to_str(row.created_by) if row.created_by else None,
        "created_at": row.created_at.isoformat(),
        "updated_at": row.updated_at.isoformat(),
    }


def _sent(row: SentMessage) -> dict:
    return {
        "id": str(row.id),
        "guild_id": snowflake_to_str(row.guild_id),
        "channel_id": snowflake_to_str(row.channel_id),
        "message_id": snowflake_to_str(row.message_id),
        "template_id": str(row.template_id) if row.template_id else None,
        "payload": row.payload,
        "sent_by": snowflake_to_str(row.sent_by) if row.sent_by else None,
        "sent_at": row.sent_at.isoformat(),
        "edited_at": row.edited_at.isoformat() if row.edited_at else None,
        "missing": bool(row.missing),
        "jump_url": f"https://discord.com/channels/{row.guild_id}/{row.channel_id}/{row.message_id}",
    }


def _name(value: str) -> str:
    cleaned = (value or "").strip()
    if not cleaned or len(cleaned) > 80:
        raise MessageError("Template name must be 1–80 characters")
    return cleaned


async def list_templates(guild_id: int) -> list[dict]:
    async with session_scope() as session:
        rows = (
            await session.execute(
                select(MessageTemplate).where(MessageTemplate.guild_id == guild_id).order_by(MessageTemplate.updated_at.desc())
            )
        ).scalars().all()
        return [_template(row) for row in rows]


async def get_template(guild_id: int, template_id: str) -> dict:
    row = await _template_row(guild_id, template_id)
    return _template(row)


async def _template_row(guild_id: int, template_id: str) -> MessageTemplate:
    try:
        parsed = uuid.UUID(template_id)
    except ValueError as exc:
        raise MessageError("Template not found") from exc
    async with session_scope() as session:
        row = await session.get(MessageTemplate, parsed)
        if row is None or row.guild_id != guild_id:
            raise MessageError("Template not found")
        session.expunge(row)
        return row


async def create_template(*, guild_id: int, name: str, payload: dict, created_by: int | None) -> dict:
    cleaned = validate_payload(payload)
    now = _now()
    async with session_scope() as session:
        row = MessageTemplate(
            guild_id=guild_id,
            name=_name(name),
            payload=cleaned,
            created_by=created_by,
            created_at=now,
            updated_at=now,
        )
        session.add(row)
        await session.flush()
        return _template(row)


async def update_template(*, guild_id: int, template_id: str, name: str | None, payload: dict | None) -> dict:
    try:
        parsed = uuid.UUID(template_id)
    except ValueError as exc:
        raise MessageError("Template not found") from exc
    async with session_scope() as session:
        row = await session.get(MessageTemplate, parsed)
        if row is None or row.guild_id != guild_id:
            raise MessageError("Template not found")
        if name is not None:
            row.name = _name(name)
        if payload is not None:
            row.payload = validate_payload(payload)
        row.updated_at = _now()
        await session.flush()
        return _template(row)


async def delete_template(guild_id: int, template_id: str) -> None:
    try:
        parsed = uuid.UUID(template_id)
    except ValueError as exc:
        raise MessageError("Template not found") from exc
    async with session_scope() as session:
        row = await session.get(MessageTemplate, parsed)
        if row is None or row.guild_id != guild_id:
            raise MessageError("Template not found")
        await session.delete(row)


async def record_sent(
    *,
    guild_id: int,
    channel_id: int,
    message_id: int,
    template_id: str | None,
    payload: dict,
    sent_by: int | None,
) -> dict:
    parsed = None
    if template_id:
        try:
            parsed = uuid.UUID(template_id)
        except ValueError:
            parsed = None
    async with session_scope() as session:
        row = SentMessage(
            guild_id=guild_id,
            channel_id=channel_id,
            message_id=message_id,
            template_id=parsed,
            payload=payload,
            sent_by=sent_by,
            sent_at=_now(),
            missing=False,
        )
        session.add(row)
        await session.flush()
        return _sent(row)


async def list_sent(guild_id: int) -> list[dict]:
    async with session_scope() as session:
        rows = (
            await session.execute(select(SentMessage).where(SentMessage.guild_id == guild_id).order_by(SentMessage.sent_at.desc()).limit(100))
        ).scalars().all()
        return [_sent(row) for row in rows]


async def get_sent(guild_id: int, sent_id: str) -> SentMessage:
    try:
        parsed = uuid.UUID(sent_id)
    except ValueError as exc:
        raise MessageError("Sent message not found") from exc
    async with session_scope() as session:
        row = await session.get(SentMessage, parsed)
        if row is None or row.guild_id != guild_id:
            raise MessageError("Sent message not found")
        session.expunge(row)
        return row


async def mark_sent(guild_id: int, sent_id: str, *, missing: bool | None = None, payload: dict | None = None, message_id: int | None = None, channel_id: int | None = None, edited: bool = False) -> dict:
    row = await get_sent(guild_id, sent_id)
    async with session_scope() as session:
        current = await session.get(SentMessage, row.id)
        if current is None or current.guild_id != guild_id:
            raise MessageError("Sent message not found")
        if missing is not None:
            current.missing = missing
        if payload is not None:
            current.payload = payload
        if message_id is not None:
            current.message_id = message_id
        if channel_id is not None:
            current.channel_id = channel_id
        if edited:
            current.edited_at = _now()
            current.missing = False
        await session.flush()
        return _sent(current)


async def delete_sent(guild_id: int, sent_id: str) -> None:
    row = await get_sent(guild_id, sent_id)
    async with session_scope() as session:
        current = await session.get(SentMessage, row.id)
        if current is None or current.guild_id != guild_id:
            raise MessageError("Sent message not found")
        await session.delete(current)
