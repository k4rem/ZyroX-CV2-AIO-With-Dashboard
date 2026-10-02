"""Role menu persistence. Snowflakes leave this module as strings."""

from __future__ import annotations

import sqlite3
import uuid
from datetime import datetime, timezone

from sqlalchemy import BigInteger, Boolean, DateTime, ForeignKey, Integer, String, select
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from cls_platform.database import session_scope
from cls_platform.discord_types import snowflake_to_str
from cls_platform.models import Base
from cls_platform.role_menus.logic import BUTTON_STYLES, MODES, TYPES, button_option_limit, emoji_token

class MenuError(Exception):
    pass


class RoleMenu(Base):
    __tablename__ = "role_menus"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    guild_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    name: Mapped[str] = mapped_column(String(80), nullable=False)
    channel_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    message_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    source: Mapped[str] = mapped_column(String(16), nullable=False, default="created")
    menu_type: Mapped[str] = mapped_column(String(16), nullable=False, default="reaction")
    mode: Mapped[str] = mapped_column(String(16), nullable=False, default="toggle")
    button_style: Mapped[str] = mapped_column(String(16), nullable=False, default="toggle")
    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    max_roles: Mapped[int | None] = mapped_column(Integer, nullable=True)
    payload: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    publish_status: Mapped[str] = mapped_column(String(16), nullable=False, default="draft")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))


class RoleMenuOption(Base):
    __tablename__ = "role_menu_options"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    menu_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("role_menus.id", ondelete="CASCADE"), nullable=False)
    role_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    emoji: Mapped[str] = mapped_column(String(80), nullable=False, default="")
    label: Mapped[str] = mapped_column(String(80), nullable=False, default="")
    description: Mapped[str] = mapped_column(String(100), nullable=False, default="")
    position: Mapped[int] = mapped_column(Integer, nullable=False, default=0)


def _sid(value: int | None) -> str | None:
    return snowflake_to_str(value) if value else None


def _option(row: RoleMenuOption) -> dict:
    return {
        "id": str(row.id),
        "role_id": snowflake_to_str(row.role_id),
        "emoji": row.emoji or "",
        "label": row.label or "",
        "description": row.description or "",
        "position": row.position,
    }


def _menu(row: RoleMenu, options: list[RoleMenuOption]) -> dict:
    return {
        "id": str(row.id),
        "guild_id": snowflake_to_str(row.guild_id),
        "name": row.name,
        "channel_id": _sid(row.channel_id),
        "message_id": _sid(row.message_id),
        "source": row.source,
        "type": row.menu_type,
        "mode": row.mode,
        "button_style": row.button_style or "toggle",
        "enabled": row.enabled,
        "max_roles": row.max_roles,
        "payload": row.payload,
        "publish_status": row.publish_status,
        "created_at": row.created_at.isoformat() if row.created_at else None,
        "updated_at": row.updated_at.isoformat() if row.updated_at else None,
        "options": [_option(item) for item in sorted(options, key=lambda item: item.position)],
    }


def _clean_options(options: list[dict], menu_type: str) -> list[dict]:
    limit = 20 if menu_type == "reaction" else 25
    cleaned = []
    for index, option in enumerate((options or [])[:limit]):
        role = str(option.get("role_id") or "")
        if not role.isdigit():
            continue
        cleaned.append({
            "role_id": int(role),
            "emoji": emoji_token(str(option.get("emoji") or "")),
            "label": str(option.get("label") or "")[:80],
            "description": str(option.get("description") or "")[:100],
            "position": index,
        })
    return cleaned


async def _load(session, guild_id: int, menu_id: str) -> tuple[RoleMenu, list[RoleMenuOption]]:
    row = await session.get(RoleMenu, uuid.UUID(menu_id))
    if row is None or row.guild_id != guild_id:
        raise MenuError("missing")
    options = (
        await session.execute(select(RoleMenuOption).where(RoleMenuOption.menu_id == row.id).order_by(RoleMenuOption.position))
    ).scalars().all()
    return row, list(options)


