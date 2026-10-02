"""Invite V2 history and giveaways. Legacy invite counters are not read."""

from __future__ import annotations

import random
import uuid
from datetime import datetime, timezone

from sqlalchemy import BigInteger, DateTime, ForeignKey, String, func, select
from sqlalchemy.dialects.postgresql import ARRAY, UUID
from sqlalchemy.orm import Mapped, mapped_column

from cls_platform.database import session_scope
from cls_platform.discord_types import snowflake_to_str
from cls_platform.models import Base


class InviteCode(Base):
    __tablename__ = "invite_codes_v2"

    guild_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    code: Mapped[str] = mapped_column(String(32), primary_key=True)
    inviter_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    uses: Mapped[int] = mapped_column(nullable=False, default=0)
    vanity: Mapped[bool] = mapped_column(nullable=False, default=False)


class InviteJoin(Base):
    __tablename__ = "invite_joins_v2"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    guild_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    user_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    code: Mapped[str | None] = mapped_column(String(32), nullable=True)
    status: Mapped[str] = mapped_column(String(16), nullable=False)
    joined_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    left_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class InviteSettings(Base):
    __tablename__ = "invite_settings_v2"

    guild_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    log_channel_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)


class Giveaway(Base):
    __tablename__ = "giveaways_v2"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    guild_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    channel_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    prize: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str] = mapped_column(String(500), nullable=False, default="", server_default="")
    ends_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    starts_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="open")
    winner_count: Mapped[int] = mapped_column(nullable=False, default=1, server_default="1")
    winner_ids: Mapped[list[int]] = mapped_column(ARRAY(BigInteger), nullable=False, default=list)
    required_role_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    blocked_role_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    host_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    message_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)


class GiveawayEntry(Base):
    __tablename__ = "giveaway_entries_v2"

    giveaway_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("giveaways_v2.id"), primary_key=True)
    user_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)


def attribute(before: dict[str, int], after: dict[str, int]) -> tuple[str, str | None]:
    increased = [code for code, uses in after.items() if uses == before.get(code, 0) + 1 and uses > before.get(code, 0)]
    if len(increased) == 1:
        return "certain", increased[0]
    if len(increased) > 1:
        return "ambiguous", None
    return "unknown", None


async def sync_codes(guild_id: int, codes: list[dict]) -> None:
    async with session_scope() as session:
        for item in codes:
            row = await session.get(InviteCode, (guild_id, item["code"]))
            if row is None:
                session.add(
                    InviteCode(
                        guild_id=guild_id,
                        code=item["code"],
                        inviter_id=item.get("inviter_id"),
                        uses=int(item.get("uses") or 0),
                        vanity=bool(item.get("vanity")),
                    )
                )
            else:
                row.uses = int(item.get("uses") or 0)
                row.inviter_id = item.get("inviter_id")


async def note_join(guild_id: int, user_id: int, before: dict[str, int], after: dict[str, int]) -> dict:
    status, code = attribute(before, after)
    async with session_scope() as session:
        row = InviteJoin(
            guild_id=guild_id,
            user_id=user_id,
            code=code,
            status=status,
            joined_at=datetime.now(timezone.utc),
        )
        session.add(row)
        await session.flush()
        return {"id": str(row.id), "status": status, "code": code, "user_id": snowflake_to_str(user_id)}


async def invite_history(guild_id: int) -> list[dict]:
    async with session_scope() as session:
        rows = (
            await session.execute(
                select(InviteJoin).where(InviteJoin.guild_id == guild_id).order_by(InviteJoin.joined_at.desc()).limit(100)
            )
        ).scalars().all()
        return [
            {
                "user_id": snowflake_to_str(row.user_id),
                "code": row.code,
                "status": row.status,
                "joined_at": row.joined_at.isoformat(),
                "left_at": row.left_at.isoformat() if row.left_at else None,
            }
            for row in rows
        ]


async def note_leave(guild_id: int, user_id: int) -> bool:
    async with session_scope() as session:
        row = (
            await session.execute(
                select(InviteJoin)
                .where(InviteJoin.guild_id == guild_id, InviteJoin.user_id == user_id, InviteJoin.left_at.is_(None))
                .order_by(InviteJoin.joined_at.desc())
                .limit(1)
            )
        ).scalar_one_or_none()
        if row is None:
            return False
        row.left_at = datetime.now(timezone.utc)
        return True


