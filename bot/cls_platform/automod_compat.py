"""Dashboard Automod vocabulary, mapped once for the legacy cogs.

Dashboard rule ids and action names are not what the legacy tables stored.
This module is the only place that translates them. Warn is not an action:
there is no strike record yet, so it is rejected instead of pretended.
"""

from __future__ import annotations

import logging
import os
from datetime import datetime, timedelta, timezone

import aiosqlite
import discord

logger = logging.getLogger("cls.automod")

DASHBOARD_RULES = {
    "anti_spam": "Anti spam",
    "anti_caps": "Anti caps",
    "anti_links": "Anti link",
    "anti_invites": "Anti invites",
    "anti_mentions": "Anti mass mention",
}
LEGACY_TO_DASHBOARD = {legacy: dash for dash, legacy in DASHBOARD_RULES.items()}
# Not on the dashboard. Left untouched when the dashboard saves the five rules.
EMOJI_EVENT = "Anti emoji spam"

_ACTIONS = {
    "delete": "delete",
    "mute": "mute",
    "kick": "kick",
    "ban": "ban",
    "timeout": "mute",
}

MUTE_MINUTES = {
    "anti_spam": 12,
    "anti_caps": 1,
    "anti_links": 7,
    "anti_invites": 12,
    "anti_mentions": 3,
    "anti_emoji_spam": 1,
}

_ACTION_LABEL = {
    "delete": "Delete message",
    "mute": "Mute",
    "kick": "Kick",
    "ban": "Ban",
}


def automod_db_path() -> str:
    return os.environ.get("AUTOMOD_DB", "db/automod.db")


def normalize_action(value: str | None) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    if not text or text.lower() == "warn":
        return None
    return _ACTIONS.get(text.lower())


def legacy_event(key: str) -> str | None:
    if key in DASHBOARD_RULES:
        return DASHBOARD_RULES[key]
    if key in LEGACY_TO_DASHBOARD:
        return key
    if key == EMOJI_EVENT:
        return key
    return None


def dashboard_key(event: str) -> str | None:
    if event in DASHBOARD_RULES:
        return event
    if event in LEGACY_TO_DASHBOARD:
        return LEGACY_TO_DASHBOARD[event]
    if event == EMOJI_EVENT:
        return "anti_emoji_spam"
    return None


def effective_punishments(raw: dict) -> dict[str, str]:
    """Rules the runtime will actually enforce, in dashboard ids."""
    out: dict[str, str] = {}
    for dash, legacy in DASHBOARD_RULES.items():
        chosen = None
        if dash in raw:
            chosen = normalize_action(raw.get(dash))
        if chosen is None and legacy in raw:
            chosen = normalize_action(raw.get(legacy))
        if chosen:
            out[dash] = chosen
    return out


def prepare_punishment_rows(punishments: dict) -> list[tuple[str, str]]:
    rows: list[tuple[str, str]] = []
    for key, action in punishments.items():
        legacy = legacy_event(str(key))
        if legacy is None or legacy == EMOJI_EVENT:
            raise ValueError(f"Unknown automod rule '{key}'.")
        canon = normalize_action(None if action is None else str(action))
        if canon is None:
            raise ValueError(
                f"Automod action '{action}' is not available. Choose delete, mute, kick, or ban."
            )
        rows.append((legacy, canon))
    return rows


async def apply_punishment_update(db, guild_id: int, punishments: dict) -> None:
    """Replace the five dashboard rules. Missing keys are deleted and stay off."""
    rows = prepare_punishment_rows(punishments)
    for dash, legacy in DASHBOARD_RULES.items():
        await db.execute(
            "DELETE FROM automod_punishments WHERE guild_id = ? AND event IN (?, ?)",
            (guild_id, dash, legacy),
        )
    for legacy, action in rows:
        await db.execute(
            "INSERT OR REPLACE INTO automod_punishments (guild_id, event, punishment) VALUES (?, ?, ?)",
            (guild_id, legacy, action),
        )


