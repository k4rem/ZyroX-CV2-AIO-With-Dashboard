"""Discord message payload limits and variable substitution for standalone messages."""

from __future__ import annotations

import re
from datetime import datetime, timezone

CONTENT_MAX = 2000
TITLE_MAX = 256
DESCRIPTION_MAX = 4096
FIELD_NAME_MAX = 256
FIELD_VALUE_MAX = 1024
FOOTER_MAX = 2048
AUTHOR_MAX = 256
FIELDS_MAX = 25
EMBEDS_MAX = 10
EMBED_TOTAL_MAX = 6000
BUTTONS_MAX = 5
URL_MAX = 512

_HTTP = re.compile(r"^https://", re.IGNORECASE)
_VAR = re.compile(r"\{([a-z_]+)\}")
STANDALONE_VARIABLES = ("server_name", "server_membercount", "server_icon", "timestamp")


class MessageSchemaError(ValueError):
    def __init__(self, errors: list[str]):
        self.errors = errors
        super().__init__("; ".join(errors))


def _text(value, limit: int, label: str, errors: list[str]) -> str:
    if value is None:
        return ""
    if not isinstance(value, str):
        errors.append(f"{label} must be text")
        return ""
    if len(value) > limit:
        errors.append(f"{label} is {len(value)} characters; the limit is {limit}")
    return value


def _url(value, label: str, errors: list[str], allow_attachment: bool = False) -> str | None:
    if value in {None, ""}:
        return None
    if not isinstance(value, str) or len(value) > URL_MAX:
        errors.append(f"{label} is not a valid URL")
        return None
    if _HTTP.match(value) or (allow_attachment and value.startswith("attachment://")):
        return value
    errors.append(f"{label} must start with https://")
    return None


def _media(value, label: str, errors: list[str]) -> dict | None:
    if value is None or value == "":
        return None
    if not isinstance(value, dict):
        errors.append(f"{label} is not a media reference")
        return None
    kind = value.get("kind")
    raw = value.get("value")
    if kind == "url":
        url = _url(raw, label, errors, allow_attachment=True)
        return {"kind": "url", "value": url} if url else None
    if kind == "media":
        if not isinstance(raw, str) or not re.fullmatch(r"[a-f0-9]{32}\.png", raw):
            errors.append(f"{label} media key is invalid")
            return None
        return {"kind": "media", "value": raw}
    errors.append(f"{label} must be an upload or a URL")
    return None


def _color(value, errors: list[str]) -> str | None:
    if value in {None, ""}:
        return None
    if not isinstance(value, str) or not re.fullmatch(r"#[0-9A-Fa-f]{6}", value):
        errors.append("Embed color must be a hex color")
        return None
    return value.lower()


def validate_payload(payload: dict) -> dict:
    """Return a cleaned payload or raise MessageSchemaError."""
    errors: list[str] = []
    if not isinstance(payload, dict):
        raise MessageSchemaError(["Message must be an object"])
    unknown = set(payload) - {"content", "embeds", "buttons"}
    if unknown:
        errors.append("Unknown message fields: " + ", ".join(sorted(unknown)))
    content = _text(payload.get("content") or "", CONTENT_MAX, "Message content", errors)
    embeds_in = payload.get("embeds") or []
    buttons_in = payload.get("buttons") or []
    if not isinstance(embeds_in, list) or not isinstance(buttons_in, list):
        raise MessageSchemaError(["Embeds and buttons must be lists"])
    if len(embeds_in) > EMBEDS_MAX:
        errors.append(f"A message can have at most {EMBEDS_MAX} embeds")
    if len(buttons_in) > BUTTONS_MAX:
        errors.append(f"A message can have at most {BUTTONS_MAX} link buttons")
    embeds = [_embed(item, index, errors) for index, item in enumerate(embeds_in[:EMBEDS_MAX])]
    buttons = [_button(item, index, errors) for index, item in enumerate(buttons_in[:BUTTONS_MAX])]
    total = sum(_embed_chars(item) for item in embeds)
    if total > EMBED_TOTAL_MAX:
        errors.append(f"Embeds use {total} characters; the limit is {EMBED_TOTAL_MAX}")
    if not content.strip() and not any(_embed_chars(item) or item.get("image") or item.get("thumbnail") for item in embeds) and not buttons:
        errors.append("Add message content, an embed, or a link button")
    if errors:
        raise MessageSchemaError(errors)
    return {"content": content, "embeds": embeds, "buttons": [item for item in buttons if item]}


