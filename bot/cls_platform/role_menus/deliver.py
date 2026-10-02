"""Discord components for a role menu."""

from __future__ import annotations

import discord

from cls_platform.messages.deliver import render_message
from cls_platform.role_menus.logic import button_custom_id, emoji_identity, select_custom_id


def discord_emoji(token: str):
    text = (token or "").strip()
    if not text:
        return None
    if text.startswith("<") and text.endswith(">"):
        return discord.PartialEmoji.from_str(text)
    return text


def component_view(menu: dict, *, disabled: bool = False) -> discord.ui.View:
    view = discord.ui.View(timeout=None)
    if menu.get("type") == "button":
        for option in (menu.get("options") or [])[:25]:
            view.add_item(discord.ui.Button(
                label=(option.get("label") or "Role")[:80],
                emoji=discord_emoji(option.get("emoji") or ""),
                custom_id=button_custom_id(menu["id"], option["id"]),
                disabled=disabled,
            ))
    elif menu.get("type") == "select":
        choices = []
        for option in (menu.get("options") or [])[:25]:
            choices.append(discord.SelectOption(
                label=(option.get("label") or "Role")[:100],
                value=option["id"][:100],
                description=(option.get("description") or None),
                emoji=discord_emoji(option.get("emoji") or ""),
            ))
        if choices:
            view.add_item(discord.ui.Select(
                custom_id=select_custom_id(menu["id"]),
                placeholder="Choose a role",
                min_values=1,
                max_values=1,
                options=choices,
                disabled=disabled,
            ))
    return view


async def message_args(guild_id: int, menu: dict, *, disabled: bool = False):
    raw = menu.get("payload") if isinstance(menu.get("payload"), dict) else {"content": menu.get("name") or "Role menu", "embeds": [], "buttons": []}
    payload = {key: raw.get(key) for key in ("content", "embeds", "buttons")}
    if not payload.get("content") and not payload.get("embeds") and not payload.get("buttons"):
        payload["content"] = menu.get("name") or "Role menu"
    content, embeds, view, files = await render_message(guild_id, payload, {})
    if menu.get("type") == "reaction":
        return content, embeds, None, files
    extra = component_view(menu, disabled=disabled)
    if view is None:
        view = extra
    else:
        for item in extra.children:
            view.add_item(item)
    return content, embeds, view, files


def reaction_targets(menu: dict) -> dict[str, dict]:
    found = {}
    for option in menu.get("options") or []:
        if option.get("emoji"):
            found[emoji_identity(option["emoji"])] = option
    return found
