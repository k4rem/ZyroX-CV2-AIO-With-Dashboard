"""Load guild allowlist without importing the heavy utils package."""

from __future__ import annotations

import importlib.util
import os
import types
from functools import lru_cache
from pathlib import Path

from cls_platform.env_parse import parse_discord_snowflake_list, parse_env_bool


@lru_cache(maxsize=1)
def _module():
    os.environ.setdefault("ALLOW_EMPTY_GUILD_ALLOWLIST", "true")
    path = Path(__file__).resolve().parents[2] / "utils" / "guild_allowlist.py"
    source = path.read_text(encoding="utf-8")
    source = source.replace("from .env_parse import parse_discord_snowflake_list, parse_env_bool", "")
    mod = types.ModuleType("_cls_guild_allowlist")
    mod.__dict__["parse_discord_snowflake_list"] = parse_discord_snowflake_list
    mod.__dict__["parse_env_bool"] = parse_env_bool
    exec(compile(source, str(path), "exec"), mod.__dict__)  # noqa: S102
    return mod


def is_guild_allowed(guild_id: int) -> bool:
    return _module().is_guild_allowed(guild_id)


def clear_allowlist_cache() -> None:
    _module.cache_clear()
