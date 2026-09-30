"""Re-export env parsing without importing the heavy utils package."""

from __future__ import annotations

import importlib.util
from functools import lru_cache
from pathlib import Path


@lru_cache(maxsize=1)
def _env_parse_module():
    path = Path(__file__).resolve().parents[1] / "utils" / "env_parse.py"
    spec = importlib.util.spec_from_file_location("utils_env_parse_standalone", path)
    if spec is None or spec.loader is None:
        raise RuntimeError("env_parse module missing")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def parse_discord_snowflake_list(name: str):
    return _env_parse_module().parse_discord_snowflake_list(name)


def parse_env_bool(name: str, default: str = "false") -> bool:
    return _env_parse_module().parse_env_bool(name, default)
