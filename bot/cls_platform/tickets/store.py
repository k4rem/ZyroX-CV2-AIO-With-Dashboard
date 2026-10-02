"""Tickets V2 persistence. No SQLite writes."""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy import BigInteger, Boolean, DateTime, ForeignKey, Integer, String, Text, func, select, update
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
    ping_staff: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    required_role_ids: Mapped[list[int]] = mapped_column(ARRAY(BigInteger), nullable=False, default=list)
    blocked_role_ids: Mapped[list[int]] = mapped_column(ARRAY(BigInteger), nullable=False, default=list)


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
    payload: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    required_role_ids: Mapped[list[int]] = mapped_column(ARRAY(BigInteger), nullable=False, default=list)
    blocked_role_ids: Mapped[list[int]] = mapped_column(ARRAY(BigInteger), nullable=False, default=list)
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    publish_status: Mapped[str] = mapped_column(String(16), nullable=False, default="draft")
    button_emoji: Mapped[str] = mapped_column(String(80), nullable=False, default="")
    button_style: Mapped[str] = mapped_column(String(16), nullable=False, default="primary")
    updated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class TicketQuestion(Base):
    __tablename__ = "ticket_questions_v2"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    panel_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("ticket_panels_v2.id"))
    label: Mapped[str] = mapped_column(String(120), nullable=False)
    kind: Mapped[str] = mapped_column(String(16), nullable=False)
    required: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    position: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    placeholder: Mapped[str] = mapped_column(Text, nullable=False, default="")
    min_length: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    max_length: Mapped[int] = mapped_column(Integer, nullable=False, default=1000)


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
    closed_by: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    control_message_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    panel_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    last_activity_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    activity_generation: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    degraded: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    opener_name: Mapped[str] = mapped_column(Text, nullable=False, default="")
    opener_avatar: Mapped[str] = mapped_column(Text, nullable=False, default="")


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


class TicketSettings(Base):
    __tablename__ = "ticket_settings_v2"

    guild_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    cooldown_seconds: Mapped[int] = mapped_column(Integer, nullable=False, default=60)
    max_open: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    auto_close_hours: Mapped[int | None] = mapped_column(Integer, nullable=True)
    grace_minutes: Mapped[int] = mapped_column(Integer, nullable=False, default=60)
    transcript_channel_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    name_format: Mapped[str] = mapped_column(String(80), nullable=False, default="ticket-{number}-{username}")


class TicketBlacklist(Base):
    __tablename__ = "ticket_blacklist_v2"

    guild_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    user_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    reason: Mapped[str] = mapped_column(Text, nullable=False, default="")
    actor_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)


class TicketParticipant(Base):
    __tablename__ = "ticket_participants_v2"

    ticket_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("tickets_v2.id"), primary_key=True)
    user_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    added_by: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class TicketMessage(Base):
    __tablename__ = "ticket_messages_v2"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    ticket_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("tickets_v2.id"))
    guild_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    message_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    author_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    author_name: Mapped[str] = mapped_column(Text, nullable=False, default="")
    display_name: Mapped[str] = mapped_column(Text, nullable=False, default="")
    avatar: Mapped[str] = mapped_column(Text, nullable=False, default="")
    content: Mapped[str] = mapped_column(Text, nullable=False, default="")
    attachments: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    embeds: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    reference_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class TicketHtml(Base):
    __tablename__ = "ticket_html_v2"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    ticket_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("tickets_v2.id"))
    guild_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    html: Mapped[str] = mapped_column(Text, nullable=False)
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


async def create_category(*, guild_id: int, name: str, discord_category_id: int | None, staff_role_ids: list[int], name_format: str | None = None, ping_staff: bool = True, required_role_ids: list[int] | None = None, blocked_role_ids: list[int] | None = None) -> dict:
    async with session_scope() as session:
        row = TicketCategory(
            guild_id=guild_id,
            name=name[:80],
            discord_category_id=discord_category_id,
            staff_role_ids=staff_role_ids,
            name_format=(name_format or "ticket-{number}")[:80],
            ping_staff=ping_staff,
            required_role_ids=required_role_ids or [],
            blocked_role_ids=blocked_role_ids or [],
        )
        session.add(row)
        await session.flush()
        return _category_dict(row)


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
            "message": panel.message,
            "button_label": panel.button_label,
            "questions": [_question_dict(row) for row in questions],
            "staff_role_ids": [int(item) for item in (category.staff_role_ids or [])] if category else [],
            "ping_staff": bool(category.ping_staff) if category else True,
            "name_format": category.name_format if category else "ticket-{number}",
            "category_name": category.name if category else "",
            "required_role_ids": [int(item) for item in (panel.required_role_ids or [])],
            "blocked_role_ids": [int(item) for item in (panel.blocked_role_ids or [])],
            "channel_id": panel.channel_id,
            "payload": panel.payload,
            "published_message_id": panel.published_message_id,
            "publish_status": panel.publish_status,
            "button_emoji": panel.button_emoji or "",
            "button_style": panel.button_style or "primary",
            "published_at": panel.published_at.isoformat() if panel.published_at else None,
            "updated_at": panel.updated_at.isoformat() if panel.updated_at else None,
            "preview": panel_preview(panel.title, panel.message, panel.button_label, str(panel.id)),
        }


