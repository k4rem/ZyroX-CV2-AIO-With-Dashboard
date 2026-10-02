"""Runtime command policy. Registration stays fixed; execution is gated."""

from __future__ import annotations

from discord.ext import commands
from sqlalchemy import BigInteger, Boolean, String, select
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import Mapped, mapped_column

from cls_platform.database import session_scope
from cls_platform.discord_types import snowflake_to_str
from cls_platform.models import Base
from cls_platform.services.audit import record_audit

DANGEROUS_COGS = {"Ban", "Kick", "Moderation", "Owner", "Block", "Emergency", "Global"}
DANGEROUS_HEADS = {"ban", "unban", "kick", "nuke", "purge", "massban", "hackban", "lockdown", "raid"}
PROTECTED = {"reload", "sync"}

CATEGORY_BY_COG = {
    "ban": "Moderation", "kick": "Moderation", "moderation": "Moderation", "mute": "Moderation",
    "unmute": "Moderation", "unban": "Moderation", "lock": "Moderation", "hide": "Moderation",
    "jail": "Moderation", "message": "Moderation", "block": "Moderation", "automod": "Moderation",
    "antispam": "Moderation", "antiinvites": "Moderation", "antiinvite": "Moderation",
    "antiemojispam": "Moderation", "antimassmention": "Moderation",
    "fun": "Fun", "games": "Fun", "slots": "Fun", "blackjack": "Fun",
    "owner": "Administration", "emergency": "Administration", "badges": "Administration", "status": "Administration",
    "help": "Utility", "general": "Utility", "extra": "Utility", "afk": "Utility", "stats": "Utility",
    "calculator": "Utility", "encryption": "Utility", "encrypt": "Utility",
    "voice": "Voice", "jointocreate": "Voice", "j2c": "Voice",
    "logging": "Logging", "loggingv2": "Logging",
    "autorole": "Roles", "reactionroles": "Roles", "customrole": "Roles", "roleautomation": "Roles", "rolemenus": "Roles",
    "ticket": "Tickets", "tickets": "Tickets",
    "welcome": "Engagement", "joindm": "Engagement", "vanity": "Engagement", "counting": "Engagement",
    "tracking": "Invites", "invite": "Invites", "invitetracker": "Invites",
    "messages": "Messaging", "messagespack": "Messaging", "stickymessage": "Messaging", "autoresponder": "Messaging",
    "embed": "Messaging", "media": "Messaging", "sticky": "Messaging",
    "ai": "Utility", "autoreaction": "Engagement", "birth": "Engagement", "birthdays": "Engagement",
    "boost": "Engagement", "booster": "Engagement", "nitro": "Engagement", "fastgreet": "Engagement",
    "welcomer": "Engagement", "leveling": "Engagement", "giveaway": "Giveaways",
    "blacklist": "Moderation", "warn": "Moderation", "ignore": "Moderation", "unhide": "Moderation", "unlock": "Moderation",
    "global": "Administration", "server": "Administration", "staffdmcog": "Administration", "noprefix": "Administration",
    "imagecommands": "Utility", "steal": "Utility", "nightmode": "Utility", "notifcommands": "Utility",
    "qr": "Utility", "snipe": "Utility", "timer": "Utility", "topcheck": "Utility", "youtube": "Utility", "mc": "Fun",
    "invcrole": "Roles", "role": "Roles", "vanityroles": "Roles",
    "verification": "Security", "verify": "Security",
    "music": "Music",
}


class PolicyError(Exception):
    pass


class CommandClosed(commands.CommandError):
    """Raised by the prefix gate. Not a CheckFailure, so the legacy ignore handler does not replace it."""

    def __init__(self, message: str):
        self.cls_message = message
        super().__init__(message)


def category_for(cog: str | None) -> str:
    key = "".join(ch for ch in (cog or "").lower() if ch.isalnum())
    if not key:
        return "Utility"
    if key in CATEGORY_BY_COG:
        return CATEGORY_BY_COG[key]
    if key.startswith("anti"):
        return "Security"
    cleaned = (cog or "General").strip("_")
    return cleaned[:1].upper() + cleaned[1:] if cleaned else "General"


