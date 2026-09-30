"""Strict environment parsing for security-related settings."""

from __future__ import annotations

import os
from typing import Iterable


def parse_env_bool(name: str, default: str = "false") -> bool:
    raw = os.getenv(name, default)
    if raw is None:
        raw = default
    value = str(raw).strip().lower()
    if value in ("true", "1", "yes", "on"):
        return True
    if value in ("false", "0", "no", "off"):
        return False
    raise SystemExit(
        f"Startup stopped: {name} must be a strict boolean "
        f"(true/false, 1/0, yes/no, on/off). Got {raw!r}."
    )


def parse_discord_snowflake_list(
    name: str,
    *,
    required: bool = False,
) -> frozenset[int]:
    raw = os.getenv(name, "").strip()
    if not raw:
        if required:
            raise SystemExit(
                f"Startup stopped: {name} is missing. "
                "Set comma-separated Discord guild IDs."
            )
        return frozenset()
    parts = [p.strip() for p in raw.split(",") if p.strip()]
    ids: list[int] = []
    for part in parts:
        if not part.isdigit() or len(part) < 17 or len(part) > 20:
            raise SystemExit(
                f"Startup stopped: {name} contains invalid guild ID {part!r}. "
                "Use comma-separated numeric Discord snowflakes only."
            )
        ids.append(int(part))
    return frozenset(ids)
