"""Startup allowlist sweep.

Leaves guilds that are not on an enforced allowlist. Never leaves allowlisted
product guilds, and never leaves OPS_GUILD_ID. When the allowlist is not
enforced (explicit local development), the sweep leaves nobody.
"""

from __future__ import annotations

import logging

logger = logging.getLogger(__name__)

try:
    from cls_platform.config import OPS_GUILD_ID
    from utils.guild_allowlist import ALLOWLIST_ENFORCED, is_guild_allowed
except ImportError:  # phase-0 tests stub utils; production imports the real module
    OPS_GUILD_ID = None
    ALLOWLIST_ENFORCED = False

    def is_guild_allowed(guild_id: int) -> bool:
        return False


def allowlist_config_status() -> str:
    """ok, empty, or malformed. A bad parse must not become a leave decision."""
    try:
        from utils.env_parse import parse_discord_snowflake_list, parse_env_bool
    except ImportError:
        return "ok" if ALLOWLIST_ENFORCED else "empty"
    try:
        allow_empty = parse_env_bool("ALLOW_EMPTY_GUILD_ALLOWLIST", "false")
        ids = parse_discord_snowflake_list("ALLOWED_GUILD_IDS")
    except SystemExit:
        logger.error("Guild allowlist config is malformed. Refusing to leave any guild.")
        return "malformed"
    except Exception:
        logger.exception("Guild allowlist config could not be read. Refusing to leave any guild.")
        return "malformed"
    if not ids and not allow_empty:
        logger.error("ALLOWED_GUILD_IDS is empty. Refusing to leave any guild.")
        return "empty"
    return "ok"


async def sweep_non_allowlisted_guilds(bot) -> list[int]:
    status = allowlist_config_status()
    if status != "ok":
        return []
    if not ALLOWLIST_ENFORCED:
        return []
    left: list[int] = []
    for guild in list(getattr(bot, "guilds", []) or []):
        gid = int(guild.id)
        if is_guild_allowed(gid):
            continue
        if OPS_GUILD_ID is not None and gid == int(OPS_GUILD_ID):
            logger.info("Startup allowlist sweep kept Ops guild %s", gid)
            continue
        try:
            await guild.leave()
        except Exception:
            logger.exception("Startup allowlist sweep could not leave guild %s", gid)
            continue
        left.append(gid)
        logger.info("Startup allowlist sweep left non-allowlisted guild %s", gid)
    return left
