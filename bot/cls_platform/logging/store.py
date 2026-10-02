"""Guild-scoped Discord activity log. Snowflakes stay integers in Postgres."""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy import BigInteger, Boolean, DateTime, String, Text, and_, cast, delete, func, or_, select
from sqlalchemy.dialects.postgresql import JSONB, UUID, insert
from sqlalchemy.orm import Mapped, mapped_column

from cls_platform.database import session_scope
from cls_platform.discord_types import snowflake_to_str
from cls_platform.logging.pipeline import resolve_delivery
from cls_platform.logging.present import TITLES, present
from cls_platform.logging.redact import redact
from cls_platform.logging.render import FOOTER_MODES, STYLES, default_appearance
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
    "automod",
    "security",
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
    attachments: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class LogRoute(Base):
    __tablename__ = "log_routes"

    guild_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    category: Mapped[str] = mapped_column(String(32), primary_key=True)
    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    channel_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)


class LogIgnore(Base):
    __tablename__ = "log_ignores"

    guild_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    kind: Mapped[str] = mapped_column(String(16), primary_key=True)
    entity_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)


class LogMigration(Base):
    __tablename__ = "log_migrations"

    guild_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    migrated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class LogEventRoute(Base):
    __tablename__ = "log_event_routes"

    guild_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    event_type: Mapped[str] = mapped_column(String(64), primary_key=True)
    mode: Mapped[str] = mapped_column(String(16), nullable=False)
    channel_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)


class LogAppearance(Base):
    __tablename__ = "log_appearance"

    guild_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    style: Mapped[str] = mapped_column(String(16), nullable=False, default="balanced")
    show_avatars: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    show_moderator: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    show_jump: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    show_timestamp: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    show_ids: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    footer_mode: Mapped[str] = mapped_column(String(16), nullable=False, default="cls")
    footer_text: Mapped[str | None] = mapped_column(String(80), nullable=True)
    colors: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)


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


def _with_presentation(event: dict) -> dict:
    event["presentation"] = present(event)
    return event