def _embed(item: dict, index: int, errors: list[str]) -> dict:
    label = f"Embed {index + 1}"
    if not isinstance(item, dict):
        errors.append(f"{label} is invalid")
        return {"title": "", "description": "", "fields": []}
    unknown = set(item) - {"title", "url", "description", "color", "author", "thumbnail", "image", "fields", "footer", "timestamp"}
    if unknown:
        errors.append(f"{label} has unknown fields: " + ", ".join(sorted(unknown)))
    fields_in = item.get("fields") or []
    if not isinstance(fields_in, list):
        errors.append(f"{label} fields must be a list")
        fields_in = []
    if len(fields_in) > FIELDS_MAX:
        errors.append(f"{label} has {len(fields_in)} fields; the limit is {FIELDS_MAX}")
    author = item.get("author") if isinstance(item.get("author"), dict) else {}
    footer = item.get("footer") if isinstance(item.get("footer"), dict) else {}
    return {
        "title": _text(item.get("title") or "", TITLE_MAX, f"{label} title", errors),
        "url": _url(item.get("url"), f"{label} URL", errors),
        "description": _text(item.get("description") or "", DESCRIPTION_MAX, f"{label} description", errors),
        "color": _color(item.get("color"), errors),
        "author": {
            "name": _text(author.get("name") or "", AUTHOR_MAX, f"{label} author", errors),
            "url": _url(author.get("url"), f"{label} author URL", errors),
            "icon": _media(author.get("icon"), f"{label} author icon", errors),
        },
        "thumbnail": _media(item.get("thumbnail"), f"{label} thumbnail", errors),
        "image": _media(item.get("image"), f"{label} image", errors),
        "fields": [_field(field, label, errors) for field in fields_in[:FIELDS_MAX] if isinstance(field, dict)],
        "footer": {
            "text": _text(footer.get("text") or "", FOOTER_MAX, f"{label} footer", errors),
            "icon": _media(footer.get("icon"), f"{label} footer icon", errors),
        },
        "timestamp": bool(item.get("timestamp")),
    }


def _field(item: dict, label: str, errors: list[str]) -> dict:
    return {
        "name": _text(item.get("name") or "", FIELD_NAME_MAX, f"{label} field name", errors) or "Field",
        "value": _text(item.get("value") or "", FIELD_VALUE_MAX, f"{label} field value", errors) or "—",
        "inline": bool(item.get("inline")),
    }


def _button(item: dict, index: int, errors: list[str]) -> dict | None:
    if not isinstance(item, dict):
        errors.append(f"Button {index + 1} is invalid")
        return None
    label = _text(item.get("label") or "", 80, f"Button {index + 1} label", errors)
    url = _url(item.get("url"), f"Button {index + 1} URL", errors)
    emoji = item.get("emoji") or ""
    if emoji and (not isinstance(emoji, str) or len(emoji) > 64):
        errors.append(f"Button {index + 1} emoji is invalid")
        emoji = ""
    if not label or not url:
        errors.append(f"Button {index + 1} needs a label and an https URL")
        return None
    return {"label": label, "url": url, "emoji": emoji}


def _embed_chars(embed: dict) -> int:
    total = len(embed.get("title") or "") + len(embed.get("description") or "")
    author = embed.get("author") or {}
    footer = embed.get("footer") or {}
    total += len(author.get("name") or "") + len(footer.get("text") or "")
    for field in embed.get("fields") or []:
        total += len(field.get("name") or "") + len(field.get("value") or "")
    return total


def variable_values(guild) -> dict[str, str]:
    now = int(datetime.now(timezone.utc).timestamp())
    icon = ""
    if getattr(guild, "icon", None) is not None:
        icon = str(guild.icon.url)
    return {
        "server_name": str(getattr(guild, "name", "") or ""),
        "server_membercount": str(getattr(guild, "member_count", "") or ""),
        "server_icon": icon,
        "timestamp": f"<t:{now}:f>",
    }


def apply_variables(payload: dict, values: dict[str, str], allowed: tuple[str, ...] | list[str] | None = None) -> dict:
    """Replace variables the caller allows. Unknown tokens are left untouched."""
    permitted = set(STANDALONE_VARIABLES if allowed is None else allowed)

    def swap(text: str) -> str:
        def repl(match: re.Match) -> str:
            key = match.group(1)
            if key in permitted and key in values:
                return values[key]
            return match.group(0)

        return _VAR.sub(repl, text)

    def media(ref):
        if not isinstance(ref, dict):
            return ref
        if ref.get("kind") == "url" and isinstance(ref.get("value"), str):
            return {**ref, "value": swap(ref["value"])}
        return ref

    embeds = []
    for embed in payload.get("embeds") or []:
        author = embed.get("author") or {}
        footer = embed.get("footer") or {}
        embeds.append(
            {
                **embed,
                "title": swap(embed.get("title") or ""),
                "description": swap(embed.get("description") or ""),
                "url": swap(embed["url"]) if embed.get("url") else None,
                "author": {
                    **author,
                    "name": swap(author.get("name") or ""),
                    "icon": media(author.get("icon")),
                },
                "thumbnail": media(embed.get("thumbnail")),
                "image": media(embed.get("image")),
                "fields": [
                    {**field, "name": swap(field.get("name") or ""), "value": swap(field.get("value") or "")}
                    for field in embed.get("fields") or []
                ],
                "footer": {**footer, "text": swap(footer.get("text") or ""), "icon": media(footer.get("icon"))},
            }
        )
    return {
        "content": swap(payload.get("content") or ""),
        "embeds": embeds,
        "buttons": payload.get("buttons") or [],
    }