def _question_dict(row: TicketQuestion) -> dict:
    kind = row.kind if row.kind in {"short", "paragraph"} else "paragraph" if row.kind in {"long", "paragraph"} else "short"
    if row.kind in {"long", "paragraph"}:
        kind = "paragraph"
    return {
        "id": str(row.id),
        "label": row.label,
        "kind": kind,
        "required": row.required,
        "placeholder": row.placeholder or "",
        "min_length": row.min_length or 0,
        "max_length": row.max_length or 1000,
    }


def _category_dict(row: TicketCategory) -> dict:
    return {
        "id": str(row.id),
        "name": row.name,
        "discord_category_id": _sid(row.discord_category_id),
        "staff_role_ids": [snowflake_to_str(item) for item in (row.staff_role_ids or [])],
        "name_format": row.name_format,
        "ping_staff": row.ping_staff,
        "required_role_ids": [snowflake_to_str(item) for item in (row.required_role_ids or [])],
        "blocked_role_ids": [snowflake_to_str(item) for item in (row.blocked_role_ids or [])],
    }


async def create_panel(*, guild_id: int, category_id: str, channel_id: int | None, title: str, message: str, button_label: str, questions: list[dict], required_role_ids: list[int] | None = None, blocked_role_ids: list[int] | None = None, payload: dict | None = None, button_emoji: str = "", button_style: str = "primary") -> dict:
    async with session_scope() as session:
        panel = TicketPanel(
            guild_id=guild_id,
            category_id=uuid.UUID(category_id),
            channel_id=channel_id,
            title=title,
            message=message,
            button_label=button_label or "Open ticket",
            required_role_ids=required_role_ids or [],
            blocked_role_ids=blocked_role_ids or [],
            payload=payload,
            button_emoji=(button_emoji or "")[:80],
            button_style=button_style if button_style in {"primary", "secondary", "success", "danger"} else "primary",
            updated_at=datetime.now(timezone.utc),
        )
        session.add(panel)
        await session.flush()
        for index, question in enumerate(questions):
            session.add(
                TicketQuestion(
                    panel_id=panel.id,
                    label=question["label"],
                    kind="paragraph" if question.get("kind") in {"long", "paragraph"} else "short",
                    required=bool(question.get("required", True)),
                    position=index,
                    placeholder=str(question.get("placeholder") or "")[:100],
                    min_length=max(0, int(question.get("min_length") or 0)),
                    max_length=min(4000, max(1, int(question.get("max_length") or 1000))),
                )
            )
        preview = panel_preview(panel.title, panel.message, panel.button_label, str(panel.id))
        return {"id": str(panel.id), "preview": preview}


async def set_limits(*, guild_id: int, cooldown_seconds: int, max_open: int, auto_close_hours: int | None = None, grace_minutes: int | None = None, transcript_channel_id: int | None = None, name_format: str | None = None) -> dict:
    if cooldown_seconds < 0 or cooldown_seconds > 86400 or max_open < 1 or max_open > 10:
        raise TicketError("invalid_limits")
    if auto_close_hours is not None and not 0 <= auto_close_hours <= 720:
        raise TicketError("invalid_limits")
    if grace_minutes is not None and not 1 <= grace_minutes <= 10080:
        raise TicketError("invalid_limits")
    async with session_scope() as session:
        row = await session.get(TicketSettings, guild_id)
        if row is None:
            row = TicketSettings(guild_id=guild_id)
            session.add(row)
        row.cooldown_seconds = cooldown_seconds
        row.max_open = max_open
        if auto_close_hours is not None or auto_close_hours == 0:
            row.auto_close_hours = auto_close_hours or None
        if grace_minutes is not None:
            row.grace_minutes = grace_minutes
        if transcript_channel_id is not None:
            row.transcript_channel_id = transcript_channel_id or None
        if name_format is not None:
            row.name_format = (name_format or "ticket-{number}-{username}")[:80]
        return {
            "cooldown_seconds": row.cooldown_seconds,
            "max_open": row.max_open,
            "auto_close_hours": row.auto_close_hours,
            "grace_minutes": row.grace_minutes,
            "transcript_channel_id": _sid(row.transcript_channel_id),
            "name_format": row.name_format,
        }