async def list_menus(guild_id: int) -> list[dict]:
    async with session_scope() as session:
        rows = (
            await session.execute(select(RoleMenu).where(RoleMenu.guild_id == guild_id).order_by(RoleMenu.updated_at.desc()))
        ).scalars().all()
        result = []
        for row in rows:
            options = (
                await session.execute(select(RoleMenuOption).where(RoleMenuOption.menu_id == row.id).order_by(RoleMenuOption.position))
            ).scalars().all()
            result.append(_menu(row, list(options)))
        return result


async def get_menu(guild_id: int, menu_id: str) -> dict:
    async with session_scope() as session:
        row, options = await _load(session, guild_id, menu_id)
        return _menu(row, options)


def _style(menu_type: str, button_style: str | None) -> str:
    if menu_type != "button":
        return "toggle"
    style = button_style or "pair"
    if style not in BUTTON_STYLES:
        raise MenuError("invalid")
    return style


def _guard_buttons(menu_type: str, button_style: str, payload: dict | None, options: list[dict] | None) -> None:
    if menu_type != "button":
        return
    links = len(((payload or {}).get("buttons") or []))
    limit = button_option_limit(button_style, links)
    count = len([item for item in (options or []) if str(item.get("role_id") or "").isdigit()])
    if count > limit:
        raise MenuError(f"Discord allows {limit} options for this button style. Use Single Toggle or a select menu.")


async def create_menu(*, guild_id: int, name: str, source: str, menu_type: str, mode: str, channel_id: int | None = None, max_roles: int | None = None, payload: dict | None = None, options: list[dict] | None = None, button_style: str | None = None) -> dict:
    if menu_type not in TYPES or mode not in MODES or source not in {"created", "existing"}:
        raise MenuError("invalid")
    if source == "existing" and menu_type != "reaction":
        raise MenuError("existing_reactions_only")
    style = _style(menu_type, button_style)
    _guard_buttons(menu_type, style, payload, options)
    now = datetime.now(timezone.utc)
    async with session_scope() as session:
        row = RoleMenu(
            guild_id=guild_id,
            name=(name or "Role menu")[:80],
            source=source,
            menu_type=menu_type,
            mode=mode,
            button_style=style,
            channel_id=channel_id,
            max_roles=None if mode == "unique" else max_roles,
            payload=payload,
            publish_status="draft",
            created_at=now,
            updated_at=now,
        )
        session.add(row)
        await session.flush()
        for option in _clean_options(options or [], menu_type):
            session.add(RoleMenuOption(menu_id=row.id, **option))
        await session.flush()
        loaded, saved = await _load(session, guild_id, str(row.id))
        return _menu(loaded, saved)


async def update_menu(*, guild_id: int, menu_id: str, name: str | None = None, mode: str | None = None, menu_type: str | None = None, enabled: bool | None = None, max_roles: int | None = None, max_roles_set: bool = False, channel_id: int | None = None, channel_set: bool = False, payload: dict | None = None, options: list[dict] | None = None, button_style: str | None = None) -> dict:
    async with session_scope() as session:
        row, current = await _load(session, guild_id, menu_id)
        if name is not None:
            row.name = name[:80]
        if mode is not None:
            if mode not in MODES:
                raise MenuError("invalid")
            row.mode = mode
        if menu_type is not None:
            if menu_type not in TYPES or (row.source == "existing" and menu_type != "reaction"):
                raise MenuError("existing_reactions_only")
            row.menu_type = menu_type
        if button_style is not None:
            if button_style not in BUTTON_STYLES:
                raise MenuError("invalid")
            row.button_style = button_style
        if enabled is not None:
            row.enabled = enabled
        if max_roles_set:
            row.max_roles = None if row.mode == "unique" else max_roles
        if row.mode == "unique":
            row.max_roles = None
        if channel_set:
            row.channel_id = channel_id
        if payload is not None:
            row.payload = payload
        next_options = options if options is not None else [
            {"role_id": str(item.role_id), "emoji": item.emoji, "label": item.label, "description": item.description} for item in current
        ]
        _guard_buttons(row.menu_type, row.button_style or "toggle", payload if payload is not None else row.payload, next_options)
        if options is not None:
            for option in current:
                await session.delete(option)
            await session.flush()
            for option in _clean_options(options, row.menu_type):
                session.add(RoleMenuOption(menu_id=row.id, **option))
        row.updated_at = datetime.now(timezone.utc)
        await session.flush()
        loaded, saved = await _load(session, guild_id, menu_id)
        return _menu(loaded, saved)