def _join_public(row: InviteJoin, inviter_id: int | None) -> dict:
    return {
        "user_id": snowflake_to_str(row.user_id),
        "code": row.code,
        "status": row.status,
        "joined_at": row.joined_at.isoformat(),
        "left_at": row.left_at.isoformat() if row.left_at else None,
        "inviter_id": snowflake_to_str(inviter_id),
    }


async def invite_overview(guild_id: int) -> dict:
    async with session_scope() as session:
        joins = (
            await session.execute(select(InviteJoin).where(InviteJoin.guild_id == guild_id).order_by(InviteJoin.joined_at.desc()))
        ).scalars().all()
        codes = (await session.execute(select(InviteCode).where(InviteCode.guild_id == guild_id))).scalars().all()
        settings = await session.get(InviteSettings, guild_id)
    inviter_by_code = {row.code: row.inviter_id for row in codes}
    members: dict[int, dict] = {}
    uncredited = {"ambiguous": 0, "unknown": 0, "no_inviter": 0}

    def bucket(inviter_id: int) -> dict:
        return members.setdefault(
            inviter_id,
            {"user_id": snowflake_to_str(inviter_id), "valid": 0, "left": 0, "codes": []},
        )

    for row in codes:
        if row.inviter_id:
            item = bucket(int(row.inviter_id))
            if row.code not in item["codes"]:
                item["codes"].append(row.code)
    for row in joins:
        if row.status != "certain" or not row.code:
            key = row.status if row.status in {"ambiguous", "unknown"} else "unknown"
            uncredited[key] += 1
            continue
        inviter_id = inviter_by_code.get(row.code)
        if not inviter_id:
            uncredited["no_inviter"] += 1
            continue
        item = bucket(int(inviter_id))
        if row.left_at is None:
            item["valid"] += 1
        else:
            item["left"] += 1
    ranked = sorted(members.values(), key=lambda item: (-item["valid"], -item["left"], item["user_id"]))
    return {
        "members": ranked,
        "uncredited": uncredited,
        "log_channel_id": snowflake_to_str(settings.log_channel_id) if settings and settings.log_channel_id else None,
    }


async def invite_member(guild_id: int, user_id: int) -> dict:
    async with session_scope() as session:
        codes = (
            await session.execute(select(InviteCode).where(InviteCode.guild_id == guild_id, InviteCode.inviter_id == user_id))
        ).scalars().all()
        code_names = [row.code for row in codes]
        joins = (
            await session.execute(
                select(InviteJoin).where(InviteJoin.guild_id == guild_id, InviteJoin.code.in_(code_names or [""])).order_by(InviteJoin.joined_at.desc())
            )
        ).scalars().all() if code_names else []
    credited = [_join_public(row, user_id) for row in joins if row.status == "certain"]
    return {
        "user_id": snowflake_to_str(user_id),
        "codes": [{"code": row.code, "uses": row.uses, "vanity": row.vanity} for row in codes],
        "joins": credited,
        "valid": sum(1 for row in credited if row["left_at"] is None),
        "left": sum(1 for row in credited if row["left_at"] is not None),
    }


async def invite_log_channel(guild_id: int) -> int | None:
    async with session_scope() as session:
        row = await session.get(InviteSettings, guild_id)
        return int(row.log_channel_id) if row and row.log_channel_id else None


async def set_invite_log_channel(guild_id: int, channel_id: int | None, *, actor_id: int | None = None) -> dict:
    async with session_scope() as session:
        row = await session.get(InviteSettings, guild_id)
        if row is None:
            row = InviteSettings(guild_id=guild_id, log_channel_id=channel_id)
            session.add(row)
        else:
            row.log_channel_id = channel_id
    try:
        from cls_platform.logging.store import record_event

        await record_event(
            guild_id=guild_id,
            category="bot_actions",
            event_type="invite_log",
            actor_id=actor_id,
            actor_confidence="certain" if actor_id else "unknown",
            channel_id=channel_id,
            metadata={"summary": "Invite log channel updated"},
        )
    except Exception:
        pass
    return {"log_channel_id": snowflake_to_str(channel_id)}


