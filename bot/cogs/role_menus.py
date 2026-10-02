"""Role menus. Legacy ReactionRoles stays unloaded so one system assigns roles."""

from __future__ import annotations

import logging
from pathlib import Path

import discord
from discord.ext import commands

from cls_platform.logging.store import record_event
from cls_platform.messages.deliver import DeliveryError
from cls_platform.role_menus.deliver import component_view, discord_emoji, message_args, reaction_targets
from cls_platform.role_menus.logic import emoji_identity, parse_custom_id, plan_change, role_block, same_emoji
from cls_platform.role_menus.store import MenuError, get_menu, menu_for_message, migrate_legacy, remember_channel, set_published

log = logging.getLogger("cls.role_menus")


class RoleMenus(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def cog_load(self):
        path = Path("rr.db")
        if path.exists():
            try:
                count = await migrate_legacy(str(path))
                if count:
                    log.info("migrated %s legacy reaction menus", count)
            except Exception:
                log.debug("legacy reaction migration skipped", exc_info=True)

    async def _log(self, guild_id: int, event_type: str, actor_id: int | None, channel_id: int | None, summary: str):
        try:
            await record_event(
                guild_id=guild_id,
                category="bot_actions",
                event_type=event_type,
                actor_id=actor_id,
                actor_confidence="confirmed" if actor_id else "unknown",
                channel_id=channel_id,
                metadata={"summary": summary},
            )
        except Exception:
            log.debug("role menu log skipped", exc_info=True)

    def _channel(self, guild, menu: dict):
        if guild is None or not menu.get("channel_id"):
            return None
        return guild.get_channel(int(menu["channel_id"]))

    async def _fetch(self, guild, menu: dict):
        channel = self._channel(guild, menu)
        if channel is None or not hasattr(channel, "fetch_message") or not menu.get("message_id"):
            return None, "missing"
        try:
            return await channel.fetch_message(int(menu["message_id"])), "published"
        except discord.NotFound:
            return None, "missing"
        except discord.HTTPException:
            return None, "missing"

    async def sync(self, guild_id: int, menu_id: str) -> str:
        menu = await get_menu(guild_id, menu_id)
        guild = self.bot.get_guild(int(guild_id))
        message, status = await self._fetch(guild, menu)
        if message is None:
            await set_published(guild_id=guild_id, menu_id=menu_id, channel_id=int(menu["channel_id"]) if menu.get("channel_id") else None, message_id=int(menu["message_id"]) if menu.get("message_id") else None, status="missing")
            return "missing"
        disabled = not menu["enabled"]
        if menu["type"] == "reaction":
            if menu["source"] == "created":
                try:
                    await message.edit(view=discord.ui.View(timeout=None))
                except discord.HTTPException:
                    pass
            wanted = reaction_targets(menu)
            present = {}
            for reaction in message.reactions:
                present[emoji_identity(str(reaction.emoji))] = reaction
            for option in menu["options"]:
                key = emoji_identity(option["emoji"]) if option.get("emoji") else ""
                if key and key not in present:
                    try:
                        await message.add_reaction(discord_emoji(option["emoji"]))
                    except discord.HTTPException:
                        log.debug("reaction add failed", exc_info=True)
            me = guild.me if guild else None
            for key, reaction in present.items():
                if key not in wanted and reaction.me and me is not None:
                    try:
                        await message.remove_reaction(reaction.emoji, me)
                    except discord.HTTPException:
                        pass
        else:
            await message.edit(view=component_view(menu, disabled=disabled))
        await set_published(guild_id=guild_id, menu_id=menu_id, channel_id=int(message.channel.id), message_id=int(message.id), status="published")
        return "published"

    async def publish(self, guild_id: int, menu_id: str, *, channel_id: int | None = None, message_id: int | None = None) -> dict:
        menu = await get_menu(guild_id, menu_id)
        guild = self.bot.get_guild(int(guild_id))
        if guild is None:
            raise DeliveryError("This server is not available to CLS right now.")
        target_channel = channel_id or (int(menu["channel_id"]) if menu.get("channel_id") else None)
        if menu["source"] == "existing":
            channel = guild.get_channel(int(target_channel)) if target_channel else None
            target_message = message_id or (int(menu["message_id"]) if menu.get("message_id") else None)
            if channel is None or target_message is None:
                raise DeliveryError("Choose the channel and message first.")
            try:
                await channel.fetch_message(int(target_message))
            except discord.NotFound:
                raise DeliveryError("That message is not in this channel.") from None
            await set_published(guild_id=guild_id, menu_id=menu_id, channel_id=int(channel.id), message_id=int(target_message), status="published")
            await self.sync(guild_id, menu_id)
            await self._log(guild_id, "role_menu_published", None, int(channel.id), f"Role menu {menu['name']} synced")
            return await get_menu(guild_id, menu_id)
        channel = guild.get_channel(int(target_channel)) if target_channel else None
        if channel is None or not hasattr(channel, "send"):
            raise DeliveryError("Choose a channel CLS can post in.")
        if menu.get("message_id") and menu.get("publish_status") == "published":
            await set_published(guild_id=guild_id, menu_id=menu_id, channel_id=int(channel.id), message_id=int(menu["message_id"]), status="published")
            await self.sync(guild_id, menu_id)
            return await get_menu(guild_id, menu_id)
        content, embeds, view, files = await message_args(guild_id, {**menu, "channel_id": str(channel.id)})
        sent = await channel.send(content=content or None, embeds=embeds, view=view, files=files, allowed_mentions=discord.AllowedMentions.none())
        await set_published(guild_id=guild_id, menu_id=menu_id, channel_id=int(channel.id), message_id=int(sent.id), status="published")
        if menu["type"] == "reaction":
            await self.sync(guild_id, menu_id)
        await self._log(guild_id, "role_menu_published", None, int(channel.id), f"Role menu {menu['name']} published")
        return await get_menu(guild_id, menu_id)

    async def republish(self, guild_id: int, menu_id: str) -> dict:
        menu = await get_menu(guild_id, menu_id)
        if menu["source"] != "created":
            raise DeliveryError("Choose a replacement message for this existing post.")
        guild = self.bot.get_guild(int(guild_id))
        channel = self._channel(guild, menu)
        if channel is None:
            raise DeliveryError("The original channel is not available.")
        old_id = int(menu["message_id"]) if menu.get("message_id") else None
        content, embeds, view, files = await message_args(guild_id, menu, disabled=not menu["enabled"])
        sent = await channel.send(content=content or None, embeds=embeds, view=view, files=files, allowed_mentions=discord.AllowedMentions.none())
        if old_id and old_id != sent.id:
            try:
                previous = await channel.fetch_message(old_id)
                await previous.delete()
            except discord.HTTPException:
                pass
        await set_published(guild_id=guild_id, menu_id=menu_id, channel_id=int(channel.id), message_id=int(sent.id), status="published")
        if menu["type"] == "reaction":
            await self.sync(guild_id, menu_id)
        await self._log(guild_id, "role_menu_published", None, int(channel.id), f"Role menu {menu['name']} republished")
        return await get_menu(guild_id, menu_id)

    async def clear_reactions(self, guild_id: int, menu: dict) -> None:
        guild = self.bot.get_guild(int(guild_id))
        message, status = await self._fetch(guild, menu)
        if message is None or status != "published" or guild is None or guild.me is None:
            return
        wanted = reaction_targets(menu)
        for reaction in message.reactions:
            if emoji_identity(str(reaction.emoji)) in wanted and reaction.me:
                try:
                    await message.remove_reaction(reaction.emoji, guild.me)
                except discord.HTTPException:
                    pass

    def explain(self, guild, member: discord.Member, menu: dict, target: int, intent: str) -> str:
        role = guild.get_role(int(target)) if guild else None
        me = guild.me if guild else None
        block = role_block(
            exists=role is not None,
            managed=bool(getattr(role, "managed", False)),
            bot_can_manage=bool(me and me.guild_permissions.manage_roles),
            below_bot=bool(role and me and me.top_role and (role.position < me.top_role.position or (role.position == me.top_role.position and role.id < me.top_role.id))),
        )
        if block:
            return block
        held = {item.id for item in member.roles}
        menu_roles = {int(option["role_id"]) for option in menu["options"]}
        plan = plan_change(mode=menu["mode"], intent=intent, held=held, target=int(target), menu_roles=menu_roles, max_roles=menu.get("max_roles"))
        if plan["error"]:
            return plan["error"]
        if plan.get("unchanged"):
            return f"You already have {role.name}."
        return plan

    async def apply(self, guild, member: discord.Member, menu: dict, target: int, intent: str) -> str:
        if not menu.get("enabled"):
            return "This menu is turned off."
        me = guild.me if guild else None
        if me and me.top_role and member.top_role >= me.top_role:
            return "CLS cannot change roles for a member above it."
        planned = self.explain(guild, member, menu, target, intent)
        if isinstance(planned, str):
            return planned
        added = [guild.get_role(role_id) for role_id in planned["add"]]
        removed = [guild.get_role(role_id) for role_id in planned["remove"]]
        added = [role for role in added if role is not None]
        removed = [role for role in removed if role is not None]
        try:
            if added:
                await member.add_roles(*added, reason="CLS role menu")
            if removed:
                await member.remove_roles(*removed, reason="CLS role menu")
        except discord.Forbidden:
            return "CLS cannot change that role. Check Manage Roles and the role order."
        channel_id = int(menu["channel_id"]) if menu.get("channel_id") else None
        for role in added:
            await self._log(guild.id, "role_menu_added", member.id, channel_id, f"{member.display_name} took {role.name}")
        for role in removed:
            await self._log(guild.id, "role_menu_removed", member.id, channel_id, f"{member.display_name} lost {role.name}")
        if added and not removed:
            return f"Role added: {added[0].name}"
        if removed and not added:
            return f"Role removed: {removed[0].name}"
        if added:
            return f"Role added: {added[0].name}"
        return "No role change."

    def _option_for_emoji(self, menu: dict, emoji: discord.PartialEmoji) -> dict | None:
        for option in menu["options"]:
            if same_emoji(option.get("emoji") or "", emoji.name or "", int(emoji.id) if emoji.id else None):
                return option
        return None

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload: discord.RawReactionActionEvent):
        await self._reaction(payload, "grant")

    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, payload: discord.RawReactionActionEvent):
        await self._reaction(payload, "revoke")

    async def _reaction(self, payload: discord.RawReactionActionEvent, intent: str):
        if payload.guild_id is None or payload.user_id == getattr(self.bot.user, "id", None):
            return
        menu = await menu_for_message(payload.guild_id, payload.message_id)
        if menu is None or menu["type"] != "reaction" or not menu["enabled"]:
            return
        option = self._option_for_emoji(menu, payload.emoji)
        if option is None:
            return
        guild = self.bot.get_guild(payload.guild_id)
        if guild is None:
            return
        member = payload.member if intent == "grant" and isinstance(payload.member, discord.Member) else guild.get_member(payload.user_id)
        if member is None or member.bot:
            return
        if menu.get("channel_id") is None:
            await remember_channel(payload.guild_id, menu["id"], payload.channel_id)
            menu["channel_id"] = str(payload.channel_id)
        await self.apply(guild, member, menu, int(option["role_id"]), intent)

    @commands.Cog.listener()
    async def on_interaction(self, interaction: discord.Interaction):
        if interaction.type is not discord.InteractionType.component or interaction.guild is None:
            return
        custom_id = str((interaction.data or {}).get("custom_id") or "")
        parsed = parse_custom_id(custom_id)
        if parsed is None or not isinstance(interaction.user, discord.Member):
            return
        menu_id, option_id = parsed
        try:
            menu = await get_menu(interaction.guild.id, menu_id)
        except MenuError:
            return
        if menu["type"] == "select" and option_id is None:
            values = (interaction.data or {}).get("values") or []
            option_id = str(values[0]) if values else None
        option = next((item for item in menu["options"] if item["id"] == option_id), None)
        if option is None:
            return
        text = await self.apply(interaction.guild, interaction.user, menu, int(option["role_id"]), "press")
        if interaction.response.is_done():
            await interaction.followup.send(text, ephemeral=True)
        else:
            await interaction.response.send_message(text, ephemeral=True)


async def setup(bot):
    await bot.add_cog(RoleMenus(bot))
