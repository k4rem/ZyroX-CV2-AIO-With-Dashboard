"""Guild-scoped Discord activity log. Snowflakes stay integers in Postgres."""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy import BigInteger, Boolean, DateTime, String, Text, and_, delete, func, or_, select
from sqlalchemy.dialects.postgresql import JSONB, UUID, insert
from sqlalchemy.orm import Mapped, mapped_column

from cls_platform.database import session_scope
from cls_platform.discord_types import snowflake_to_str
from cls_platform.logging.redact import redact
from cls_platform.models import Base

CATEGORIES = (
    "message_events",
    "join_leave_events",
    "member_moderation",
    "voice_events",
    "role_events",
    "channel_events",
    "guild_events",
    "bot_actions",
)
EVENT_RETENTION_DAYS = 90
MESSAGE_RETENTION_DAYS = 30
CONFIDENCE = {"certain", "probable", "unknown"}


class LogEvent(Base):
    __tablename__ = "log_events"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    guild_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    category: Mapped[str] = mapped_column(String(32), nullable=False)
    event_type: Mapped[str] = mapped_column(String(64), nullable=False)
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    actor_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    actor_confidence: Mapped[str] = mapped_column(String(16), nullable=False, default="unknown")
    target_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    channel_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    before: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    after: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    metadata_json: Mapped[dict] = mapped_column("metadata", JSONB, nullable=False, default=dict)


class LogMessage(Base):
    __tablename__ = "log_message_content"

    guild_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    message_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    channel_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    author_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class LogRoute(Base):
    __tablename__ = "log_routes"

    guild_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    category: Mapped[str] = mapped_column(String(32), primary_key=True)
    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    channel_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)


class LoggingError(ValueError):
    pass


def _sid(value: int | None) -> str | None:
    return snowflake_to_str(value) if value else None


def _event_dict(row: LogEvent) -> dict:
    return {
        "id": str(row.id),
        "guild_id": snowflake_to_str(row.guild_id),
        "category": row.category,
        "event_type": row.event_type,
        "occurred_at": row.occurred_at.isoformat(),
        "actor_id": _sid(row.actor_id),
        "actor_confidence": row.actor_confidence,
        "target_id": _sid(row.target_id),
        "channel_id": _sid(row.channel_id),
        "before": row.before,
        "after": row.after,
        "metadata": row.metadata_json or {},
    }


async def remember_message(*, guild_id: int, message_id: int, channel_id: int, author_id: int, content: str) -> None:
    now = datetime.now(timezone.utc)
    body = redact(content or "")[:2000]
    async with session_scope() as session:
        stmt = insert(LogMessage).values(
            guild_id=guild_id,
            message_id=message_id,
            channel_id=channel_id,
            author_id=author_id,
            content=body,
            created_at=now,
        )
        stmt = stmt.on_conflict_do_update(
            index_elements=["guild_id", "message_id"],
            set_={"content": body, "channel_id": channel_id, "author_id": author_id},
        )
        await session.execute(stmt)


async def stored_message(guild_id: int, message_id: int) -> str | None:
    async with session_scope() as session:
        row = await session.get(LogMessage, (guild_id, message_id))
        if row is None:
            return None
        if datetime.now(timezone.utc) - row.created_at > timedelta(days=MESSAGE_RETENTION_DAYS):
            return None
        return row.content


async def record_event(
    *,
    guild_id: int,
    category: str,
    event_type: str,
    actor_id: int | None = None,
    actor_confidence: str = "unknown",
    target_id: int | None = None,
    channel_id: int | None = None,
    before: dict | None = None,
    after: dict | None = None,
    metadata: dict | None = None,
    occurred_at: datetime | None = None,
) -> dict:
    if category not in CATEGORIES:
        raise LoggingError("unknown_category")
    if actor_confidence not in CONFIDENCE:
        raise LoggingError("unknown_confidence")
    if actor_id is None:
        actor_confidence = "unknown"
    when = occurred_at or datetime.now(timezone.utc)
    if when.tzinfo is None:
        when = when.replace(tzinfo=timezone.utc)
    async with session_scope() as session:
        row = LogEvent(
            guild_id=guild_id,
            category=category,
            event_type=event_type[:64],
            occurred_at=when,
            actor_id=actor_id,
            actor_confidence=actor_confidence,
            target_id=target_id,
            channel_id=channel_id,
            before=redact(before) if before else None,
            after=redact(after) if after else None,
            metadata_json=redact(metadata or {}),
        )
        session.add(row)
        await session.flush()
        return _event_dict(row)


async def get_event(guild_id: int, event_id: str) -> dict:
    async with session_scope() as session:
        row = await session.get(LogEvent, uuid.UUID(event_id))
        if row is None or row.guild_id != guild_id:
            raise LoggingError("missing")
        return _event_dict(row)