def entry_block(role_ids: set[int], *, required: int | None, blocked: int | None, is_bot: bool) -> str | None:
    if is_bot:
        return "Bots can't enter this giveaway."
    if required and int(required) not in role_ids:
        return "You need the required role to enter."
    if blocked and int(blocked) in role_ids:
        return "Your roles can't enter this giveaway."
    return None


def select_winners(
    entries: list[int],
    previous: list[int],
    count: int,
    eligible: set[int] | None,
    rng: random.Random,
) -> list[int]:
    blocked = {int(item) for item in previous}
    seen: set[int] = set()
    pool: list[int] = []
    for raw in entries:
        user_id = int(raw)
        if user_id in seen or user_id in blocked:
            continue
        if eligible is not None and user_id not in eligible:
            continue
        seen.add(user_id)
        pool.append(user_id)
    chosen: list[int] = []
    while pool and len(chosen) < max(0, int(count)):
        chosen.append(pool.pop(rng.randrange(len(pool))))
    return chosen


def message_body(
    *,
    prize: str,
    description: str,
    winner_count: int,
    ends_at: datetime,
    host_id: int | None,
    entry_count: int,
    status: str,
    winner_ids: list[int],
) -> str:
    unix = int(ends_at.timestamp())
    lines = [f"**{prize}**"]
    if description.strip():
        lines.append(description.strip())
    lines.append(f"Winners: {winner_count}")
    if status == "ended":
        shown = ", ".join(f"<@{item}>" for item in winner_ids) or "No eligible entries"
        lines.append(f"Ended <t:{unix}:F>")
        lines.append(f"Won by {shown}")
    elif status == "archived":
        lines.append("This giveaway was archived.")
    else:
        lines.append(f"Ends <t:{unix}:R> (<t:{unix}:F>)")
    if host_id:
        lines.append(f"Host: <@{host_id}>")
    lines.append(f"Entries: {entry_count}")
    return "\n".join(lines)


def _public(row: Giveaway, entry_count: int = 0) -> dict:
    return {
        "id": str(row.id),
        "guild_id": snowflake_to_str(row.guild_id),
        "prize": row.prize,
        "description": row.description or "",
        "channel_id": snowflake_to_str(row.channel_id),
        "status": row.status,
        "ends_at": row.ends_at.isoformat(),
        "starts_at": row.starts_at.isoformat() if row.starts_at else None,
        "winner_count": int(row.winner_count or 1),
        "winner_ids": [snowflake_to_str(item) for item in (row.winner_ids or [])],
        "required_role_id": snowflake_to_str(row.required_role_id),
        "blocked_role_id": snowflake_to_str(row.blocked_role_id),
        "host_id": snowflake_to_str(row.host_id),
        "message_id": snowflake_to_str(row.message_id),
        "entry_count": entry_count,
    }


async def _log_giveaway(guild_id: int, actor_id: int | None, summary: str, channel_id: int | None = None) -> None:
    try:
        from cls_platform.logging.store import record_event

        await record_event(
            guild_id=guild_id,
            category="bot_actions",
            event_type="giveaway",
            actor_id=actor_id,
            actor_confidence="certain" if actor_id else "unknown",
            channel_id=channel_id,
            metadata={"summary": summary},
        )
    except Exception:
        pass


async def _counts(session, ids: list[uuid.UUID]) -> dict[uuid.UUID, int]:
    if not ids:
        return {}
    rows = (
        await session.execute(
            select(GiveawayEntry.giveaway_id, func.count())
            .where(GiveawayEntry.giveaway_id.in_(ids))
            .group_by(GiveawayEntry.giveaway_id)
        )
    ).all()
    return {giveaway_id: int(count) for giveaway_id, count in rows}