async def blacklist_user(*, guild_id: int, user_id: int, reason: str = "", actor_id: int | None = None, display_name: str = "", avatar: str = "") -> dict:
    async with session_scope() as session:
        existing = await session.get(TicketBlacklist, (guild_id, user_id))
        if existing is None:
            existing = TicketBlacklist(guild_id=guild_id, user_id=user_id)
            session.add(existing)
        if reason:
            existing.reason = reason[:300]
        if actor_id:
            existing.actor_id = actor_id
        return {
            "user_id": snowflake_to_str(user_id),
            "display_name": display_name,
            "avatar": avatar,
            "reason": existing.reason or "",
            "actor_id": _sid(existing.actor_id),
            "created_at": existing.created_at.isoformat() if existing.created_at else None,
        }


async def unblacklist_user(*, guild_id: int, user_id: int) -> None:
    async with session_scope() as session:
        row = await session.get(TicketBlacklist, (guild_id, user_id))
        if row is not None:
            await session.delete(row)


async def open_ticket(*, guild_id: int, category_id: str, opener_id: int, answers: dict | None = None, channel_id: int | None = None, opener_name: str = "", opener_avatar: str = "", panel_id: str | None = None, member_role_ids: list[int] | None = None) -> dict:
    answers = answers or {}
    async with session_scope() as session:
        category = await session.get(TicketCategory, uuid.UUID(category_id))
        if category is None or category.guild_id != guild_id:
            raise TicketError("category_missing")
        blocked = await session.get(TicketBlacklist, (guild_id, opener_id))
        if blocked is not None:
            raise TicketError("blacklisted")
        if panel_id and member_role_ids is not None:
            panel = await session.get(TicketPanel, uuid.UUID(panel_id))
            if panel is not None:
                required = {int(item) for item in (panel.required_role_ids or [])}
                blocked_roles = {int(item) for item in (panel.blocked_role_ids or [])}
                held = {int(item) for item in member_role_ids}
                if required and not required.intersection(held):
                    raise TicketError("required_role")
                if blocked_roles.intersection(held):
                    raise TicketError("blocked_role")
        if member_role_ids is not None:
            required = {int(item) for item in (category.required_role_ids or [])}
            blocked_roles = {int(item) for item in (category.blocked_role_ids or [])}
            held = {int(item) for item in member_role_ids}
            if required and not required.intersection(held):
                raise TicketError("required_role")
            if blocked_roles.intersection(held):
                raise TicketError("blocked_role")
        settings = await session.get(TicketSettings, guild_id)
        cooldown_seconds = settings.cooldown_seconds if settings else 60
        max_open = settings.max_open if settings else 1
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
        open_count = (
            await session.execute(
                select(func.count()).select_from(Ticket).where(
                    Ticket.guild_id == guild_id,
                    Ticket.opener_id == opener_id,
                    Ticket.status == "open",
                )
            )
        ).scalar_one()
        if int(open_count) >= max_open:
            raise TicketError("max_open")
        if cooldown_seconds > 0:
            last_opened = (
                await session.execute(
                    select(func.max(Ticket.opened_at)).where(Ticket.guild_id == guild_id, Ticket.opener_id == opener_id)
                )
            ).scalar_one()
            if last_opened is not None and datetime.now(timezone.utc) - last_opened < timedelta(seconds=cooldown_seconds):
                raise TicketError("cooldown")
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
            panel_id=uuid.UUID(panel_id) if panel_id else None,
            last_activity_at=datetime.now(timezone.utc),
            opener_name=(opener_name or "")[:80],
            opener_avatar=(opener_avatar or "")[:300],
        )
        session.add(ticket)
        await session.flush()
        session.add(TicketEvent(ticket_id=ticket.id, guild_id=guild_id, kind="opened", actor_id=opener_id, payload=answers))
        if answers:
            session.add(TicketTranscript(ticket_id=ticket.id, author_id=opener_id, body="\n".join(f"{key}: {value}" for key, value in answers.items())))
        from cls_platform.tickets.naming import channel_name

        name = channel_name(category.name_format, number, opener_name)
        return {
            "id": str(ticket.id),
            "number": number,
            "name": name,
            "status": "open",
            "staff_role_ids": [int(item) for item in (category.staff_role_ids or [])],
            "ping_staff": category.ping_staff,
            "discord_category_id": category.discord_category_id,
            "category_name": category.name,
        }


async def claim_ticket(*, guild_id: int, ticket_id: str, actor_id: int) -> dict:
    return await _mutate(guild_id, ticket_id, actor_id, "claim")


