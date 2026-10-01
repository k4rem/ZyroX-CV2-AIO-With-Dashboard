"""Runtime command policy. Registration stays fixed; execution is gated."""

from __future__ import annotations

from sqlalchemy import BigInteger, Boolean, String, select
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import Mapped, mapped_column

from cls_platform.database import session_scope
from cls_platform.discord_types import snowflake_to_str
from cls_platform.models import Base
from cls_platform.services.audit import record_audit

DANGEROUS_COGS = {"Ban", "Kick", "Moderation", "Owner", "Block", "Emergency", "Global"}
DANGEROUS_HEADS = {"ban", "unban", "kick", "nuke", "purge", "massban", "hackban", "lockdown", "raid"}


class CommandPolicy(Base):
    __tablename__ = "command_policies"

    guild_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    command_name: Mapped[str] = mapped_column(String(120), primary_key=True)
    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    allowed_role_ids: Mapped[list[int]] = mapped_column(ARRAY(BigInteger), nullable=False, default=list)


def is_dangerous(name: str, cog: str | None) -> bool:
    head = name.split()[0].lower()
    return head in DANGEROUS_HEADS or (cog or "") in DANGEROUS_COGS


async def evaluate(guild_id: int, qualified_name: str, role_ids: set[int]) -> bool:
    parts = qualified_name.split()
    names = [" ".join(parts[: index]) for index in range(1, len(parts) + 1)]
    async with session_scope() as session:
        rows = (
            await session.execute(
                select(CommandPolicy).where(CommandPolicy.guild_id == guild_id, CommandPolicy.command_name.in_(names))
            )
        ).scalars().all()
    by_name = {row.command_name: row for row in rows}
    for name in names:
        row = by_name.get(name)
        if row is None:
            continue
        if not row.enabled:
            return False
        if row.allowed_role_ids and not role_ids.intersection(row.allowed_role_ids):
            return False
    return True


async def policies_for(guild_id: int) -> dict[str, dict]:
    async with session_scope() as session:
        rows = (await session.execute(select(CommandPolicy).where(CommandPolicy.guild_id == guild_id))).scalars().all()
    return {
        row.command_name: {
            "enabled": row.enabled,
            "allowed_role_ids": [snowflake_to_str(item) for item in (row.allowed_role_ids or [])],
        }
        for row in rows
    }


async def set_policy(
    *,
    guild_id: int,
    command_name: str,
    enabled: bool,
    allowed_role_ids: list[int],
    actor_id: int | None,
) -> dict:
    async with session_scope() as session:
        row = await session.get(CommandPolicy, (guild_id, command_name))
        before = None if row is None else {"enabled": row.enabled, "allowed_role_ids": list(row.allowed_role_ids or [])}
        if row is None:
            row = CommandPolicy(guild_id=guild_id, command_name=command_name)
            session.add(row)
        row.enabled = enabled
        row.allowed_role_ids = allowed_role_ids
    await record_audit(
        action="command.policy",
        actor_user_id=actor_id,
        guild_id=guild_id,
        target=command_name,
        before_state=before,
        after_state={"enabled": enabled, "allowed_role_ids": [str(item) for item in allowed_role_ids]},
    )
    return {"command_name": command_name, "enabled": enabled, "allowed_role_ids": [str(item) for item in allowed_role_ids]}


def inventory(bot, saved: dict[str, dict]) -> list[dict]:
    walker = getattr(bot, "walk_commands", None)
    if walker is None:
        return []
    rows = []
    seen = set()
    for command in walker():
        name = getattr(command, "qualified_name", None) or getattr(command, "name", None)
        if not name or name in seen:
            continue
        seen.add(name)
        cog = None
        cog_obj = getattr(command, "cog", None)
        if cog_obj is not None:
            cog = getattr(cog_obj, "qualified_name", None) or cog_obj.__class__.__name__
        policy = saved.get(name, {"enabled": True, "allowed_role_ids": []})
        rows.append(
            {
                "name": name,
                "module": cog or "General",
                "description": (getattr(command, "help", None) or getattr(command, "brief", None) or "")[:180],
                "dangerous": is_dangerous(name, cog),
                "enabled": policy["enabled"],
                "allowed_role_ids": policy["allowed_role_ids"],
            }
        )
    rows.sort(key=lambda item: (item["module"].lower(), item["name"].lower()))
    return rows


def install_command_gate(bot) -> None:
    if getattr(bot, "_cls_command_gate", False):
        return

    async def prefix_check(ctx):
        if ctx.guild is None or ctx.command is None:
            return True
        roles = {role.id for role in getattr(ctx.author, "roles", [])}
        return await evaluate(ctx.guild.id, ctx.command.qualified_name, roles)

    bot.add_check(prefix_check)

    previous = bot.tree.interaction_check

    async def interaction_check(interaction):
        if interaction.guild is None or interaction.command is None:
            return await previous(interaction)
        roles = {role.id for role in getattr(interaction.user, "roles", [])}
        allowed = await evaluate(interaction.guild.id, interaction.command.qualified_name, roles)
        if not allowed:
            return False
        return await previous(interaction)

    bot.tree.interaction_check = interaction_check
    bot._cls_command_gate = True
