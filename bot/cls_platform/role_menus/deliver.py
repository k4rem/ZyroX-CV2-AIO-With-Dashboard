"""Discord components for a role menu."""

from __future__ import annotations

import discord

from cls_platform.messages.deliver import DeliveryError, render_message
from cls_platform.role_menus.logic import button_custom_id, button_faces, button_option_limit, emoji_identity, select_custom_id


def discord_emoji(token: str):
    text = (token or "").strip()
    if not text:
        return None
    if text.startswith("<") and text.endswith(">"):
        return discord.PartialEmoji.from_str(text)
    return text


def assert_button_layout(menu: dict) -> None:
    if menu.get("type") != "button":
        return
    style = menu.get("button_style") or "toggle"
    links = len(((menu.get("payload") or {}).get("buttons") or []))
    limit = button_option_limit(style, links)
    count = len(menu.get("options") or [])
    if count > limit:
        suggestion = "Use Single Toggle or a select menu." if style == "pair" else "Remove options or link buttons."
        raise DeliveryError(f"This layout needs {count} options but Discord allows {limit}. {suggestion}")


def component_view(menu: dict, *, disabled: bool = False) -> discord.ui.View:
    view = discord.ui.View(timeout=None)
    if menu.get("type") == "button":
        style = menu.get("button_style") or "toggle"
        assert_button_layout(menu)
        for option in menu.get("options") or []:
            name = option.get("label") or "Role"
            for action, label in button_faces(style, name):
                view.add_item(discord.ui.Button(
                    label=label,
                    emoji="🟢" if action == "add" else "🔴" if action == "remove" else discord_emoji(option.get("emoji") or "") or "🔔",
                    style=discord.ButtonStyle.success if action == "add" else discord.ButtonStyle.danger if action == "remove" else discord.ButtonStyle.secondary,
                    custom_id=button_custom_id(menu["id"], option["id"], action),
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
