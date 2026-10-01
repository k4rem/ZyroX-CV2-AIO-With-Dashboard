"""Drop Ops and non-allowlisted guilds before any V2 security persistence."""

from __future__ import annotations

try:
    from cls_platform.config import OPS_GUILD_ID
    from utils.guild_allowlist import is_guild_allowed
except ImportError:  # phase-0 tests stub utils; production imports the real module
    OPS_GUILD_ID = None

    def is_guild_allowed(guild_id: int) -> bool:
        return False


def security_guild_eligible(guild_id: int) -> bool:
    gid = int(guild_id)
    if OPS_GUILD_ID is not None and gid == int(OPS_GUILD_ID):
        return False
    return bool(is_guild_allowed(gid))