async def rule_action(guild_id: int, dashboard_key_name: str, *, db_path: str | None = None) -> str | None:
    legacy = DASHBOARD_RULES.get(dashboard_key_name)
    if dashboard_key_name == "anti_emoji_spam":
        legacy = EMOJI_EVENT
    if legacy is None:
        return None
    path = db_path or automod_db_path()
    async with aiosqlite.connect(path) as db:
        cursor = await db.execute(
            "SELECT event, punishment FROM automod_punishments WHERE guild_id = ? AND event IN (?, ?)",
            (guild_id, dashboard_key_name, legacy),
        )
        found = {row[0]: row[1] for row in await cursor.fetchall()}
    return effective_punishments(found).get(dashboard_key_name) or (
        normalize_action(found.get(legacy)) if dashboard_key_name == "anti_emoji_spam" else None
    )


def _perm(member, name: str) -> bool:
    perms = getattr(member, "guild_permissions", None)
    return bool(getattr(perms, name, False))


def action_block(member, guild, action: str) -> str | None:
    """Why this action cannot run, or None when Discord should be asked."""
    me = getattr(guild, "me", None)
    if action == "delete":
        if me is None or not _perm(me, "manage_messages"):
            return "missing Manage Messages"
        return None
    if getattr(member, "id", None) == getattr(guild, "owner_id", None):
        return "target is the server owner"
    if _perm(member, "administrator"):
        return "target is an administrator"
    if me is None:
        return "bot member unavailable"
    if action == "mute" and not _perm(me, "moderate_members"):
        return "missing Moderate Members"
    if action == "kick" and not _perm(me, "kick_members"):
        return "missing Kick Members"
    if action == "ban" and not _perm(me, "ban_members"):
        return "missing Ban Members"
    member_top = getattr(getattr(member, "top_role", None), "position", None)
    bot_top = getattr(getattr(me, "top_role", None), "position", None)
    if member_top is not None and bot_top is not None and member_top >= bot_top:
        return "hierarchy failure"
    return None