async def unclaim_ticket(*, guild_id: int, ticket_id: str, actor_id: int) -> dict:
    return await _mutate(guild_id, ticket_id, actor_id, "unclaim")


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
            if ticket.status != "open":
                raise TicketError("not_open")
            result = await session.execute(
                update(Ticket)
                .where(Ticket.id == ticket.id, Ticket.status == "open", Ticket.assignee_id.is_(None))
                .values(assignee_id=actor_id)
            )
            if result.rowcount == 0:
                await session.refresh(ticket)
                if ticket.assignee_id != actor_id:
                    raise TicketError("already_claimed")
            else:
                ticket.assignee_id = actor_id
        elif kind == "unclaim":
            if ticket.status != "open":
                raise TicketError("not_open")
            ticket.assignee_id = None
        elif kind == "close":
            if ticket.status != "open":
                raise TicketError("not_open")
            ticket.status = "closed"
            ticket.close_reason = reason
            ticket.closed_at = datetime.now(timezone.utc)
            ticket.closed_by = actor_id
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
        event_kind = {"claim": "claimed", "unclaim": "unclaimed", "close": "closed", "reopen": "reopened"}.get(kind, kind)
        session.add(TicketEvent(ticket_id=ticket.id, guild_id=guild_id, kind=event_kind, actor_id=actor_id, payload={"reason": reason} if reason else {}))
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
        settings = await session.get(TicketSettings, guild_id)
        blocked = (await session.execute(select(TicketBlacklist.user_id).where(TicketBlacklist.guild_id == guild_id))).scalars().all()
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
            "cooldown_seconds": settings.cooldown_seconds if settings else 60,
            "max_open": settings.max_open if settings else 1,
            "blacklist": [snowflake_to_str(user_id) for user_id in blocked],
            "categories": [_category_dict(row) for row in categories],
            "panels": [
                {
                    "id": str(row.id),
                    "title": row.title,
                    "message": row.message,
                    "button_label": row.button_label,
                    "category_id": str(row.category_id),
                    "channel_id": _sid(row.channel_id),
                    "published_message_id": _sid(row.published_message_id),
                    "publish_status": row.publish_status,
                    "published_at": row.published_at.isoformat() if row.published_at else None,
                    "updated_at": row.updated_at.isoformat() if row.updated_at else None,
                    "required_role_ids": [snowflake_to_str(item) for item in (row.required_role_ids or [])],
                    "blocked_role_ids": [snowflake_to_str(item) for item in (row.blocked_role_ids or [])],
                    "preview": panel_preview(row.title, row.message, row.button_label, str(row.id)),
                }
                for row in panels
            ],
            "auto_close_hours": settings.auto_close_hours if settings else None,
            "grace_minutes": settings.grace_minutes if settings else 60,
            "transcript_channel_id": _sid(settings.transcript_channel_id) if settings else None,
            "name_format": settings.name_format if settings else "ticket-{number}-{username}",
            "degraded_open": int((
                await session.execute(
                    select(func.count()).select_from(Ticket).where(Ticket.guild_id == guild_id, Ticket.status == "error")
                )
            ).scalar_one()),
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
        messages = (
            await session.execute(
                select(TicketMessage).where(TicketMessage.ticket_id == ticket.id).order_by(TicketMessage.created_at)
            )
        ).scalars().all()
        html_row = (
            await session.execute(
                select(TicketHtml).where(TicketHtml.ticket_id == ticket.id).order_by(TicketHtml.created_at.desc())
            )
        ).scalars().first()
        return {
            "id": str(ticket.id),
            "number": ticket.number,
            "status": ticket.status,
            "close_reason": ticket.close_reason,
            "lines": [{"author_id": snowflake_to_str(row.author_id), "body": row.body} for row in rows],
            "messages": [
                {
                    "message_id": snowflake_to_str(row.message_id),
                    "author_id": snowflake_to_str(row.author_id),
                    "display_name": row.display_name,
                    "avatar": row.avatar,
                    "content": row.content,
                    "created_at": row.created_at,
                    "attachments": row.attachments,
                    "embeds": row.embeds,
                    "reference_id": _sid(row.reference_id),
                }
                for row in messages
            ],
            "html": html_row.html if html_row else None,
        }


async def record_event(*, guild_id: int, ticket_id: str, kind: str, actor_id: int | None, payload: dict | None = None) -> None:
    async with session_scope() as session:
        ticket = await session.get(Ticket, uuid.UUID(ticket_id))
        if ticket is None or ticket.guild_id != guild_id:
            raise TicketError("missing")
        session.add(TicketEvent(ticket_id=ticket.id, guild_id=guild_id, kind=kind, actor_id=actor_id, payload=payload or {}))


async def bind_channel(*, guild_id: int, ticket_id: str, channel_id: int, control_message_id: int | None) -> None:
    async with session_scope() as session:
        ticket = await session.get(Ticket, uuid.UUID(ticket_id))
        if ticket is None or ticket.guild_id != guild_id:
            raise TicketError("missing")
        ticket.channel_id = channel_id
        ticket.control_message_id = control_message_id
        ticket.degraded = False
        ticket.status = "open"


async def mark_degraded(*, guild_id: int, ticket_id: str, reason: str) -> None:
    async with session_scope() as session:
        ticket = await session.get(Ticket, uuid.UUID(ticket_id))
        if ticket is None or ticket.guild_id != guild_id:
            return
        ticket.degraded = True
        ticket.status = "error"
        session.add(TicketEvent(ticket_id=ticket.id, guild_id=guild_id, kind="channel_failed", actor_id=None, payload={"reason": reason[:200]}))


