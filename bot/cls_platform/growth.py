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


class Giveaway(Base):
    __tablename__ = "giveaways_v2"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    guild_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    channel_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    prize: Mapped[str] = mapped_column(String(200), nullable=False)
    ends_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="open")
    winner_ids: Mapped[list[int]] = mapped_column(ARRAY(BigInteger), nullable=False, default=list)


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
            }
            for row in rows
        ]


async def create_giveaway(*, guild_id: int, channel_id: int | None, prize: str, ends_at: datetime) -> dict:
    async with session_scope() as session:
        row = Giveaway(guild_id=guild_id, channel_id=channel_id, prize=prize, ends_at=ends_at, winner_ids=[])
        session.add(row)
        await session.flush()
        return {"id": str(row.id), "status": "open", "prize": prize}


async def enter_giveaway(guild_id: int, giveaway_id: str, user_id: int) -> None:
    async with session_scope() as session:
        row = await session.get(Giveaway, uuid.UUID(giveaway_id))
        if row is None or row.guild_id != guild_id or row.status != "open":
            raise ValueError("closed")
        existing = await session.get(GiveawayEntry, (row.id, user_id))
        if existing is None:
            session.add(GiveawayEntry(giveaway_id=row.id, user_id=user_id))


async def _choose(session, row: Giveaway, rng: random.Random) -> int | None:
    entries = (
        await session.execute(select(GiveawayEntry.user_id).where(GiveawayEntry.giveaway_id == row.id))
    ).scalars().all()
    pool = [int(user_id) for user_id in entries if int(user_id) not in set(row.winner_ids or [])]
    if not pool:
        return None
    return int(rng.choice(pool))


async def end_giveaway(guild_id: int, giveaway_id: str, *, rng: random.Random | None = None) -> dict:
    rng = rng or random.SystemRandom()
    async with session_scope() as session:
        row = await session.get(Giveaway, uuid.UUID(giveaway_id))
        if row is None or row.guild_id != guild_id:
            raise ValueError("missing")
        winner = await _choose(session, row, rng)
        row.status = "ended"
        row.winner_ids = [winner] if winner else []
        return {"id": str(row.id), "status": row.status, "winner_ids": [snowflake_to_str(item) for item in row.winner_ids]}


async def reroll_giveaway(guild_id: int, giveaway_id: str, *, rng: random.Random | None = None) -> dict:
    rng = rng or random.SystemRandom()
    async with session_scope() as session:
        row = await session.get(Giveaway, uuid.UUID(giveaway_id))
        if row is None or row.guild_id != guild_id or row.status != "ended":
            raise ValueError("not_ended")
        winner = await _choose(session, row, rng)
        if winner is not None:
            row.winner_ids = list(row.winner_ids or []) + [winner]
        return {"id": str(row.id), "winner_ids": [snowflake_to_str(item) for item in row.winner_ids]}


async def giveaway_history(guild_id: int) -> list[dict]:
    async with session_scope() as session:
        rows = (
            await session.execute(select(Giveaway).where(Giveaway.guild_id == guild_id).order_by(Giveaway.ends_at.desc()))
        ).scalars().all()
        return [
            {
                "id": str(row.id),
                "prize": row.prize,
                "status": row.status,
                "ends_at": row.ends_at.isoformat(),
                "winner_ids": [snowflake_to_str(item) for item in (row.winner_ids or [])],
            }
            for row in rows
        ]


async def close_due(now: datetime | None = None) -> int:
    moment = now or datetime.now(timezone.utc)
    rng = random.SystemRandom()
    async with session_scope() as session:
        rows = (
            await session.execute(select(Giveaway).where(Giveaway.status == "open", Giveaway.ends_at <= moment))
        ).scalars().all()
        for row in rows:
            winner = await _choose(session, row, rng)
            row.status = "ended"
            row.winner_ids = [winner] if winner else []
        return len(rows)