async def _record(guild_id: int, user_id: int | None, rule: str, action: str, result: str, detail: str, db_path: str) -> None:
    try:
        async with aiosqlite.connect(db_path) as db:
            await db.execute(
                """
                CREATE TABLE IF NOT EXISTS automod_events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    guild_id INTEGER NOT NULL,
                    user_id INTEGER,
                    rule TEXT NOT NULL,
                    action TEXT,
                    result TEXT NOT NULL,
                    detail TEXT,
                    created_at TEXT NOT NULL
                )
                """
            )
            await db.execute(
                """
                INSERT INTO automod_events (guild_id, user_id, rule, action, result, detail, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    guild_id,
                    user_id,
                    rule,
                    action,
                    result,
                    detail,
                    datetime.now(timezone.utc).isoformat(),
                ),
            )
            await db.commit()
    except Exception:
        logger.exception("Could not record automod event for guild %s rule %s", guild_id, rule)


async def _discord_log(guild, user, channel, rule: str, action: str, detail: str, db_path: str) -> None:
    try:
        async with aiosqlite.connect(db_path) as db:
            cursor = await db.execute(
                "SELECT log_channel FROM automod_logging WHERE guild_id = ?",
                (guild.id,),
            )
            row = await cursor.fetchone()
    except Exception:
        logger.exception("Could not read automod log channel for guild %s", getattr(guild, "id", None))
        return
    if not row or not row[0]:
        return
    log_channel = guild.get_channel(row[0]) if hasattr(guild, "get_channel") else None
    if log_channel is None:
        logger.warning("Automod log channel %s is missing in guild %s", row[0], guild.id)
        return
    try:
        embed = discord.Embed(title=f"Automod: {rule}", color=0xFF0000)
        embed.add_field(name="User", value=getattr(user, "mention", str(getattr(user, "id", "unknown"))), inline=False)
        embed.add_field(name="Action", value=_ACTION_LABEL.get(action, action), inline=False)
        embed.add_field(name="Result", value=detail, inline=False)
        embed.add_field(name="Channel", value=getattr(channel, "mention", str(getattr(channel, "id", "unknown"))), inline=False)
        await log_channel.send(embed=embed)
    except discord.HTTPException as exc:
        logger.warning("Automod log channel send failed in guild %s: %s", guild.id, exc)


async def _delete_messages(messages, guild) -> tuple[bool, str]:
    me = getattr(guild, "me", None)
    if me is None or not _perm(me, "manage_messages"):
        return False, "missing Manage Messages"
    deleted = 0
    failure = None
    for message in messages:
        try:
            await message.delete()
            deleted += 1
        except discord.NotFound:
            deleted += 1
        except discord.Forbidden:
            failure = "missing Manage Messages"
            logger.warning("Automod delete forbidden in guild %s", getattr(guild, "id", None))
        except discord.HTTPException as exc:
            failure = f"delete failed: {exc}"
            logger.warning("Automod delete failed in guild %s: %s", getattr(guild, "id", None), exc)
    if failure and deleted == 0:
        return False, failure
    if failure:
        return False, failure
    return True, f"deleted {deleted} message(s)"


async def enforce(bot, message, *, rule: str, action: str, reason: str, messages: list | None = None, db_path: str | None = None) -> dict:
    """Run one real action. Failures are logged. Nothing is reported as success unless it happened."""
    path = db_path or automod_db_path()
    canon = normalize_action(action)
    guild = message.guild
    user = message.author
    channel = message.channel
    user_id = getattr(user, "id", None)
    guild_id = getattr(guild, "id", 0)
    targets = list(messages if messages is not None else [message])

    if canon is None:
        detail = f"unsupported action '{action}'"
        logger.warning("Automod %s in guild %s: %s", rule, guild_id, detail)
        await _record(guild_id, user_id, rule, str(action), "failed", detail, path)
        return {"ok": False, "action": action, "detail": detail}

    if canon == "delete":
        ok, detail = await _delete_messages(targets, guild)
        result = "ok" if ok else "failed"
        if ok:
            logger.info("Automod %s deleted messages in guild %s: %s", rule, guild_id, reason)
        else:
            logger.warning("Automod %s delete failed in guild %s: %s", rule, guild_id, detail)
        await _record(guild_id, user_id, rule, canon, result, detail, path)
        await _discord_log(guild, user, channel, rule, canon, detail, path)
        return {"ok": ok, "action": canon, "detail": detail}

    blocked = action_block(user, guild, canon)
    if blocked:
        logger.warning("Automod %s %s blocked in guild %s: %s", rule, canon, guild_id, blocked)
        await _record(guild_id, user_id, rule, canon, "failed", blocked, path)
        await _discord_log(guild, user, channel, rule, canon, blocked, path)
        return {"ok": False, "action": canon, "detail": blocked}

    try:
        if canon == "mute":
            minutes = MUTE_MINUTES.get(rule, 5)
            until = discord.utils.utcnow() + timedelta(minutes=minutes)
            await user.edit(timed_out_until=until, reason=reason)
            detail = f"Muted for {minutes} minutes"
        elif canon == "kick":
            await user.kick(reason=reason)
            detail = "Kicked"
        elif canon == "ban":
            await user.ban(reason=reason)
            detail = "Banned"
        else:
            detail = f"unsupported action '{canon}'"
            await _record(guild_id, user_id, rule, canon, "failed", detail, path)
            return {"ok": False, "action": canon, "detail": detail}
    except discord.Forbidden as exc:
        detail = f"Discord refused the action ({exc})"
        logger.warning("Automod %s %s forbidden in guild %s: %s", rule, canon, guild_id, exc)
        await _record(guild_id, user_id, rule, canon, "failed", detail, path)
        await _discord_log(guild, user, channel, rule, canon, detail, path)
        return {"ok": False, "action": canon, "detail": detail}
    except discord.HTTPException as exc:
        detail = f"Discord error ({exc})"
        logger.warning("Automod %s %s failed in guild %s: %s", rule, canon, guild_id, exc)
        await _record(guild_id, user_id, rule, canon, "failed", detail, path)
        await _discord_log(guild, user, channel, rule, canon, detail, path)
        return {"ok": False, "action": canon, "detail": detail}

    if targets:
        deleted_ok, delete_detail = await _delete_messages(targets, guild)
        if not deleted_ok:
            logger.warning("Automod %s removed the member but could not delete in guild %s: %s", rule, guild_id, delete_detail)
            detail = f"{detail}; {delete_detail}"
    logger.info("Automod %s %s in guild %s: %s", rule, canon, guild_id, detail)
    await _record(guild_id, user_id, rule, canon, "ok", detail, path)
    await _discord_log(guild, user, channel, rule, canon, detail, path)
    return {"ok": True, "action": canon, "detail": detail}