async def ticket_by_channel(guild_id: int, channel_id: int) -> dict | None:
    async with session_scope() as session:
        ticket = (
            await session.execute(select(Ticket).where(Ticket.guild_id == guild_id, Ticket.channel_id == channel_id))
        ).scalar_one_or_none()
        if ticket is None:
            return None
        return {
            "id": str(ticket.id),
            "status": ticket.status,
            "number": ticket.number,
            "opener_id": ticket.opener_id,
            "generation": ticket.activity_generation,
        }


async def capture_message(*, guild_id: int, channel_id: int, message_id: int, author_id: int, author_name: str, display_name: str, avatar: str, content: str, attachments: list, embeds: list, reference_id: int | None, created_at: datetime, record_activity: bool = True) -> str | None:
    async with session_scope() as session:
        ticket = (
            await session.execute(
                select(Ticket).where(Ticket.guild_id == guild_id, Ticket.channel_id == channel_id, Ticket.status == "open")
            )
        ).scalar_one_or_none()
        if ticket is None:
            return None
        existing = (
            await session.execute(
                select(TicketMessage).where(TicketMessage.guild_id == guild_id, TicketMessage.message_id == message_id)
            )
        ).scalar_one_or_none()
        if existing is None:
            session.add(
                TicketMessage(
                    ticket_id=ticket.id,
                    guild_id=guild_id,
                    message_id=message_id,
                    author_id=author_id,
                    author_name=author_name[:80],
                    display_name=display_name[:80],
                    avatar=avatar[:300],
                    content=content[:4000],
                    attachments=attachments[:10],
                    embeds=embeds[:10],
                    reference_id=reference_id,
                    created_at=created_at,
                )
            )
        if record_activity:
            ticket.last_activity_at = created_at
            ticket.activity_generation = int(ticket.activity_generation or 0) + 1
        return str(ticket.id)


async def add_participant(*, guild_id: int, ticket_id: str, user_id: int, actor_id: int) -> dict:
    async with session_scope() as session:
        ticket = await session.get(Ticket, uuid.UUID(ticket_id))
        if ticket is None or ticket.guild_id != guild_id or ticket.status != "open":
            raise TicketError("not_open")
        if user_id == ticket.opener_id:
            raise TicketError("is_opener")
        row = await session.get(TicketParticipant, (ticket.id, user_id))
        if row is None:
            session.add(TicketParticipant(ticket_id=ticket.id, user_id=user_id, added_by=actor_id))
        session.add(TicketEvent(ticket_id=ticket.id, guild_id=guild_id, kind="member_added", actor_id=actor_id, payload={"user_id": user_id}))
        return {"user_id": snowflake_to_str(user_id)}


async def remove_participant(*, guild_id: int, ticket_id: str, user_id: int, actor_id: int) -> dict:
    async with session_scope() as session:
        ticket = await session.get(Ticket, uuid.UUID(ticket_id))
        if ticket is None or ticket.guild_id != guild_id or ticket.status != "open":
            raise TicketError("not_open")
        if user_id == ticket.opener_id:
            raise TicketError("is_opener")
        row = await session.get(TicketParticipant, (ticket.id, user_id))
        if row is not None:
            await session.delete(row)
        session.add(TicketEvent(ticket_id=ticket.id, guild_id=guild_id, kind="member_removed", actor_id=actor_id, payload={"user_id": user_id}))
        return {"user_id": snowflake_to_str(user_id)}


async def transfer_ticket(*, guild_id: int, ticket_id: str, category_id: str, actor_id: int) -> dict:
    async with session_scope() as session:
        ticket = await session.get(Ticket, uuid.UUID(ticket_id))
        category = await session.get(TicketCategory, uuid.UUID(category_id))
        if ticket is None or ticket.guild_id != guild_id or ticket.status != "open":
            raise TicketError("not_open")
        if category is None or category.guild_id != guild_id:
            raise TicketError("category_missing")
        previous = await session.get(TicketCategory, ticket.category_id)
        ticket.category_id = category.id
        session.add(
            TicketEvent(
                ticket_id=ticket.id,
                guild_id=guild_id,
                kind="transferred",
                actor_id=actor_id,
                payload={"from": previous.name if previous else "", "to": category.name},
            )
        )
        extras = (
            await session.execute(select(TicketParticipant.user_id).where(TicketParticipant.ticket_id == ticket.id))
        ).scalars().all()
        return {
            "id": str(ticket.id),
            "opener_id": ticket.opener_id,
            "channel_id": ticket.channel_id,
            "category_name": category.name,
            "discord_category_id": category.discord_category_id,
            "staff_role_ids": [int(item) for item in (category.staff_role_ids or [])],
            "previous_staff_role_ids": [int(item) for item in (previous.staff_role_ids or [])] if previous else [],
            "participants": [int(item) for item in extras],
            "ping_staff": category.ping_staff,
        }