class CommandPolicy(Base):
    __tablename__ = "command_policies"

    guild_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    command_name: Mapped[str] = mapped_column(String(120), primary_key=True)
    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    allowed_role_ids: Mapped[list[int]] = mapped_column(ARRAY(BigInteger), nullable=False, default=list)
    blocked_role_ids: Mapped[list[int]] = mapped_column(ARRAY(BigInteger), nullable=False, default=list)
    allowed_channel_ids: Mapped[list[int]] = mapped_column(ARRAY(BigInteger), nullable=False, default=list)
    blocked_channel_ids: Mapped[list[int]] = mapped_column(ARRAY(BigInteger), nullable=False, default=list)


def is_dangerous(name: str, cog: str | None) -> bool:
    head = name.split()[0].lower()
    return head in DANGEROUS_HEADS or (cog or "") in DANGEROUS_COGS


def _ids(values) -> list[int]:
    return [int(item) for item in (values or [])]


async def decision(guild_id: int, qualified_name: str, role_ids: set[int], channel_id: int | None = None) -> str | None:
    """None means the command may run. A string is the refusal the member should see."""
    head = qualified_name.split()[0].lower()
    if head in PROTECTED:
        return None
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
            return "This command is turned off in this server."
        blocked_roles = set(_ids(row.blocked_role_ids))
        if blocked_roles and role_ids.intersection(blocked_roles):
            return "You can't use this command with your current roles."
        allowed_roles = set(_ids(row.allowed_role_ids))
        if allowed_roles and not role_ids.intersection(allowed_roles):
            return "You can't use this command with your current roles."
        blocked_channels = set(_ids(row.blocked_channel_ids))
        allowed_channels = set(_ids(row.allowed_channel_ids))
        if channel_id is not None and channel_id in blocked_channels:
            return "This command isn't available in this channel."
        if allowed_channels and channel_id not in allowed_channels:
            return "This command isn't available in this channel."
    return None


async def evaluate(guild_id: int, qualified_name: str, role_ids: set[int], channel_id: int | None = None) -> bool:
    return await decision(guild_id, qualified_name, role_ids, channel_id) is None


