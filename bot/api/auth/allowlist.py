"""Load guild allowlist without importing utils package (avoids discord.py side effects)."""

from __future__ import annotations

import importlib.util
from functools import lru_cache
from pathlib import Path


@lru_cache(maxsize=1)
def _module():
    path = Path(__file__).resolve().parents[2] / "utils" / "guild_allowlist.py"
    spec = importlib.util.spec_from_file_location("_cls_guild_allowlist", path)
    if spec is None or spec.loader is None:
        raise RuntimeError("guild_allowlist module not found")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def is_guild_allowed(guild_id: int) -> bool:
    return _module().is_guild_allowed(guild_id)