async def list_events(
    guild_id: int,
    *,
    category: str | None = None,
    event_type: str | None = None,
    actor_id: int | None = None,
    target_id: int | None = None,
    since: datetime | None = None,
    until: datetime | None = None,
    cursor: str | None = None,
    limit: int = 50,
) -> dict:
    limit = max(1, min(limit, 100))
    async with session_scope() as session:
        stmt = select(LogEvent).where(LogEvent.guild_id == guild_id)
        if category:
            stmt = stmt.where(LogEvent.category == category)
        if event_type:
            stmt = stmt.where(LogEvent.event_type == event_type)
        if actor_id:
            stmt = stmt.where(LogEvent.actor_id == actor_id)
        if target_id:
            stmt = stmt.where(LogEvent.target_id == target_id)
        if since:
            stmt = stmt.where(LogEvent.occurred_at >= since)
        if until:
            stmt = stmt.where(LogEvent.occurred_at <= until)
        if cursor:
            stamp, raw_id = cursor.split("|", 1)
            moment = datetime.fromisoformat(stamp)
            stmt = stmt.where(
                or_(
                    LogEvent.occurred_at < moment,
                    and_(LogEvent.occurred_at == moment, LogEvent.id < uuid.UUID(raw_id)),
                )
            )
        rows = (
            await session.execute(stmt.order_by(LogEvent.occurred_at.desc(), LogEvent.id.desc()).limit(limit + 1))
        ).scalars().all()
        page = rows[:limit]
        next_cursor = None
        if len(rows) > limit and page:
            last = page[-1]
            next_cursor = f"{last.occurred_at.isoformat()}|{last.id}"
        return {"events": [_event_dict(row) for row in page], "next_cursor": next_cursor}


async def overview(guild_id: int) -> dict:
    async with session_scope() as session:
        total = (
            await session.execute(select(func.count()).select_from(LogEvent).where(LogEvent.guild_id == guild_id))
        ).scalar_one()
        if int(total) == 0:
            return {"total": 0, "by_category": {}, "top_types": [], "series": [], "heatmap": None}
        categories = (
            await session.execute(
                select(LogEvent.category, func.count())
                .where(LogEvent.guild_id == guild_id)
                .group_by(LogEvent.category)
                .order_by(func.count().desc())
            )
        ).all()
        types = (
            await session.execute(
                select(LogEvent.event_type, func.count())
                .where(LogEvent.guild_id == guild_id)
                .group_by(LogEvent.event_type)
                .order_by(func.count().desc())
                .limit(8)
            )
        ).all()
        day = func.date_trunc("day", LogEvent.occurred_at)
        series_rows = (
            await session.execute(
                select(day, func.count()).where(LogEvent.guild_id == guild_id).group_by(day).order_by(day)
            )
        ).all()
        span = (
            await session.execute(
                select(func.min(LogEvent.occurred_at), func.max(LogEvent.occurred_at)).where(LogEvent.guild_id == guild_id)
            )
        ).one()
        heatmap = None
        if span[0] and span[1] and (span[1] - span[0]) >= timedelta(days=7):
            hour = func.extract("hour", LogEvent.occurred_at)
            weekday = func.extract("dow", LogEvent.occurred_at)
            cells = (
                await session.execute(
                    select(weekday, hour, func.count())
                    .where(LogEvent.guild_id == guild_id)
                    .group_by(weekday, hour)
                )
            ).all()
            heatmap = [
                {"weekday": int(cell[0]), "hour": int(cell[1]), "count": int(cell[2])}
                for cell in cells
            ]
        return {
            "total": int(total),
            "by_category": {name: int(count) for name, count in categories},
            "top_types": [{"event_type": name, "count": int(count)} for name, count in types],
            "series": [{"day": row[0].date().isoformat(), "count": int(row[1])} for row in series_rows],
            "heatmap": heatmap,
        }


async def routes(guild_id: int) -> list[dict]:
    async with session_scope() as session:
        rows = (await session.execute(select(LogRoute).where(LogRoute.guild_id == guild_id))).scalars().all()
        found = {row.category: row for row in rows}
        return [
            {
                "category": category,
                "enabled": bool(found[category].enabled) if category in found else False,
                "channel_id": _sid(found[category].channel_id) if category in found else None,
            }
            for category in CATEGORIES
        ]


async def route_for(guild_id: int, category: str) -> dict | None:
    async with session_scope() as session:
        row = await session.get(LogRoute, (guild_id, category))
        if row is None or not row.enabled or row.channel_id is None:
            return None
        return {"channel_id": row.channel_id}


async def set_route(*, guild_id: int, category: str, enabled: bool, channel_id: int | None) -> dict:
    if category not in CATEGORIES:
        raise LoggingError("unknown_category")
    async with session_scope() as session:
        row = await session.get(LogRoute, (guild_id, category))
        if row is None:
            row = LogRoute(guild_id=guild_id, category=category)
            session.add(row)
        row.enabled = enabled
        row.channel_id = channel_id
        return {"category": category, "enabled": enabled, "channel_id": _sid(channel_id)}


async def purge_expired(now: datetime | None = None) -> dict:
    moment = now or datetime.now(timezone.utc)
    async with session_scope() as session:
        messages = await session.execute(
            delete(LogMessage).where(LogMessage.created_at < moment - timedelta(days=MESSAGE_RETENTION_DAYS))
        )
        events = await session.execute(
            delete(LogEvent).where(LogEvent.occurred_at < moment - timedelta(days=EVENT_RETENTION_DAYS))
        )
        return {"messages": messages.rowcount or 0, "events": events.rowcount or 0}
