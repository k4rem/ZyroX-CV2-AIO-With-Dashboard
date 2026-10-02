"""Short-lived stamp for a CLS mutation so the audit listener can name the module."""

from __future__ import annotations

from time import monotonic

_STAMPS: dict[tuple[int, int], tuple[str, float]] = {}
_TTL = 20.0


def note_source(*, guild_id: int, target_id: int | None, module: str) -> None:
    if not guild_id or not target_id or not module:
        return
    _STAMPS[(int(guild_id), int(target_id))] = (str(module)[:40], monotonic() + _TTL)


def read_source(*, guild_id: int, target_id: int | None) -> str | None:
    if not guild_id or not target_id:
        return None
    row = _STAMPS.get((int(guild_id), int(target_id)))
    if row is None or row[1] < monotonic():
        _STAMPS.pop((int(guild_id), int(target_id)), None)
        return None
    return row[0]
