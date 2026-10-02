"""Discord delivery for ticket panels and private channels."""

from __future__ import annotations

import discord

from cls_platform.messages.deliver import DeliveryError, render_message
from cls_platform.tickets.access import access_overwrites

_STYLES = {
    "primary": discord.ButtonStyle.primary,
    "secondary": discord.ButtonStyle.secondary,
    "success": discord.ButtonStyle.success,
    "danger": discord.ButtonStyle.danger,
}


def panel_payload(panel: dict) -> dict:
    stored = panel.get("payload")
    if isinstance(stored, dict) and stored.get("embeds"):
        return stored
    return {
        "content": "",
        "embeds": [
            {
                "title": panel.get("title") or "Support",
                "description": panel.get("message") or "Tell us what happened.",
                "color": "#9474ff",
                "footer": {"text": "CLS Tickets"},
                "timestamp": True,
            }
        ],
        "buttons": [],
    }


def _button_emoji(value: str):
    text = (value or "").strip()
    if not text:
        return None
    if text.startswith("<") and text.endswith(">"):
        return discord.PartialEmoji.from_str(text)
    return text


def open_button(panel: dict) -> discord.ui.Button:
    return discord.ui.Button(
        label=(panel.get("button_label") or "Open ticket")[:80],
        style=_STYLES.get(panel.get("button_style") or "primary", discord.ButtonStyle.primary),
        emoji=_button_emoji(panel.get("button_emoji") or ""),
        custom_id=f"cls-ticket:open:{panel['id']}",
    )


def _view_with(button: discord.ui.Button, extra: discord.ui.View | None) -> discord.ui.View:
    view = extra or discord.ui.View(timeout=None)
    view.add_item(button)
    return view


def select_panel_view(panel: dict) -> discord.ui.View | None:
    options = []
    for option in (panel.get("options") or [])[:25]:
        label = str(option.get("label") or "").strip()
        if not label or not option.get("id"):
            continue
        description = str(option.get("description") or "").strip()[:100]
        options.append(
            discord.SelectOption(
                label=label[:100],
                value=str(option["id"]),
                description=description or None,
                emoji=_button_emoji(str(option.get("emoji") or "")),
            )
        )
    if not options:
        return None
    view = discord.ui.View(timeout=None)
    view.add_item(
        discord.ui.Select(
            placeholder="Open a ticket",
            custom_id=f"cls-ticket:pick:{panel['id']}",
            options=options,
            min_values=1,
            max_values=1,
        )
    )
    return view


async def panel_message_args(guild_id: int, panel: dict):
    shown = panel
    if shown.get("panel_type") == "select" and "options" not in shown:
        from cls_platform.tickets.advanced import panel_advanced

        shown = {**shown, **await panel_advanced(shown["id"])}
    content, embeds, view, files = await render_message(guild_id, panel_payload(shown), {})
    select = select_panel_view(shown) if shown.get("panel_type") == "select" else None
    if select is not None:
        return content, embeds, select, files
    return content, embeds, _view_with(open_button(shown), view), files


def discord_overwrites(guild, opener, staff_roles, extras, deny_roles=None):
    me = guild.me
    spec = access_overwrites(
        everyone_id=guild.default_role.id,
        opener_id=opener.id,
        staff_role_ids=[role.id for role in staff_roles],
        bot_id=me.id if me else 0,
        extra_user_ids=[member.id for member in extras],
        deny_role_ids=[role.id for role in (deny_roles or [])],
    )
    targets = {guild.default_role.id: guild.default_role, opener.id: opener}
    if me is not None:
        targets[me.id] = me
    for role in list(staff_roles) + list(deny_roles or []):
        targets[role.id] = role
    for member in extras:
        targets[member.id] = member
    overwrites = {}
    for target_id, flags in spec.items():
        target = targets.get(target_id)
        if target is None:
            continue
        overwrites[target] = discord.PermissionOverwrite(
            view_channel=flags["view"],
            send_messages=flags["send"],
            read_message_history=flags["history"],
            manage_channels=flags.get("manage", False),
            attach_files=flags.get("attach", False),
            embed_links=flags.get("attach", False),
        )
    return overwrites