async def create_giveaway(
    *,
    guild_id: int,
    channel_id: int | None,
    prize: str,
    ends_at: datetime,
    description: str = "",
    winner_count: int = 1,
    required_role_id: int | None = None,
    blocked_role_id: int | None = None,
    host_id: int | None = None,
    starts_at: datetime | None = None,
) -> dict:
    now = datetime.now(timezone.utc)
    status = "scheduled" if starts_at is not None and starts_at > now else "open"
    async with session_scope() as session:
        row = Giveaway(
            guild_id=guild_id,
            channel_id=channel_id,
            prize=prize[:200],
            description=description[:500],
            ends_at=ends_at,
            starts_at=starts_at,
            status=status,
            winner_count=max(1, min(int(winner_count or 1), 20)),
            winner_ids=[],
            required_role_id=required_role_id,
            blocked_role_id=blocked_role_id,
            host_id=host_id,
        )
        session.add(row)
        await session.flush()
        payload = _public(row, 0)
    await _log_giveaway(guild_id, host_id, f"Giveaway started: {prize[:80]}", channel_id)
    return payload


async def giveaway_for(guild_id: int, giveaway_id: str) -> dict | None:
    async with session_scope() as session:
        row = await session.get(Giveaway, uuid.UUID(giveaway_id))
        if row is None or row.guild_id != guild_id:
            return None
        counts = await _counts(session, [row.id])
        return _public(row, counts.get(row.id, 0))


async def enter_giveaway(guild_id: int, giveaway_id: str, user_id: int) -> str:
    async with session_scope() as session:
        row = await session.get(Giveaway, uuid.UUID(giveaway_id))
        if row is None or row.guild_id != guild_id:
            return "missing"
        if row.status != "open":
            return "closed"
        existing = await session.get(GiveawayEntry, (row.id, user_id))
        if existing is not None:
            return "duplicate"
        session.add(GiveawayEntry(giveaway_id=row.id, user_id=user_id))
        return "entered"


async def leave_giveaway(guild_id: int, giveaway_id: str, user_id: int) -> str:
    async with session_scope() as session:
        row = await session.get(Giveaway, uuid.UUID(giveaway_id))
        if row is None or row.guild_id != guild_id:
            return "missing"
        if row.status != "open":
            return "closed"
        existing = await session.get(GiveawayEntry, (row.id, user_id))
        if existing is None:
            return "absent"
        await session.delete(existing)
        return "left"


async def _entry_ids(session, giveaway_id: uuid.UUID) -> list[int]:
    return list(
        (await session.execute(select(GiveawayEntry.user_id).where(GiveawayEntry.giveaway_id == giveaway_id))).scalars().all()
    )


async def end_giveaway(
    guild_id: int,
    giveaway_id: str,
    *,
    rng: random.Random | None = None,
    eligible: set[int] | None = None,
    actor_id: int | None = None,
) -> dict:
    rng = rng or random.SystemRandom()
    async with session_scope() as session:
        row = await session.get(Giveaway, uuid.UUID(giveaway_id))
        if row is None or row.guild_id != guild_id:
            raise ValueError("missing")
        if row.status == "archived":
            raise ValueError("archived")
        winners = select_winners(await _entry_ids(session, row.id), [], int(row.winner_count or 1), eligible, rng)
        row.status = "ended"
        row.winner_ids = winners
        payload = _public(row, len(await _entry_ids(session, row.id)))
    await _log_giveaway(guild_id, actor_id, f"Giveaway ended: {payload['prize']}", int(payload["channel_id"]) if payload["channel_id"] else None)
    return payload


async def reroll_giveaway(
    guild_id: int,
    giveaway_id: str,
    *,
    rng: random.Random | None = None,
    eligible: set[int] | None = None,
    actor_id: int | None = None,
) -> dict:
    rng = rng or random.SystemRandom()
    async with session_scope() as session:
        row = await session.get(Giveaway, uuid.UUID(giveaway_id))
        if row is None or row.guild_id != guild_id or row.status != "ended":
            raise ValueError("not_ended")
        extra = select_winners(await _entry_ids(session, row.id), list(row.winner_ids or []), 1, eligible, rng)
        if extra:
            row.winner_ids = list(row.winner_ids or []) + extra
        payload = _public(row, len(await _entry_ids(session, row.id)))
    await _log_giveaway(guild_id, actor_id, f"Giveaway rerolled: {payload['prize']}", int(payload["channel_id"]) if payload["channel_id"] else None)
    return payload