async def participants(guild_id: int, ticket_id: str) -> list[int]:
    async with session_scope() as session:
        ticket = await session.get(Ticket, uuid.UUID(ticket_id))
        if ticket is None or ticket.guild_id != guild_id:
            return []
        rows = (
            await session.execute(select(TicketParticipant.user_id).where(TicketParticipant.ticket_id == ticket.id))
        ).scalars().all()
        return [int(item) for item in rows]


async def load_ticket(guild_id: int, ticket_id: str) -> dict | None:
    async with session_scope() as session:
        ticket = await session.get(Ticket, uuid.UUID(ticket_id))
        if ticket is None or ticket.guild_id != guild_id:
            return None
        category = await session.get(TicketCategory, ticket.category_id)
        return {
            "id": str(ticket.id),
            "number": ticket.number,
            "status": ticket.status,
            "opener_id": ticket.opener_id,
            "assignee_id": ticket.assignee_id,
            "channel_id": ticket.channel_id,
            "control_message_id": ticket.control_message_id,
            "category_id": str(ticket.category_id),
            "category_name": category.name if category else "",
            "staff_role_ids": [int(item) for item in (category.staff_role_ids or [])] if category else [],
            "discord_category_id": category.discord_category_id if category else None,
            "close_reason": ticket.close_reason,
            "degraded": ticket.degraded,
            "generation": ticket.activity_generation,
            "opened_at": ticket.opened_at,
        }


async def save_html(*, guild_id: int, ticket_id: str, html: str, actor_id: int | None) -> None:
    async with session_scope() as session:
        ticket = await session.get(Ticket, uuid.UUID(ticket_id))
        if ticket is None or ticket.guild_id != guild_id:
            raise TicketError("missing")
        session.add(TicketHtml(ticket_id=ticket.id, guild_id=guild_id, html=html))
        session.add(TicketEvent(ticket_id=ticket.id, guild_id=guild_id, kind="transcript_generated", actor_id=actor_id, payload={}))


async def mark_deleted(*, guild_id: int, ticket_id: str, actor_id: int) -> dict | None:
    async with session_scope() as session:
        ticket = await session.get(Ticket, uuid.UUID(ticket_id))
        if ticket is None or ticket.guild_id != guild_id:
            raise TicketError("missing")
        channel_id = ticket.channel_id
        ticket.status = "deleted"
        ticket.channel_id = None
        session.add(TicketEvent(ticket_id=ticket.id, guild_id=guild_id, kind="deleted", actor_id=actor_id, payload={}))
        return {"channel_id": channel_id}


async def set_publish(*, guild_id: int, panel_id: str, channel_id: int | None, message_id: int | None, status: str) -> dict:
    async with session_scope() as session:
        panel = await session.get(TicketPanel, uuid.UUID(panel_id))
        if panel is None or panel.guild_id != guild_id:
            raise TicketError("missing")
        if channel_id is not None:
            panel.channel_id = channel_id
        panel.published_message_id = message_id
        panel.publish_status = status
        panel.published_at = datetime.now(timezone.utc) if status == "published" else panel.published_at
        return {"channel_id": _sid(panel.channel_id), "published_message_id": _sid(panel.published_message_id), "publish_status": panel.publish_status}


async def update_panel_text(*, guild_id: int, panel_id: str, title: str | None, message: str | None, payload: dict | None) -> dict:
    async with session_scope() as session:
        panel = await session.get(TicketPanel, uuid.UUID(panel_id))
        if panel is None or panel.guild_id != guild_id:
            raise TicketError("missing")
        if title is not None:
            panel.title = title[:120]
        if message is not None:
            panel.message = message
        if payload is not None:
            panel.payload = payload
        panel.updated_at = datetime.now(timezone.utc)
        return {"id": str(panel.id), "title": panel.title, "message": panel.message}


async def guild_settings(guild_id: int) -> dict:
    async with session_scope() as session:
        row = await session.get(TicketSettings, guild_id)
        return {
            "auto_close_hours": row.auto_close_hours if row else None,
            "grace_minutes": row.grace_minutes if row else 60,
            "transcript_channel_id": row.transcript_channel_id if row else None,
            "name_format": row.name_format if row else "ticket-{number}-{username}",
        }


async def bump_generation(guild_id: int, ticket_id: str) -> int:
    async with session_scope() as session:
        ticket = await session.get(Ticket, uuid.UUID(ticket_id))
        if ticket is None or ticket.guild_id != guild_id:
            return 0
        ticket.activity_generation = int(ticket.activity_generation or 0) + 1
        ticket.last_activity_at = datetime.now(timezone.utc)
        return ticket.activity_generation


def _style(value: str) -> str:
    return value if value in {"primary", "secondary", "success", "danger"} else "primary"


def _questions(panel_id, questions: list[dict]) -> list[TicketQuestion]:
    rows = []
    for index, question in enumerate((questions or [])[:5]):
        rows.append(
            TicketQuestion(
                panel_id=panel_id,
                label=str(question.get("label") or "Question")[:45],
                kind="paragraph" if question.get("kind") in {"long", "paragraph"} else "short",
                required=bool(question.get("required", True)),
                position=index,
                placeholder=str(question.get("placeholder") or "")[:100],
                min_length=max(0, int(question.get("min_length") or 0)),
                max_length=min(4000, max(1, int(question.get("max_length") or 1000))),
            )
        )
    return rows