async def remember_message(
    *,
    guild_id: int,
    message_id: int,
    channel_id: int,
    author_id: int,
    content: str,
    attachments: list | None = None,
) -> None:
    now = datetime.now(timezone.utc)
    body = redact(content or "")[:2000]
    files = redact(attachments or [])
    async with session_scope() as session:
        stmt = insert(LogMessage).values(
            guild_id=guild_id,
            message_id=message_id,
            channel_id=channel_id,
            author_id=author_id,
            content=body,
            attachments=files,
            created_at=now,
        )
        stmt = stmt.on_conflict_do_update(
            index_elements=["guild_id", "message_id"],
            set_={"content": body, "channel_id": channel_id, "author_id": author_id, "attachments": files},
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


async def stored_message_record(guild_id: int, message_id: int) -> dict | None:
    async with session_scope() as session:
        row = await session.get(LogMessage, (guild_id, message_id))
        if row is None:
            return None
        if datetime.now(timezone.utc) - row.created_at > timedelta(days=MESSAGE_RETENTION_DAYS):
            return None
        return {
            "content": row.content,
            "author_id": row.author_id,
            "channel_id": row.channel_id,
            "attachments": row.attachments or [],
        }


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
        return _with_presentation(_event_dict(row))


async def get_event(guild_id: int, event_id: str) -> dict:
    async with session_scope() as session:
        row = await session.get(LogEvent, uuid.UUID(event_id))
        if row is None or row.guild_id != guild_id:
            raise LoggingError("missing")
        return _with_presentation(_event_dict(row))


async def list_events(
    guild_id: int,
    *,
    category: str | None = None,
    event_type: str | None = None,
    actor_id: int | None = None,
    target_id: int | None = None,
    member_id: int | None = None,
    query: str | None = None,
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
        if member_id:
            stmt = stmt.where(or_(LogEvent.actor_id == member_id, LogEvent.target_id == member_id))
        if query:
            needle = query.strip().lower().replace("%", "").replace("_", "")[:80]
            if needle:
                blob = func.lower(
                    func.coalesce(cast(LogEvent.metadata_json, String), "")
                    + " "
                    + func.coalesce(cast(LogEvent.before, String), "")
                    + " "
                    + func.coalesce(cast(LogEvent.after, String), "")
                    + " "
                    + LogEvent.event_type
                )
                stmt = stmt.where(blob.contains(needle))
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
        return {"events": [_with_presentation(_event_dict(row)) for row in page], "next_cursor": next_cursor}


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


def _ignore_public(rows: list[LogIgnore]) -> dict:
    grouped = {"channels": [], "roles": [], "users": []}
    kind_map = {"channel": "channels", "role": "roles", "user": "users"}
    for row in rows:
        key = kind_map.get(row.kind)
        if key:
            grouped[key].append(snowflake_to_str(row.entity_id))
    return grouped


async def ignores(guild_id: int) -> dict:
    async with session_scope() as session:
        rows = (await session.execute(select(LogIgnore).where(LogIgnore.guild_id == guild_id))).scalars().all()
        public = _ignore_public(rows)
        return {
            "channels": [int(item) for item in public["channels"]],
            "roles": [int(item) for item in public["roles"]],
            "users": [int(item) for item in public["users"]],
        }


async def ignores_public(guild_id: int) -> dict:
    raw = await ignores(guild_id)
    return {key: [str(item) for item in values] for key, values in raw.items()}


async def set_ignores(*, guild_id: int, channels: list[int], roles: list[int], users: list[int]) -> dict:
    groups = {"channel": channels, "role": roles, "user": users}
    async with session_scope() as session:
        await session.execute(delete(LogIgnore).where(LogIgnore.guild_id == guild_id))
        for kind, values in groups.items():
            seen = set()
            for value in values:
                if value in seen:
                    continue
                seen.add(int(value))
                session.add(LogIgnore(guild_id=guild_id, kind=kind, entity_id=int(value)))
        await session.flush()
    return await ignores_public(guild_id)


def _known_event(event_type: str) -> bool:
    return event_type in TITLES


def _appearance_dict(row: LogAppearance | None) -> dict:
    base = default_appearance()
    if row is None:
        return base
    colors = row.colors if isinstance(row.colors, dict) else {}
    return {
        "style": row.style if row.style in STYLES else "balanced",
        "show_avatars": bool(row.show_avatars),
        "show_moderator": bool(row.show_moderator),
        "show_jump": bool(row.show_jump),
        "show_timestamp": bool(row.show_timestamp),
        "show_ids": bool(row.show_ids),
        "footer_mode": row.footer_mode if row.footer_mode in FOOTER_MODES else "cls",
        "footer_text": row.footer_text,
        "colors": {str(key): value for key, value in colors.items() if isinstance(value, str)},
    }


async def event_routes(guild_id: int) -> list[dict]:
    async with session_scope() as session:
        rows = (await session.execute(select(LogEventRoute).where(LogEventRoute.guild_id == guild_id))).scalars().all()
        return [
            {"event_type": row.event_type, "mode": row.mode, "channel_id": _sid(row.channel_id)}
            for row in rows
        ]


async def set_event_route(*, guild_id: int, event_type: str, mode: str, channel_id: int | None) -> dict:
    if not _known_event(event_type):
        raise LoggingError("unknown_event")
    if mode not in {"inherit", "custom", "stored_only", "disabled"}:
        raise LoggingError("unknown_mode")
    if mode == "custom" and channel_id is None:
        raise LoggingError("custom_route_needs_channel")
    if mode != "custom":
        channel_id = None
    async with session_scope() as session:
        if mode == "inherit":
            await session.execute(
                delete(LogEventRoute).where(LogEventRoute.guild_id == guild_id, LogEventRoute.event_type == event_type)
            )
        else:
            row = await session.get(LogEventRoute, (guild_id, event_type))
            if row is None:
                row = LogEventRoute(guild_id=guild_id, event_type=event_type, mode=mode)
                session.add(row)
            row.mode = mode
            row.channel_id = channel_id
    return {"event_type": event_type, "mode": mode, "channel_id": _sid(channel_id)}


async def delivery_target(guild_id: int, category: str, event_type: str) -> dict:
    async with session_scope() as session:
        route = await session.get(LogRoute, (guild_id, category))
        event = await session.get(LogEventRoute, (guild_id, event_type))
    decision = resolve_delivery(
        category_enabled=bool(route and route.enabled),
        category_channel_id=route.channel_id if route else None,
        mode=event.mode if event else "inherit",
        event_channel_id=event.channel_id if event else None,
    )
    channel = decision["channel_id"]
    return {**decision, "channel_id": int(channel) if channel else None}


async def appearance_for(guild_id: int) -> dict:
    async with session_scope() as session:
        row = await session.get(LogAppearance, guild_id)
        return _appearance_dict(row)


def _valid_color(value: str) -> bool:
    return len(value) == 7 and value.startswith("#") and all(char in "0123456789abcdefABCDEF" for char in value[1:])


async def set_appearance(guild_id: int, patch: dict) -> dict:
    async with session_scope() as session:
        row = await session.get(LogAppearance, guild_id)
        if row is None:
            row = LogAppearance(guild_id=guild_id, colors={})
            session.add(row)
        if "style" in patch:
            if patch["style"] not in STYLES:
                raise LoggingError("unknown_style")
            row.style = patch["style"]
        for flag in ("show_avatars", "show_moderator", "show_jump", "show_timestamp", "show_ids"):
            if flag in patch:
                setattr(row, flag, bool(patch[flag]))
        if "footer_mode" in patch:
            if patch["footer_mode"] not in FOOTER_MODES:
                raise LoggingError("unknown_footer")
            row.footer_mode = patch["footer_mode"]
        if "footer_text" in patch:
            text = patch["footer_text"]
            row.footer_text = None if text in {None, ""} else str(text)[:80]
        if "colors" in patch and isinstance(patch["colors"], dict):
            colors = dict(row.colors or {})
            for key, value in patch["colors"].items():
                if key not in CATEGORIES or not isinstance(value, str) or not _valid_color(value):
                    raise LoggingError("invalid_color")
                colors[key] = value.lower()
            row.colors = colors
        await session.flush()
        return _appearance_dict(row)
