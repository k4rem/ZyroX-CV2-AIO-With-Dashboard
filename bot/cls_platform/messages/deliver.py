"""Turn a validated message payload into Discord send arguments."""

from __future__ import annotations

import io
from datetime import datetime, timezone

import discord

from cls_platform import storage
from cls_platform.messages.media import valid_key
from cls_platform.messages.schema import apply_variables, validate_payload


class DeliveryError(ValueError):
    pass


def _namespace(guild_id: int) -> str:
    return f"g{guild_id}"


async def _resolve_media(guild_id: int, ref: dict | None, files: list[discord.File]) -> str | None:
    if not ref:
        return None
    if ref.get("kind") == "url":
        return ref.get("value")
    key = ref.get("value")
    if not valid_key(key or ""):
        raise DeliveryError("Uploaded image is missing.")
    data = await storage.get(_namespace(guild_id), key)
    if data is None:
        raise DeliveryError("Uploaded image is missing.")
    if not any(item.filename == key for item in files):
        files.append(discord.File(io.BytesIO(data), filename=key))
    return f"attachment://{key}"


async def render_message(guild_id: int, payload: dict, values: dict[str, str], allowed=None):
    """One renderer for templates, welcome, direct messages, and goodbye."""
    rendered = validate_payload(apply_variables(validate_payload(payload), values, allowed))
    files: list[discord.File] = []
    embeds: list[discord.Embed] = []
    for item in rendered["embeds"]:
        color = int(item["color"][1:], 16) if item.get("color") else None
        embed = discord.Embed(
            title=item.get("title") or None,
            description=item.get("description") or None,
            url=item.get("url"),
            color=color,
        )
        if item.get("timestamp"):
            embed.timestamp = datetime.now(timezone.utc)
        author = item.get("author") or {}
        icon = await _resolve_media(guild_id, author.get("icon"), files)
        if author.get("name"):
            embed.set_author(name=author["name"][:256], url=author.get("url"), icon_url=icon)
        thumb = await _resolve_media(guild_id, item.get("thumbnail"), files)
        if thumb:
            embed.set_thumbnail(url=thumb)
        image = await _resolve_media(guild_id, item.get("image"), files)
        if image:
            embed.set_image(url=image)
        for field in item.get("fields") or []:
            embed.add_field(name=field["name"][:256], value=field["value"][:1024], inline=bool(field.get("inline")))
        footer = item.get("footer") or {}
        footer_icon = await _resolve_media(guild_id, footer.get("icon"), files)
        if footer.get("text"):
            embed.set_footer(text=footer["text"][:2048], icon_url=footer_icon)
        embeds.append(embed)
    view = None
    if rendered["buttons"]:
        view = discord.ui.View()
        for button in rendered["buttons"]:
            view.add_item(
                discord.ui.Button(
                    style=discord.ButtonStyle.link,
                    label=button["label"][:80],
                    url=button["url"],
                    emoji=button.get("emoji") or None,
                )
            )
    return rendered["content"] or None, embeds, view, files