async def update_category(*, guild_id: int, category_id: str, name: str | None = None, discord_category_id: int | None = None, staff_role_ids: list[int] | None = None, name_format: str | None = None, ping_staff: bool | None = None, required_role_ids: list[int] | None = None, blocked_role_ids: list[int] | None = None, discord_category_set: bool = False) -> dict:
    async with session_scope() as session:
        row = await session.get(TicketCategory, uuid.UUID(category_id))
        if row is None or row.guild_id != guild_id:
            raise TicketError("missing")
        if name is not None:
            row.name = name[:80]
        if discord_category_set:
            row.discord_category_id = discord_category_id
        if staff_role_ids is not None:
            row.staff_role_ids = staff_role_ids
        if name_format is not None:
            row.name_format = name_format[:80]
        if ping_staff is not None:
            row.ping_staff = ping_staff
        if required_role_ids is not None:
            row.required_role_ids = required_role_ids
        if blocked_role_ids is not None:
            row.blocked_role_ids = blocked_role_ids
        return _category_dict(row)


async def save_panel(*, guild_id: int, panel_id: str, category_id: str | None, channel_id: int | None, title: str | None, message: str | None, button_label: str | None, button_emoji: str | None, button_style: str | None, questions: list[dict] | None, required_role_ids: list[int] | None, blocked_role_ids: list[int] | None, payload: dict | None, channel_set: bool = False) -> dict:
    async with session_scope() as session:
        panel = await session.get(TicketPanel, uuid.UUID(panel_id))
        if panel is None or panel.guild_id != guild_id:
            raise TicketError("missing")
        if category_id:
            category = await session.get(TicketCategory, uuid.UUID(category_id))
            if category is None or category.guild_id != guild_id:
                raise TicketError("category_missing")
            panel.category_id = category.id
        if channel_set:
            panel.channel_id = channel_id
        if title is not None:
            panel.title = title[:120]
        if message is not None:
            panel.message = message
        if button_label is not None:
            panel.button_label = (button_label or "Open ticket")[:40]
        if button_emoji is not None:
            panel.button_emoji = button_emoji[:80]
        if button_style is not None:
            panel.button_style = _style(button_style)
        if required_role_ids is not None:
            panel.required_role_ids = required_role_ids
        if blocked_role_ids is not None:
            panel.blocked_role_ids = blocked_role_ids
        if payload is not None:
            panel.payload = payload
        if questions is not None:
            existing = (await session.execute(select(TicketQuestion).where(TicketQuestion.panel_id == panel.id))).scalars().all()
            for row in existing:
                await session.delete(row)
            for row in _questions(panel.id, questions):
                session.add(row)
        panel.updated_at = datetime.now(timezone.utc)
        return {"id": str(panel.id)}


async def duplicate_panel(*, guild_id: int, panel_id: str) -> dict:
    source = await load_panel(panel_id)
    if source is None or source["guild_id"] != guild_id:
        raise TicketError("missing")
    return await create_panel(
        guild_id=guild_id,
        category_id=source["category_id"],
        channel_id=source.get("channel_id"),
        title=f"{source['title']} copy"[:120],
        message=source.get("message") or "",
        button_label=source.get("button_label") or "Open ticket",
        button_emoji=source.get("button_emoji") or "",
        button_style=source.get("button_style") or "primary",
        questions=source.get("questions") or [],
        required_role_ids=source.get("required_role_ids") or [],
        blocked_role_ids=source.get("blocked_role_ids") or [],
        payload=source.get("payload"),
    )


async def delete_panel(*, guild_id: int, panel_id: str) -> dict:
    async with session_scope() as session:
        panel = await session.get(TicketPanel, uuid.UUID(panel_id))
        if panel is None or panel.guild_id != guild_id:
            raise TicketError("missing")
        channel_id = panel.channel_id
        message_id = panel.published_message_id
        questions = (await session.execute(select(TicketQuestion).where(TicketQuestion.panel_id == panel.id))).scalars().all()
        for row in questions:
            await session.delete(row)
        await session.delete(panel)
        return {"channel_id": channel_id, "message_id": message_id}


def _queue_row(ticket: Ticket, category: TicketCategory | None) -> dict:
    status = "claimed" if ticket.status == "open" and ticket.assignee_id else ticket.status
    return {
        "id": str(ticket.id),
        "number": ticket.number,
        "status": status,
        "raw_status": ticket.status,
        "opener_id": snowflake_to_str(ticket.opener_id),
        "opener_name": ticket.opener_name or "",
        "opener_avatar": ticket.opener_avatar or "",
        "assignee_id": _sid(ticket.assignee_id),
        "category_id": str(ticket.category_id),
        "category_name": category.name if category else "",
        "close_reason": ticket.close_reason or "",
        "opened_at": ticket.opened_at.isoformat() if ticket.opened_at else None,
        "closed_at": ticket.closed_at.isoformat() if ticket.closed_at else None,
        "last_activity_at": (ticket.last_activity_at or ticket.opened_at).isoformat() if (ticket.last_activity_at or ticket.opened_at) else None,
        "degraded": bool(ticket.degraded),
    }