async def policies_for(guild_id: int) -> dict[str, dict]:
    async with session_scope() as session:
        rows = (await session.execute(select(CommandPolicy).where(CommandPolicy.guild_id == guild_id))).scalars().all()
    return {
        row.command_name: {
            "enabled": row.enabled,
            "allowed_role_ids": [snowflake_to_str(item) for item in (row.allowed_role_ids or [])],
            "blocked_role_ids": [snowflake_to_str(item) for item in (row.blocked_role_ids or [])],
            "allowed_channel_ids": [snowflake_to_str(item) for item in (row.allowed_channel_ids or [])],
            "blocked_channel_ids": [snowflake_to_str(item) for item in (row.blocked_channel_ids or [])],
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
    blocked_role_ids: list[int] | None = None,
    allowed_channel_ids: list[int] | None = None,
    blocked_channel_ids: list[int] | None = None,
) -> dict:
    if command_name.split()[0].lower() in PROTECTED and (
        not enabled or allowed_role_ids or blocked_role_ids or allowed_channel_ids or blocked_channel_ids
    ):
        raise PolicyError("This command is required for recovery and stays available.")
    blocked_roles = blocked_role_ids or []
    allowed_channels = allowed_channel_ids or []
    blocked_channels = blocked_channel_ids or []
    async with session_scope() as session:
        row = await session.get(CommandPolicy, (guild_id, command_name))
        before = None if row is None else {
            "enabled": row.enabled,
            "allowed_role_ids": list(row.allowed_role_ids or []),
            "blocked_role_ids": list(row.blocked_role_ids or []),
            "allowed_channel_ids": list(row.allowed_channel_ids or []),
            "blocked_channel_ids": list(row.blocked_channel_ids or []),
        }
        if row is None:
            row = CommandPolicy(guild_id=guild_id, command_name=command_name)
            session.add(row)
        row.enabled = enabled
        row.allowed_role_ids = allowed_role_ids
        row.blocked_role_ids = blocked_roles
        row.allowed_channel_ids = allowed_channels
        row.blocked_channel_ids = blocked_channels
    after = {
        "enabled": enabled,
        "allowed_role_ids": [str(item) for item in allowed_role_ids],
        "blocked_role_ids": [str(item) for item in blocked_roles],
        "allowed_channel_ids": [str(item) for item in allowed_channels],
        "blocked_channel_ids": [str(item) for item in blocked_channels],
    }
    await record_audit(
        action="command.policy",
        actor_user_id=actor_id,
        guild_id=guild_id,
        target=command_name,
        before_state=before,
        after_state=after,
    )
    try:
        from cls_platform.logging.store import record_event

        await record_event(
            guild_id=guild_id,
            category="bot_actions",
            event_type="command_policy",
            actor_id=actor_id,
            actor_confidence="certain" if actor_id else "unknown",
            metadata={"summary": f"{command_name} {'on' if enabled else 'off'}", "command": command_name},
        )
    except Exception:
        pass
    return {"command_name": command_name, **after}


def inventory(bot, saved: dict[str, dict]) -> list[dict]:
    walker = getattr(bot, "walk_commands", None)
    if walker is None:
        return []
    rows = []
    seen = set()
    for command in walker():
        name = getattr(command, "qualified_name", None) or getattr(command, "name", None)
        if not name or name in seen or (name.startswith("__") and name.endswith("__")):
            continue
        seen.add(name)
        cog = None
        cog_obj = getattr(command, "cog", None)
        if cog_obj is not None:
            cog = getattr(cog_obj, "qualified_name", None) or cog_obj.__class__.__name__
        policy = saved.get(name, {
            "enabled": True,
            "allowed_role_ids": [],
            "blocked_role_ids": [],
            "allowed_channel_ids": [],
            "blocked_channel_ids": [],
        })
        cooldown = _cooldown(command)
        signature = getattr(command, "signature", "") or ""
        permissions = getattr(command, "default_member_permissions", None)
        permission_names = []
        if permissions is not None:
            try:
                permission_names = [str(label).replace("_", " ") for label, allowed in permissions if allowed]
            except (TypeError, ValueError):
                permission_names = []
        rows.append(
            {
                "name": name,
                "module": cog or "General",
                "category": category_for(cog),
                "description": _summary(command),
                "usage": f"{name} {signature}".strip(),
                "aliases": [str(item) for item in (getattr(command, "aliases", None) or [])],
                "cooldown": cooldown,
                "permissions": permission_names,
                "dangerous": is_dangerous(name, cog),
                "protected": name.split()[0].lower() in PROTECTED,
                "enabled": bool(policy.get("enabled", True)),
                "allowed_role_ids": policy.get("allowed_role_ids") or [],
                "blocked_role_ids": policy.get("blocked_role_ids") or [],
                "allowed_channel_ids": policy.get("allowed_channel_ids") or [],
                "blocked_channel_ids": policy.get("blocked_channel_ids") or [],
            }
        )
    rows.sort(key=lambda item: (item["category"].lower(), item["name"].lower()))
    return rows


def _summary(command) -> str:
    brief = str(getattr(command, "brief", None) or "").strip()
    short = str(getattr(command, "short_doc", None) or "").strip()
    source = brief or short
    for raw in source.splitlines():
        line = " ".join(raw.replace("`", "").replace("*", "").replace("_", " ").split())
        if len(line) < 3 or line.lower() in {"utility", "moderation", "general", "fun"}:
            continue
        return line[:140]
    return ""


def _cooldown(command) -> dict | None:
    bucket = getattr(command, "cooldown", None)
    if bucket is None:
        buckets = getattr(command, "_buckets", None)
        bucket = getattr(buckets, "_cooldown", None) if buckets is not None else None
    per = getattr(bucket, "per", None)
    if not per:
        return None
    return {"rate": int(getattr(bucket, "rate", 1) or 1), "per": float(per)}


def install_command_gate(bot) -> None:
    if getattr(bot, "_cls_command_gate", False):
        return

    async def prefix_check(ctx):
        if ctx.guild is None or ctx.command is None:
            return True
        roles = {role.id for role in getattr(ctx.author, "roles", [])}
        channel_id = getattr(getattr(ctx, "channel", None), "id", None)
        reason = await decision(ctx.guild.id, ctx.command.qualified_name, roles, channel_id)
        if reason:
            raise CommandClosed(reason)
        return True

    bot.add_check(prefix_check)

    previous = bot.tree.interaction_check

    async def interaction_check(interaction):
        if interaction.guild is None or interaction.command is None:
            return await previous(interaction)
        roles = {role.id for role in getattr(interaction.user, "roles", [])}
        channel_id = getattr(interaction, "channel_id", None)
        reason = await decision(interaction.guild.id, interaction.command.qualified_name, roles, channel_id)
        if reason:
            try:
                if not interaction.response.is_done():
                    await interaction.response.send_message(reason, ephemeral=True)
            except Exception:
                pass
            return False
        return await previous(interaction)

    bot.tree.interaction_check = interaction_check
    bot._cls_command_gate = True
