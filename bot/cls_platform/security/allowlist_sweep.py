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


async def sweep_non_allowlisted_guilds(bot) -> list[int]:
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