async def list_queue(guild_id: int) -> list[dict]:
    async with session_scope() as session:
        tickets = (
            await session.execute(select(Ticket).where(Ticket.guild_id == guild_id).order_by(Ticket.number.desc()).limit(300))
        ).scalars().all()
        categories = {
            row.id: row
            for row in (await session.execute(select(TicketCategory).where(TicketCategory.guild_id == guild_id))).scalars().all()
        }
        return [_queue_row(ticket, categories.get(ticket.category_id)) for ticket in tickets]


async def ticket_detail(guild_id: int, ticket_id: str) -> dict:
    async with session_scope() as session:
        ticket = await session.get(Ticket, uuid.UUID(ticket_id))
        if ticket is None or ticket.guild_id != guild_id:
            raise TicketError("missing")
        category = await session.get(TicketCategory, ticket.category_id)
        events = (
            await session.execute(select(TicketEvent).where(TicketEvent.ticket_id == ticket.id).order_by(TicketEvent.created_at))
        ).scalars().all()
        messages = (
            await session.execute(select(TicketMessage).where(TicketMessage.ticket_id == ticket.id).order_by(TicketMessage.created_at))
        ).scalars().all()
        people = (
            await session.execute(select(TicketParticipant).where(TicketParticipant.ticket_id == ticket.id))
        ).scalars().all()
        opened = next((event for event in events if event.kind == "opened"), None)
        answers = opened.payload if opened and isinstance(opened.payload, dict) else {}
        return {
            **_queue_row(ticket, category),
            "channel_id": _sid(ticket.channel_id),
            "answers": {str(key): str(value) for key, value in answers.items()},
            "participants": [snowflake_to_str(row.user_id) for row in people],
            "events": [
                {
                    "id": str(event.id),
                    "kind": event.kind,
                    "actor_id": _sid(event.actor_id),
                    "payload": event.payload or {},
                    "created_at": event.created_at.isoformat() if event.created_at else None,
                }
                for event in events
            ],
            "messages": [
                {
                    "id": str(row.id),
                    "author_id": snowflake_to_str(row.author_id),
                    "display_name": row.display_name or row.author_name or "Member",
                    "avatar": row.avatar or "",
                    "content": row.content or "",
                    "attachments": row.attachments or [],
                    "embeds": row.embeds or [],
                    "reference_id": _sid(row.reference_id),
                    "created_at": row.created_at.isoformat() if row.created_at else None,
                }
                for row in messages
            ],
        }


async def list_blacklist(guild_id: int) -> list[dict]:
    async with session_scope() as session:
        rows = (
            await session.execute(select(TicketBlacklist).where(TicketBlacklist.guild_id == guild_id).order_by(TicketBlacklist.created_at.desc()))
        ).scalars().all()
        return [
            {
                "user_id": snowflake_to_str(row.user_id),
                "reason": row.reason or "",
                "actor_id": _sid(row.actor_id),
                "created_at": row.created_at.isoformat() if row.created_at else None,
            }
            for row in rows
        ]


async def list_transcripts(guild_id: int) -> list[dict]:
    async with session_scope() as session:
        tickets = (
            await session.execute(
                select(Ticket).where(Ticket.guild_id == guild_id, Ticket.status.in_(("closed", "deleted"))).order_by(Ticket.closed_at.desc().nulls_last()).limit(300)
            )
        ).scalars().all()
        categories = {
            row.id: row
            for row in (await session.execute(select(TicketCategory).where(TicketCategory.guild_id == guild_id))).scalars().all()
        }
        html_ids = set(
            (
                await session.execute(select(TicketHtml.ticket_id).where(TicketHtml.guild_id == guild_id))
            ).scalars().all()
        )
        rows = []
        for ticket in tickets:
            row = _queue_row(ticket, categories.get(ticket.category_id))
            row["has_transcript"] = ticket.id in html_ids
            rows.append(row)
        return rows


async def category_counts(guild_id: int) -> dict[str, dict]:
    async with session_scope() as session:
        rows = (
            await session.execute(
                select(Ticket.category_id, Ticket.status, func.count()).where(Ticket.guild_id == guild_id).group_by(Ticket.category_id, Ticket.status)
            )
        ).all()
    counts: dict[str, dict] = {}
    for category_id, status, count in rows:
        bucket = counts.setdefault(str(category_id), {"open": 0, "total": 0})
        bucket["total"] += int(count)
        if status == "open":
            bucket["open"] += int(count)
    return counts