def close_request_view(ticket_id: str) -> discord.ui.View:
    view = discord.ui.View(timeout=None)
    view.add_item(discord.ui.Button(label="Close ticket", style=discord.ButtonStyle.success, custom_id=f"cls-t:confirm-close:{ticket_id}"))
    view.add_item(discord.ui.Button(label="Keep open", custom_id=f"cls-t:keep:{ticket_id}"))
    return view


def control_view(ticket_id: str, *, closed: bool, close_mode: str = "direct", tags: list[dict] | None = None) -> discord.ui.View:
    view = discord.ui.View(timeout=None)
    if closed:
        view.add_item(discord.ui.Button(label="Reopen", custom_id=f"cls-t:reopen:{ticket_id}"))
        view.add_item(discord.ui.Button(label="Transcript", custom_id=f"cls-t:transcript:{ticket_id}"))
        view.add_item(discord.ui.Button(label="Delete", style=discord.ButtonStyle.danger, custom_id=f"cls-t:delete:{ticket_id}"))
        return view
    view.add_item(discord.ui.Button(label="Claim", custom_id=f"cls-t:claim:{ticket_id}"))
    view.add_item(discord.ui.Button(label="Unclaim", custom_id=f"cls-t:unclaim:{ticket_id}"))
    view.add_item(discord.ui.Button(label="Close", style=discord.ButtonStyle.danger, custom_id=f"cls-t:close:{ticket_id}"))
    if close_mode == "request":
        view.add_item(discord.ui.Button(label="Ask to close", custom_id=f"cls-t:ask-close:{ticket_id}"))
    view.add_item(discord.ui.Button(label="Add member", custom_id=f"cls-t:add:{ticket_id}"))
    view.add_item(discord.ui.Button(label="Remove member", custom_id=f"cls-t:remove:{ticket_id}"))
    view.add_item(discord.ui.Button(label="Transfer", custom_id=f"cls-t:transfer:{ticket_id}"))
    view.add_item(
        discord.ui.Select(
            placeholder="Priority",
            custom_id=f"cls-t:priority:{ticket_id}",
            row=3,
            options=[
                discord.SelectOption(label="Low", value="low"),
                discord.SelectOption(label="Normal", value="normal"),
                discord.SelectOption(label="High", value="high"),
                discord.SelectOption(label="Urgent", value="urgent"),
            ],
        )
    )
    tag_options = [
        discord.SelectOption(label=str(tag.get("name") or "Tag")[:100], value=str(tag["id"]))
        for tag in (tags or [])[:25]
        if tag.get("id") and tag.get("name")
    ]
    if tag_options:
        view.add_item(discord.ui.Select(placeholder="Tag", custom_id=f"cls-t:tag:{ticket_id}", options=tag_options, row=4))
    return view


def opening_embed(*, number: int, opener: discord.Member, category: str, answers: dict) -> discord.Embed:
    embed = discord.Embed(title=f"Ticket {number:04d}", color=0x9474FF, timestamp=discord.utils.utcnow())
    embed.add_field(name="Opened by", value=opener.mention, inline=True)
    embed.add_field(name="Team", value=category or "Support", inline=True)
    embed.add_field(name="Opened", value=discord.utils.format_dt(discord.utils.utcnow(), "F"), inline=False)
    for label, value in list(answers.items())[:5]:
        embed.add_field(name=str(label)[:256] or "Answer", value=(str(value) or "—")[:1024], inline=False)
    embed.set_footer(text="CLS Tickets")
    return embed


async def publish_panel(guild, panel: dict, *, mode: str):
    channel_id = panel.get("channel_id")
    channel = guild.get_channel(int(channel_id)) if channel_id else None
    if channel is None or not hasattr(channel, "send"):
        raise DeliveryError("Choose a channel CLS can post in.")
    content, embeds, view, files = await panel_message_args(guild.id, panel)
    kwargs = {"content": content, "embeds": embeds, "view": view, "files": files, "allowed_mentions": discord.AllowedMentions.none()}
    message_id = panel.get("published_message_id")
    if mode == "update" and message_id:
        try:
            message = await channel.fetch_message(int(message_id))
        except discord.NotFound:
            return None
        await message.edit(content=content, embeds=embeds, view=view, attachments=files or [])
        return await channel.fetch_message(int(message_id))
    message = await channel.send(**kwargs)
    return message