async def set_published(*, guild_id: int, menu_id: str, channel_id: int | None, message_id: int | None, status: str) -> dict:
    async with session_scope() as session:
        row, options = await _load(session, guild_id, menu_id)
        row.channel_id = channel_id
        row.message_id = message_id
        row.publish_status = status
        row.updated_at = datetime.now(timezone.utc)
        return _menu(row, options)


async def duplicate_menu(*, guild_id: int, menu_id: str) -> dict:
    source = await get_menu(guild_id, menu_id)
    return await create_menu(
        guild_id=guild_id,
        name=f"{source['name']} copy"[:80],
        source="created",
        menu_type=source["type"],
        mode=source["mode"],
        button_style=source.get("button_style") or "toggle",
        max_roles=source["max_roles"],
        payload=source["payload"],
        options=source["options"],
    )


async def delete_menu(*, guild_id: int, menu_id: str) -> dict:
    async with session_scope() as session:
        row, options = await _load(session, guild_id, menu_id)
        snapshot = _menu(row, options)
        for option in options:
            await session.delete(option)
        await session.delete(row)
        return snapshot


async def menu_for_message(guild_id: int, message_id: int) -> dict | None:
    async with session_scope() as session:
        row = (
            await session.execute(select(RoleMenu).where(RoleMenu.guild_id == guild_id, RoleMenu.message_id == message_id))
        ).scalars().first()
        if row is None:
            return None
        options = (
            await session.execute(select(RoleMenuOption).where(RoleMenuOption.menu_id == row.id).order_by(RoleMenuOption.position))
        ).scalars().all()
        return _menu(row, list(options))


async def remember_channel(guild_id: int, menu_id: str, channel_id: int) -> None:
    async with session_scope() as session:
        row, _options = await _load(session, guild_id, menu_id)
        if row.channel_id is None:
            row.channel_id = channel_id


def read_legacy_rows(path: str) -> list[tuple[int, int, str, int]]:
    try:
        with sqlite3.connect(path) as conn:
            conn.execute("CREATE TABLE IF NOT EXISTS reaction_roles (guild_id INTEGER, message_id INTEGER, emoji TEXT, role_id INTEGER)")
            return [(int(guild), int(message), str(emoji), int(role)) for guild, message, emoji, role in conn.execute("SELECT guild_id, message_id, emoji, role_id FROM reaction_roles")]
    except sqlite3.Error:
        return []


async def migrate_legacy(path: str) -> int:
    """Copy rr.db listeners into reaction menus. The sqlite file is not modified."""
    grouped: dict[tuple[int, int], list[tuple[str, int]]] = {}
    for guild_id, message_id, emoji, role_id in read_legacy_rows(path):
        grouped.setdefault((guild_id, message_id), []).append((emoji, role_id))
    created = 0
    for (guild_id, message_id), pairs in grouped.items():
        if await menu_for_message(guild_id, message_id):
            continue
        made = await create_menu(
            guild_id=guild_id,
            name="Reaction menu",
            source="existing",
            menu_type="reaction",
            mode="toggle",
            options=[{"role_id": str(role_id), "emoji": emoji, "label": "", "description": ""} for emoji, role_id in pairs],
        )
        await set_published(guild_id=guild_id, menu_id=made["id"], channel_id=None, message_id=message_id, status="published")
        created += 1
    return created
