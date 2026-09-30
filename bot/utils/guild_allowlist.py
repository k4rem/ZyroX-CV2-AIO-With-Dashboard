"""Central guild allowlist (CLS Test / Main / Ops IDs via env only)."""

from __future__ import annotations

from typing import Iterable, Optional

from .env_parse import parse_discord_snowflake_list, parse_env_bool

ALLOWED_GUILD_IDS: frozenset[int] = parse_discord_snowflake_list("ALLOWED_GUILD_IDS")
ALLOW_EMPTY_GUILD_ALLOWLIST: bool = parse_env_bool(
    "ALLOW_EMPTY_GUILD_ALLOWLIST", "false"
)

if not ALLOWED_GUILD_IDS and not ALLOW_EMPTY_GUILD_ALLOWLIST:
    raise SystemExit(
        "Startup stopped: ALLOWED_GUILD_IDS is empty and ALLOW_EMPTY_GUILD_ALLOWLIST is false. "
        "Set comma-separated guild IDs for production, or set ALLOW_EMPTY_GUILD_ALLOWLIST=true "
        "for explicit local development only."
    )

ALLOWLIST_ENFORCED: bool = len(ALLOWED_GUILD_IDS) > 0
DEV_UNRESTRICTED_GUILDS: bool = (
    not ALLOWLIST_ENFORCED and ALLOW_EMPTY_GUILD_ALLOWLIST
)


def guild_allowlist_startup_message() -> Optional[str]:
    if ALLOWLIST_ENFORCED:
        return (
            f"Guild allowlist active ({len(ALLOWED_GUILD_IDS)} guild(s)). "
            "Bot will leave guilds not on ALLOWED_GUILD_IDS."
        )
    if DEV_UNRESTRICTED_GUILDS:
        return (
            "DEV MODE: ALLOW_EMPTY_GUILD_ALLOWLIST=true with empty ALLOWED_GUILD_IDS — "
            "all guilds allowed. Do not use in production."
        )
    return None


def is_guild_allowed(guild_id: int) -> bool:
    if ALLOWLIST_ENFORCED:
        return guild_id in ALLOWED_GUILD_IDS
    if DEV_UNRESTRICTED_GUILDS:
        return True
    return False


def filter_allowed_guilds(guilds: Iterable) -> list:
    if not ALLOWLIST_ENFORCED and DEV_UNRESTRICTED_GUILDS:
        return list(guilds)
    if not ALLOWLIST_ENFORCED:
        return []
    return [g for g in guilds if getattr(g, "id", g) in ALLOWED_GUILD_IDS]


def guild_not_allowed_message() -> str:
    return (
        "This guild is not on the bot allowlist (ALLOWED_GUILD_IDS). "
        "Contact the bot owner if this is a CLS server."
    )