async def update_giveaway(guild_id: int, giveaway_id: str, changes: dict) -> dict:
    async with session_scope() as session:
        row = await session.get(Giveaway, uuid.UUID(giveaway_id))
        if row is None or row.guild_id != guild_id:
            raise ValueError("missing")
        if row.status in {"ended", "archived"}:
            raise ValueError("closed")
        if "prize" in changes and changes["prize"]:
            row.prize = str(changes["prize"])[:200]
        if "description" in changes:
            row.description = str(changes["description"] or "")[:500]
        if "ends_at" in changes and changes["ends_at"] is not None:
            row.ends_at = changes["ends_at"]
        if "winner_count" in changes and changes["winner_count"] is not None:
            row.winner_count = max(1, min(int(changes["winner_count"]), 20))
        if "required_role_id" in changes:
            row.required_role_id = changes["required_role_id"]
        if "blocked_role_id" in changes:
            row.blocked_role_id = changes["blocked_role_id"]
        if row.message_id is None and "channel_id" in changes:
            row.channel_id = changes["channel_id"]
        counts = await _counts(session, [row.id])
        return _public(row, counts.get(row.id, 0))


async def archive_giveaway(guild_id: int, giveaway_id: str, *, actor_id: int | None = None) -> dict:
    async with session_scope() as session:
        row = await session.get(Giveaway, uuid.UUID(giveaway_id))
        if row is None or row.guild_id != guild_id:
            raise ValueError("missing")
        row.status = "archived"
        counts = await _counts(session, [row.id])
        payload = _public(row, counts.get(row.id, 0))
    await _log_giveaway(guild_id, actor_id, f"Giveaway archived: {payload['prize']}", int(payload["channel_id"]) if payload["channel_id"] else None)
    return payload


async def attach_message(guild_id: int, giveaway_id: str, message_id: int) -> None:
    async with session_scope() as session:
        row = await session.get(Giveaway, uuid.UUID(giveaway_id))
        if row is None or row.guild_id != guild_id:
            return
        row.message_id = message_id


async def giveaway_history(guild_id: int) -> list[dict]:
    async with session_scope() as session:
        rows = (
            await session.execute(select(Giveaway).where(Giveaway.guild_id == guild_id).order_by(Giveaway.ends_at.desc()))
        ).scalars().all()
        counts = await _counts(session, [row.id for row in rows])
        return [_public(row, counts.get(row.id, 0)) for row in rows]


async def close_due(now: datetime | None = None) -> int:
    moment = now or datetime.now(timezone.utc)
    rng = random.SystemRandom()
    async with session_scope() as session:
        rows = (
            await session.execute(select(Giveaway).where(Giveaway.status == "open", Giveaway.ends_at <= moment))
        ).scalars().all()
        for row in rows:
            winners = select_winners(await _entry_ids(session, row.id), [], int(row.winner_count or 1), None, rng)
            row.status = "ended"
            row.winner_ids = winners
        return len(rows)


async def entry_user_ids(giveaway_id: str) -> list[int]:
    async with session_scope() as session:
        return [int(item) for item in await _entry_ids(session, uuid.UUID(giveaway_id))]


async def due_giveaways(now: datetime | None = None) -> list[dict]:
    moment = now or datetime.now(timezone.utc)
    async with session_scope() as session:
        rows = (
            await session.execute(select(Giveaway).where(Giveaway.status == "open", Giveaway.ends_at <= moment))
        ).scalars().all()
        counts = await _counts(session, [row.id for row in rows])
        return [_public(row, counts.get(row.id, 0)) for row in rows]


async def promote_scheduled(now: datetime | None = None) -> list[dict]:
    moment = now or datetime.now(timezone.utc)
    async with session_scope() as session:
        rows = (
            await session.execute(select(Giveaway).where(Giveaway.status == "scheduled", Giveaway.starts_at <= moment))
        ).scalars().all()
        promoted = []
        for row in rows:
            if row.ends_at <= moment:
                continue
            row.status = "open"
            promoted.append(row)
        counts = await _counts(session, [row.id for row in promoted])
        return [_public(row, counts.get(row.id, 0)) for row in promoted]


async def unpublished_giveaways() -> list[dict]:
    async with session_scope() as session:
        rows = (
            await session.execute(select(Giveaway).where(Giveaway.status == "open", Giveaway.message_id.is_(None)))
        ).scalars().all()
        counts = await _counts(session, [row.id for row in rows])
        return [_public(row, counts.get(row.id, 0)) for row in rows]
