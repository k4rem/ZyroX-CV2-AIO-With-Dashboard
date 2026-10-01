"""Tickets V2 persistence. No SQLite writes."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import BigInteger, Boolean, DateTime, ForeignKey, Integer, String, Text, func, select
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from cls_platform.database import session_scope
from cls_platform.discord_types import snowflake_to_str
from cls_platform.models import Base


class TicketCategory(Base):
    __tablename__ = "ticket_categories_v2"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    guild_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    name: Mapped[str] = mapped_column(String(80), nullable=False)
    discord_category_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    staff_role_ids: Mapped[list[int]] = mapped_column(ARRAY(BigInteger), nullable=False, default=list)
    name_format: Mapped[str] = mapped_column(String(80), nullable=False, default="ticket-{number}")


class TicketPanel(Base):
    __tablename__ = "ticket_panels_v2"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    guild_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    category_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("ticket_categories_v2.id"))
    channel_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    title: Mapped[str] = mapped_column(String(120), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False, default="")
    button_label: Mapped[str] = mapped_column(String(40), nullable=False, default="Open ticket")
    published_message_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)


class TicketQuestion(Base):
    __tablename__ = "ticket_questions_v2"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    panel_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("ticket_panels_v2.id"))
    label: Mapped[str] = mapped_column(String(120), nullable=False)
    kind: Mapped[str] = mapped_column(String(16), nullable=False)
    required: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    position: Mapped[int] = mapped_column(Integer, nullable=False, default=0)


class Ticket(Base):
    __tablename__ = "tickets_v2"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    guild_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    category_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("ticket_categories_v2.id"))
    number: Mapped[int] = mapped_column(Integer, nullable=False)
    opener_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    channel_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="open")
    assignee_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    close_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    opened_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    closed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class TicketEvent(Base):
    __tablename__ = "ticket_events_v2"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    ticket_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("tickets_v2.id"))
    guild_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    kind: Mapped[str] = mapped_column(String(32), nullable=False)
    actor_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    payload: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class TicketTranscript(Base):
    __tablename__ = "ticket_transcript_v2"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    ticket_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("tickets_v2.id"))
    author_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class TicketError(ValueError):
    pass


def panel_preview(title: str, message: str, button_label: str, panel_id: str) -> dict:
    return {
        "title": title,
        "message": message,
        "components": [{"type": "button", "label": button_label, "custom_id": f"cls-ticket:{panel_id}"}],
    }


def _sid(value: int | None) -> str | None:
    return snowflake_to_str(value) if value else None


async def create_category(*, guild_id: int, name: str, discord_category_id: int | None, staff_role_ids: list[int]) -> dict:
    async with session_scope() as session:
        row = TicketCategory(
            guild_id=guild_id,
            name=name,
            discord_category_id=discord_category_id,
            staff_role_ids=staff_role_ids,
        )
        session.add(row)
        await session.flush()
        return {"id": str(row.id), "name": row.name, "discord_category_id": _sid(row.discord_category_id)}


async def load_panel(panel_id: str) -> dict | None:
    async with session_scope() as session:
        panel = await session.get(TicketPanel, uuid.UUID(panel_id))
        if panel is None:
            return None
        questions = (
            await session.execute(
                select(TicketQuestion).where(TicketQuestion.panel_id == panel.id).order_by(TicketQuestion.position)
            )
        ).scalars().all()
        category = await session.get(TicketCategory, panel.category_id)
        return {
            "id": str(panel.id),
            "guild_id": panel.guild_id,
            "category_id": str(panel.category_id),
            "discord_category_id": category.discord_category_id if category else None,
            "title": panel.title,
            "button_label": panel.button_label,
            "questions": [{"label": row.label, "required": row.required} for row in questions],
            "preview": panel_preview(panel.title, panel.message, panel.button_label, str(panel.id)),
        }


async def create_panel(*, guild_id: int, category_id: str, channel_id: int | None, title: str, message: str, button_label: str, questions: list[dict]) -> dict:
    async with session_scope() as session:
        panel = TicketPanel(
            guild_id=guild_id,
            category_id=uuid.UUID(category_id),
            channel_id=channel_id,
            title=title,
            message=message,
            button_label=button_label or "Open ticket",
        )
        session.add(panel)
        await session.flush()
        for index, question in enumerate(questions):
            session.add(
                TicketQuestion(
                    panel_id=panel.id,
                    label=question["label"],
                    kind=question.get("kind") or "short",
                    required=bool(question.get("required", True)),
                    position=index,
                )
            )
        preview = panel_preview(panel.title, panel.message, panel.button_label, str(panel.id))
        return {"id": str(panel.id), "preview": preview}


async def open_ticket(*, guild_id: int, category_id: str, opener_id: int, answers: dict | None = None, channel_id: int | None = None) -> dict:
    answers = answers or {}
    async with session_scope() as session:
        category = await session.get(TicketCategory, uuid.UUID(category_id))
        if category is None or category.guild_id != guild_id:
            raise TicketError("category_missing")
        existing = (
            await session.execute(
                select(Ticket).where(
                    Ticket.guild_id == guild_id,
                    Ticket.category_id == category.id,
                    Ticket.opener_id == opener_id,
                    Ticket.status == "open",
                )
            )
        ).scalar_one_or_none()
        if existing is not None:
            raise TicketError("duplicate_open")
        number = (
            await session.execute(select(func.coalesce(func.max(Ticket.number), 0)).where(Ticket.guild_id == guild_id))
        ).scalar_one() + 1
        ticket = Ticket(
            guild_id=guild_id,
            category_id=category.id,
            number=number,
            opener_id=opener_id,
            channel_id=channel_id,
            status="open",
        )
        session.add(ticket)
        await session.flush()
        session.add(TicketEvent(ticket_id=ticket.id, guild_id=guild_id, kind="opened", actor_id=opener_id, payload=answers))
        if answers:
            session.add(TicketTranscript(ticket_id=ticket.id, author_id=opener_id, body="\n".join(f"{key}: {value}" for key, value in answers.items())))
        name = category.name_format.format(number=number)
        return {"id": str(ticket.id), "number": number, "name": name, "status": "open"}


async def claim_ticket(*, guild_id: int, ticket_id: str, actor_id: int) -> dict:
    return await _mutate(guild_id, ticket_id, actor_id, "claim")


async def close_ticket(*, guild_id: int, ticket_id: str, actor_id: int, reason: str) -> dict:
    if not reason.strip():
        raise TicketError("reason_required")
    return await _mutate(guild_id, ticket_id, actor_id, "close", reason)


async def reopen_ticket(*, guild_id: int, ticket_id: str, actor_id: int) -> dict:
    return await _mutate(guild_id, ticket_id, actor_id, "reopen")


async def add_transcript(*, guild_id: int, ticket_id: str, author_id: int, body: str) -> None:
    async with session_scope() as session:
        ticket = await session.get(Ticket, uuid.UUID(ticket_id))
        if ticket is None or ticket.guild_id != guild_id:
            raise TicketError("missing")
        session.add(TicketTranscript(ticket_id=ticket.id, author_id=author_id, body=body))


async def _mutate(guild_id: int, ticket_id: str, actor_id: int, kind: str, reason: str | None = None) -> dict:
    async with session_scope() as session:
        ticket = await session.get(Ticket, uuid.UUID(ticket_id))
        if ticket is None or ticket.guild_id != guild_id:
            raise TicketError("missing")
        if kind == "claim":
            ticket.assignee_id = actor_id
        elif kind == "close":
            if ticket.status != "open":
                raise TicketError("not_open")
            ticket.status = "closed"
            ticket.close_reason = reason
            ticket.closed_at = datetime.now(timezone.utc)
        elif kind == "reopen":
            if ticket.status != "closed":
                raise TicketError("not_closed")
            clash = (
                await session.execute(
                    select(Ticket.id).where(
                        Ticket.guild_id == guild_id,
                        Ticket.category_id == ticket.category_id,
                        Ticket.opener_id == ticket.opener_id,
                        Ticket.status == "open",
                    )
                )
            ).first()
            if clash:
                raise TicketError("duplicate_open")
            ticket.status = "open"
            ticket.closed_at = None
        session.add(TicketEvent(ticket_id=ticket.id, guild_id=guild_id, kind=kind, actor_id=actor_id, payload={"reason": reason} if reason else {}))
        return {"id": str(ticket.id), "status": ticket.status, "assignee_id": _sid(ticket.assignee_id)}


async def workspace(guild_id: int) -> dict:
    async with session_scope() as session:
        categories = (await session.execute(select(TicketCategory).where(TicketCategory.guild_id == guild_id))).scalars().all()
        panels = (await session.execute(select(TicketPanel).where(TicketPanel.guild_id == guild_id))).scalars().all()
        tickets = (
            await session.execute(select(Ticket).where(Ticket.guild_id == guild_id).order_by(Ticket.number.desc()).limit(50))
        ).scalars().all()
        open_count = (
            await session.execute(
                select(func.count()).select_from(Ticket).where(Ticket.guild_id == guild_id, Ticket.status == "open")
            )
        ).scalar_one()
        opened = (await session.execute(select(func.count()).select_from(Ticket).where(Ticket.guild_id == guild_id))).scalar_one()
        closed_count = (
            await session.execute(
                select(func.count()).select_from(Ticket).where(Ticket.guild_id == guild_id, Ticket.status == "closed")
            )
        ).scalar_one()
        return {
            "open_now": int(open_count),
            "opened": int(opened),
            "closed": int(closed_count),
            "categories": [
                {"id": str(row.id), "name": row.name, "discord_category_id": _sid(row.discord_category_id)}
                for row in categories
            ],
            "panels": [
                {"id": str(row.id), "title": row.title, "message": row.message, "button_label": row.button_label, "preview": panel_preview(row.title, row.message, row.button_label, str(row.id))}
                for row in panels
            ],
            "tickets": [
                {
                    "id": str(row.id),
                    "number": row.number,
                    "status": row.status,
                    "opener_id": snowflake_to_str(row.opener_id),
                    "assignee_id": _sid(row.assignee_id),
                    "close_reason": row.close_reason,
                }
                for row in tickets
            ],
        }


async def transcript(guild_id: int, ticket_id: str) -> dict:
    async with session_scope() as session:
        ticket = await session.get(Ticket, uuid.UUID(ticket_id))
        if ticket is None or ticket.guild_id != guild_id:
            raise TicketError("missing")
        rows = (
            await session.execute(
                select(TicketTranscript).where(TicketTranscript.ticket_id == ticket.id).order_by(TicketTranscript.created_at)
            )
        ).scalars().all()
        return {
            "id": str(ticket.id),
            "number": ticket.number,
            "status": ticket.status,
            "lines": [{"author_id": snowflake_to_str(row.author_id), "body": row.body} for row in rows],
        }
