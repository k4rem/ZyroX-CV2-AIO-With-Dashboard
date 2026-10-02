"""Discord channel names for tickets."""

from __future__ import annotations

import re

_INVALID = re.compile(r"[^a-z0-9\-]+")
_DASHES = re.compile(r"-{2,}")


def sanitize_slug(value: str) -> str:
    cleaned = _DASHES.sub("-", _INVALID.sub("-", (value or "").lower())).strip("-")
    return cleaned[:32] or "user"


def channel_name(name_format: str, number: int, username: str) -> str:
    slug = sanitize_slug(username)
    try:
        raw = name_format.format(number=number, username=slug)
    except (KeyError, IndexError, ValueError):
        raw = f"ticket-{number:04d}-{slug}"
    name = _DASHES.sub("-", _INVALID.sub("-", raw.lower())).strip("-")
    return (name or f"ticket-{number}")[:90]


def parse_custom_id(custom_id: str) -> tuple[str, str, str]:
    """Return (kind, action, ident). kind is open, modal, or control."""
    if custom_id.startswith("cls-t:"):
        _prefix, action, ident = custom_id.split(":", 2)
        return "control", action, ident
    if not custom_id.startswith("cls-ticket:"):
        return "", "", ""
    rest = custom_id[len("cls-ticket:") :]
    if rest.startswith("open:"):
        return "open", "open", rest.split(":", 1)[1]
    if rest.startswith("modal:"):
        return "modal", "modal", rest.split(":", 1)[1]
    return "open", "open", rest
