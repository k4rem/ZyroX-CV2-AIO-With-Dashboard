"""Tickets V2 Discord runtime. Persistent buttons survive restart via custom_id."""

from __future__ import annotations

import logging
from datetime import datetime, timezone

import discord
from discord.ext import commands

from cls_platform.logging.store import record_event
from cls_platform.messages.deliver import DeliveryError
from cls_platform.tickets.advanced import (
    add_note,
    category_public,
    delete_note,
    known_categories,
    list_replies,
    list_tags,
    load_option,
    mark_close_request,
    panel_advanced,
    reject_close_request,
    render_reply,
    route_category,
    set_priority,
    set_ticket_tags,
    support_status,
)
from cls_platform.tickets.deliver import close_request_view, control_view, discord_overwrites, opening_embed, publish_panel
from cls_platform.tickets.html_transcript import render_html
from cls_platform.tickets.naming import parse_custom_id
from cls_platform.tickets.schedule import arm_close_request, arm_inactivity, inactivity_still_due, payload_generation
from cls_platform.tickets.store import (
    TicketError,
    add_participant,
    bind_channel,
    capture_message,
    claim_ticket,
    close_ticket,
    guild_settings,
    load_panel,
    load_ticket,
    mark_deleted,
    mark_degraded,
    open_ticket,
    participants,
    record_event as record_ticket_event,
    remove_participant,
    reopen_ticket,
    save_html,
    transcript,
    transfer_ticket,
    unclaim_ticket,
)

log = logging.getLogger(__name__)

_REFUSAL = {
    "blacklisted": "You cannot open tickets in this server.",
    "cooldown": "Wait before opening another ticket.",
    "max_open": "You already have the maximum number of open tickets.",
    "duplicate_open": "You already have an open ticket in this category.",
    "required_role": "You need a required role before opening this ticket.",
    "blocked_role": "Your roles cannot open this ticket.",
    "category_missing": "This ticket team is not available.",
    "not_open": "This ticket is not open.",
    "not_closed": "This ticket is not closed.",
    "already_claimed": "Another staff member already claimed this ticket.",
    "is_opener": "The ticket opener stays in the channel.",
    "missing": "This ticket is no longer available.",
    "priority": "Choose Low, Normal, High, or Urgent.",
    "tag_missing": "That tag is no longer available.",
    "note_empty": "Write a note before saving.",
    "note_forbidden": "You can only delete your own note.",
    "reply": "A saved reply needs a name and some text.",
    "timezone": "That timezone is not recognized.",
}


def _refusal(exc: TicketError) -> str:
    return _REFUSAL.get(str(exc), "That ticket action could not be completed.")


class TicketsV2(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def cog_load(self):
        from cls_platform.services.scheduler import register_job_handler

        register_job_handler("ticket_inactivity", self.handle_inactivity)
        register_job_handler("ticket_close_request", self.handle_close_request)

    async def _log(self, guild_id: int, event_type: str, actor_id: int | None, channel_id: int | None, summary: str):
        try:
            await record_event(
                guild_id=guild_id,
                category="bot_actions",
                event_type=event_type,
                actor_id=actor_id,
                actor_confidence="certain" if actor_id else "unknown",
                channel_id=channel_id,
                metadata={"summary": summary},
            )
        except Exception:
            log.debug("ticket log skipped", exc_info=True)

    def _staff(self, member: discord.Member, role_ids: list[int]) -> bool:
        if member.guild_permissions.administrator or member.guild_permissions.manage_channels:
            return True
        held = {role.id for role in member.roles}
        return bool(held.intersection(role_ids))

    async def _arm(self, guild_id: int, ticket_id: str):
        settings = await guild_settings(guild_id)
        hours = settings.get("auto_close_hours")
        if not hours:
            return
        ticket = await load_ticket(guild_id, ticket_id)
        if ticket is None:
            return
        warn = int(hours) * 3600
        grace = int(settings.get("grace_minutes") or 60) * 60
        await arm_inactivity(guild_id=guild_id, ticket_id=ticket_id, generation=int(ticket["generation"] or 0), warn_seconds=warn, close_seconds=warn + grace)

    async def handle_inactivity(self, job):
        payload = job.payload or {}
        guild_id = int(payload["guild_id"])
        ticket_id = str(payload["ticket_id"])
        ticket = await load_ticket(guild_id, ticket_id)
        if ticket is None or not inactivity_still_due(ticket["status"], ticket["generation"], payload_generation(payload)):
            return
        guild = self.bot.get_guild(guild_id)
        channel = guild.get_channel(int(ticket["channel_id"])) if guild and ticket.get("channel_id") else None
        if payload.get("phase") == "warn":
            await record_ticket_event(guild_id=guild_id, ticket_id=ticket_id, kind="auto_close_warning", actor_id=None, payload={})
            if channel is not None:
                await channel.send("This ticket has been quiet. It will close soon unless someone replies.")
            return
        await self._finish_close(guild, ticket, actor_id=None, reason="No recent activity", auto=True)

    async def handle_close_request(self, job):
        payload = job.payload or {}
        guild_id = int(payload.get("guild_id") or 0)
        ticket_id = str(payload.get("ticket_id") or "")
        ticket = await load_ticket(guild_id, ticket_id)
        if ticket is None or ticket["status"] != "open" or not ticket.get("close_timeout_minutes"):
            return
        from cls_platform.tickets.advanced import close_request_expired
        from cls_platform.tickets.store import Ticket
        from cls_platform.database import session_scope
        import uuid

        async with session_scope() as session:
            row = await session.get(Ticket, uuid.UUID(ticket_id))
            requested = row.close_requested_at if row is not None else None
        if not close_request_expired(requested, ticket.get("close_timeout_minutes"), datetime.now(timezone.utc)):
            return
        guild = self.bot.get_guild(guild_id)
        if guild is None:
            return
        await self._finish_close(guild, ticket, actor_id=None, reason="Close request timed out", auto=True)

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.guild is None or not message.channel:
            return
        reference = message.reference.message_id if message.reference else None
        created = message.created_at if message.created_at.tzinfo else message.created_at.replace(tzinfo=timezone.utc)
        human = not message.author.bot
        ticket_id = await capture_message(
            guild_id=message.guild.id,
            channel_id=message.channel.id,
            message_id=message.id,
            author_id=message.author.id,
            author_name=getattr(message.author, "name", "") or "",
            display_name=getattr(message.author, "display_name", "") or "",
            avatar=str(message.author.display_avatar.url) if getattr(message.author, "display_avatar", None) else "",
            content=message.content or "",
            attachments=[{"filename": item.filename, "url": item.url, "size": item.size} for item in message.attachments],
            embeds=[{"title": embed.title or "", "description": (embed.description or "")[:500]} for embed in message.embeds],
            reference_id=reference,
            created_at=created,
            record_activity=human,
        )
        if ticket_id and human:
            await self._arm(message.guild.id, ticket_id)

    @commands.Cog.listener()
    async def on_interaction(self, interaction: discord.Interaction):
        custom_id = str((interaction.data or {}).get("custom_id") or "")
        kind, action, ident = parse_custom_id(custom_id)
        if not kind or interaction.guild is None or not isinstance(interaction.user, discord.Member):
            return
        if kind in {"open", "modal", "pick", "omodal"}:
            await self._open(interaction, kind, ident)
            return
        await self._control(interaction, action, ident)

    async def _open(self, interaction: discord.Interaction, kind: str, panel_id: str):
        if kind == "omodal":
            option = await load_option(panel_id)
            if option is None:
                await interaction.response.send_message("This option is no longer available.", ephemeral=True)
                return
            panel = await load_panel(option["panel_id"])
            if panel is None:
                await interaction.response.send_message("This panel is not available.", ephemeral=True)
                return
            answers = {}
            for row in (interaction.data or {}).get("components") or []:
                for component in row.get("components") or []:
                    answers[str(component.get("custom_id") or "Answer")] = str(component.get("value") or "")
            await self._spawn(interaction, panel, answers, option.get("category_id"))
            return
        if kind == "pick":
            panel = await load_panel(panel_id)
            if panel is None or panel["guild_id"] != interaction.guild.id:
                await interaction.response.send_message("This panel is not available.", ephemeral=True)
                return
            chosen = str(((interaction.data or {}).get("values") or [""])[0])
            option = await load_option(chosen)
            if option is None or option["panel_id"] != panel["id"]:
                await interaction.response.send_message("That option is no longer on this panel.", ephemeral=True)
                return
            questions = option.get("questions") or []
            if questions:
                modal = discord.ui.Modal(title=(option["label"] or "Ticket")[:45], custom_id=f"cls-ticket:omodal:{option['id']}")
                for question in questions[:5]:
                    style = discord.TextStyle.paragraph if question.get("kind") == "paragraph" else discord.TextStyle.short
                    modal.add_item(discord.ui.TextInput(label=str(question.get("label") or "Question")[:45], custom_id=str(question.get("label") or "Question")[:45], style=style, required=bool(question.get("required", True)), placeholder=question.get("placeholder") or None))
                await interaction.response.send_modal(modal)
                return
            await self._spawn(interaction, panel, {}, option.get("category_id"))
            return
        panel = await load_panel(panel_id)
        if panel is None or panel["guild_id"] != interaction.guild.id:
            await interaction.response.send_message("This panel is not available.", ephemeral=True)
            return
        data = interaction.data or {}
        if kind == "open" and panel["questions"] and not data.get("components"):
            held = {role.id for role in interaction.user.roles}
            required = set(panel.get("required_role_ids") or [])
            blocked = set(panel.get("blocked_role_ids") or [])
            if required and not required.intersection(held):
                await interaction.response.send_message(_REFUSAL["required_role"], ephemeral=True)
                return
            if blocked.intersection(held):
                await interaction.response.send_message(_REFUSAL["blocked_role"], ephemeral=True)
                return
            modal = discord.ui.Modal(title=(panel["title"] or "Ticket")[:45], custom_id=f"cls-ticket:modal:{panel_id}")
            for question in panel["questions"][:5]:
                style = discord.TextStyle.paragraph if question["kind"] == "paragraph" else discord.TextStyle.short
                maximum = min(4000, max(int(question["max_length"] or 1), int(question["min_length"] or 0) or 1))
                modal.add_item(
                    discord.ui.TextInput(
                        label=question["label"][:45],
                        custom_id=question["id"][:45],
                        style=style,
                        required=question["required"],
                        placeholder=(question["placeholder"] or None),
                        min_length=int(question["min_length"] or 0) or None,
                        max_length=maximum,
                    )
                )
            await interaction.response.send_modal(modal)
            return
        answers = {}
        labels = {question["id"]: question["label"] for question in panel["questions"]}
        for row in data.get("components") or []:
            for component in row.get("components") or []:
                key = labels.get(str(component.get("custom_id") or ""), str(component.get("custom_id") or "Answer"))
                answers[key] = str(component.get("value") or "")
        await self._spawn(interaction, panel, answers, None)
        return

    async def _spawn(self, interaction: discord.Interaction, panel: dict, answers: dict, option_category_id: str | None):
        if interaction.response.is_done():
            await interaction.followup.send("Opening your ticket…", ephemeral=True)
        else:
            await interaction.response.defer(ephemeral=True)
        extra = await panel_advanced(panel["id"])
        known = await known_categories(interaction.guild.id)
        category_id, route_status = route_category(
            rules=extra["rules"],
            answers=answers,
            default_category_id=panel["category_id"],
            known_category_ids=known,
        )
        if route_status == "default" and option_category_id:
            if str(option_category_id) in known:
                category_id = str(option_category_id)
            else:
                route_status = "fallback"
        hours = await category_public(interaction.guild.id, category_id)
        state = support_status(hours or {})
        if hours and not state["open"] and hours.get("hours_outside") == "block":
            await interaction.followup.send(state["notice"] or "Support is currently offline.", ephemeral=True)
            return
        notice = state.get("notice") if hours and not state["open"] else None
        try:
            opened = await open_ticket(
                guild_id=interaction.guild.id,
                category_id=category_id,
                opener_id=interaction.user.id,
                opener_name=interaction.user.display_name,
                opener_avatar=str(interaction.user.display_avatar.url) if interaction.user.display_avatar else "",
                answers=answers,
                panel_id=panel["id"],
                member_role_ids=[role.id for role in interaction.user.roles],
            )
        except TicketError as exc:
            await interaction.followup.send(_refusal(exc), ephemeral=True)
            return
        parent = interaction.guild.get_channel(int(opened["discord_category_id"])) if opened.get("discord_category_id") else None
        me = interaction.guild.me
        if me is None or not me.guild_permissions.manage_channels:
            await mark_degraded(guild_id=interaction.guild.id, ticket_id=opened["id"], reason="missing manage channels")
            await interaction.followup.send("CLS needs Manage Channels before it can open a private ticket.", ephemeral=True)
            return
        staff_roles = [role for role_id in opened["staff_role_ids"] if (role := interaction.guild.get_role(int(role_id)))]
        channel = None
        try:
            channel = await interaction.guild.create_text_channel(
                opened["name"],
                category=parent if isinstance(parent, discord.CategoryChannel) else None,
                overwrites=discord_overwrites(interaction.guild, interaction.user, staff_roles, []),
                reason=f"CLS ticket {opened['number']}",
            )
            mentions = " ".join(role.mention for role in staff_roles) if opened.get("ping_staff") and staff_roles else ""
            tags = await list_tags(interaction.guild.id)
            control = await channel.send(
                content=mentions or None,
                embed=opening_embed(number=opened["number"], opener=interaction.user, category=opened["category_name"], answers=answers),
                view=control_view(opened["id"], closed=False, close_mode=(hours or {}).get("close_mode") or "direct", tags=tags),
                allowed_mentions=discord.AllowedMentions(everyone=False, users=False, roles=bool(mentions)),
            )
            await bind_channel(guild_id=interaction.guild.id, ticket_id=opened["id"], channel_id=channel.id, control_message_id=control.id)
        except Exception as exc:
            if channel is not None:
                try:
                    await channel.delete(reason="CLS ticket setup failed")
                except discord.HTTPException:
                    pass
            await mark_degraded(guild_id=interaction.guild.id, ticket_id=opened["id"], reason=str(exc))
            await interaction.followup.send("The ticket channel could not be created.", ephemeral=True)
            return
        await self._log(interaction.guild.id, "ticket_opened", interaction.user.id, channel.id, f"Ticket {opened['number']} opened")
        if route_status == "fallback":
            await record_ticket_event(guild_id=interaction.guild.id, ticket_id=opened["id"], kind="routing_fallback", actor_id=None, payload={"category_id": panel["category_id"]})
        if notice:
            await channel.send(notice)
        await self._arm(interaction.guild.id, opened["id"])
        await interaction.followup.send(f"Your ticket is open: {channel.mention}", ephemeral=True)

    async def _control(self, interaction: discord.Interaction, action: str, ticket_id: str):
        ticket = await load_ticket(interaction.guild.id, ticket_id)
        if ticket is None:
            await interaction.response.send_message("This ticket is no longer available.", ephemeral=True)
            return
        if action in {"add-pick", "remove-pick", "transfer-pick", "delete-yes"}:
            await self._follow(interaction, ticket, action)
            return
        if action in {"confirm-close", "keep"}:
            if interaction.user.id != int(ticket["opener_id"]):
                await interaction.response.send_message("Only the person who opened this ticket can answer that.", ephemeral=True)
                return
            if action == "keep":
                await reject_close_request(guild_id=interaction.guild.id, ticket_id=ticket_id, actor_id=interaction.user.id)
                await interaction.response.send_message("This ticket stays open.", ephemeral=True)
                return
            await interaction.response.defer(ephemeral=True)
            await self._finish_close(interaction.guild, ticket, interaction.user.id, "Member confirmed close", auto=False)
            await interaction.followup.send("Ticket closed.", ephemeral=True)
            return
        opener_close = action in {"close", "close-reason"} and interaction.user.id == ticket["opener_id"]
        if not self._staff(interaction.user, ticket["staff_role_ids"]) and not opener_close:
            await interaction.response.send_message("Only the support team can do that.", ephemeral=True)
            return
        if action == "ask-close":
            marked = await mark_close_request(guild_id=interaction.guild.id, ticket_id=ticket_id, actor_id=interaction.user.id, message="")
            channel = interaction.guild.get_channel(int(ticket["channel_id"])) if ticket.get("channel_id") else None
            if channel is not None:
                await channel.send("Can this ticket be closed?", view=close_request_view(ticket_id))
            if marked.get("timeout_minutes"):
                await arm_close_request(guild_id=interaction.guild.id, ticket_id=ticket_id, minutes=int(marked["timeout_minutes"]))
            await self._log(interaction.guild.id, "ticket_close_requested", interaction.user.id, ticket.get("channel_id"), f"Ticket {ticket['number']} close requested")
            await interaction.response.send_message("The member can confirm or keep the ticket open.", ephemeral=True)
            return
        if action == "priority":
            chosen = str(((interaction.data or {}).get("values") or ["normal"])[0])
            try:
                changed = await set_priority(guild_id=interaction.guild.id, ticket_id=ticket_id, priority=chosen, actor_id=interaction.user.id)
            except TicketError as exc:
                await interaction.response.send_message(_refusal(exc), ephemeral=True)
                return
            await self._log(interaction.guild.id, "ticket_priority", interaction.user.id, ticket.get("channel_id"), f"Ticket {ticket['number']} priority {changed['from']} → {changed['to']}")
            await self._refresh_controls(interaction.guild, ticket_id)
            await interaction.response.send_message(f"Priority changed: {changed['from']} → {changed['to']}", ephemeral=True)
            return
        if action == "tag":
            chosen = str(((interaction.data or {}).get("values") or [""])[0])
            from cls_platform.tickets.advanced import tags_for
            import uuid as _uuid

            current = (await tags_for(interaction.guild.id, [_uuid.UUID(ticket_id)])).get(_uuid.UUID(ticket_id), [])
            ids = [item["id"] for item in current if item.get("id")]
            if chosen in ids:
                ids = [item for item in ids if item != chosen]
            else:
                ids.append(chosen)
            try:
                saved = await set_ticket_tags(guild_id=interaction.guild.id, ticket_id=ticket_id, tag_ids=ids, actor_id=interaction.user.id)
            except TicketError as exc:
                await interaction.response.send_message(_refusal(exc), ephemeral=True)
                return
            names = ", ".join(item["name"] for item in saved) or "none"
            await self._refresh_controls(interaction.guild, ticket_id)
            await interaction.response.send_message(f"Tags: {names}", ephemeral=True)
            return
        if action == "close":
            modal = discord.ui.Modal(title="Close ticket", custom_id=f"cls-t:close-reason:{ticket_id}")
            modal.add_item(discord.ui.TextInput(label="Close reason", custom_id="reason", required=True, max_length=200, placeholder="Resolved"))
            await interaction.response.send_modal(modal)
            return
        if action == "close-reason":
            reason = ""
            for row in (interaction.data or {}).get("components") or []:
                for component in row.get("components") or []:
                    reason = str(component.get("value") or "")
            await interaction.response.defer(ephemeral=True)
            await self._finish_close(interaction.guild, ticket, interaction.user.id, reason.strip(), auto=False)
            await interaction.followup.send("Ticket closed.", ephemeral=True)
            return
        if action == "add":
            view = discord.ui.View(timeout=120)
            view.add_item(discord.ui.UserSelect(placeholder="Member to add", custom_id=f"cls-t:add-pick:{ticket_id}", min_values=1, max_values=1))
            await interaction.response.send_message("Choose a member to add.", view=view, ephemeral=True)
            return
        if action == "remove":
            view = discord.ui.View(timeout=120)
            view.add_item(discord.ui.UserSelect(placeholder="Member to remove", custom_id=f"cls-t:remove-pick:{ticket_id}", min_values=1, max_values=1))
            await interaction.response.send_message("Choose a member to remove.", view=view, ephemeral=True)
            return
        if action == "transfer":
            from cls_platform.tickets.store import workspace

            home = await workspace(interaction.guild.id)
            options = [
                discord.SelectOption(label=item["name"][:100], value=item["id"])
                for item in home["categories"]
                if item["id"] != ticket["category_id"]
            ][:25]
            if not options:
                await interaction.response.send_message("There is no other team to transfer to.", ephemeral=True)
                return
            view = discord.ui.View(timeout=120)
            view.add_item(discord.ui.Select(placeholder="Team", custom_id=f"cls-t:transfer-pick:{ticket_id}", options=options))
            await interaction.response.send_message("Transfer this ticket.", view=view, ephemeral=True)
            return
        if action == "delete":
            view = discord.ui.View(timeout=60)
            view.add_item(discord.ui.Button(label="Delete channel", style=discord.ButtonStyle.danger, custom_id=f"cls-t:delete-yes:{ticket_id}"))
            await interaction.response.send_message("Delete this ticket channel? The transcript stays saved.", view=view, ephemeral=True)
            return
        await interaction.response.defer(ephemeral=True)
        try:
            if action == "claim":
                await claim_ticket(guild_id=interaction.guild.id, ticket_id=ticket_id, actor_id=interaction.user.id)
                await self._log(interaction.guild.id, "ticket_claimed", interaction.user.id, ticket.get("channel_id"), f"Ticket {ticket['number']} claimed")
            elif action == "unclaim":
                await unclaim_ticket(guild_id=interaction.guild.id, ticket_id=ticket_id, actor_id=interaction.user.id)
                await self._log(interaction.guild.id, "ticket_unclaimed", interaction.user.id, ticket.get("channel_id"), f"Ticket {ticket['number']} unclaimed")
            elif action == "reopen":
                await reopen_ticket(guild_id=interaction.guild.id, ticket_id=ticket_id, actor_id=interaction.user.id)
                await self._sync_access(interaction.guild, await load_ticket(interaction.guild.id, ticket_id))
                await self._log(interaction.guild.id, "ticket_reopened", interaction.user.id, ticket.get("channel_id"), f"Ticket {ticket['number']} reopened")
                await self._arm(interaction.guild.id, ticket_id)
            elif action == "transcript":
                await self._write_transcript(interaction.guild, ticket, interaction.user.id, deliver=True)
            else:
                await interaction.followup.send("That control is not available.", ephemeral=True)
                return
        except TicketError as exc:
            await interaction.followup.send(_refusal(exc), ephemeral=True)
            return
        await self._refresh_controls(interaction.guild, ticket_id)
        if action != "transcript":
            await interaction.followup.send("Updated.", ephemeral=True)

    async def _follow(self, interaction: discord.Interaction, ticket: dict, action: str):
        if not self._staff(interaction.user, ticket["staff_role_ids"]):
            await interaction.response.send_message("Only the support team can do that.", ephemeral=True)
            return
        values = (interaction.data or {}).get("values") or []
        if not values and action != "delete-yes":
            await interaction.response.send_message("Choose someone first.", ephemeral=True)
            return
        await interaction.response.defer(ephemeral=True)
        try:
            if action == "add-pick":
                member = interaction.guild.get_member(int(values[0])) or await interaction.guild.fetch_member(int(values[0]))
                await add_participant(guild_id=interaction.guild.id, ticket_id=ticket["id"], user_id=member.id, actor_id=interaction.user.id)
                await self._sync_access(interaction.guild, await load_ticket(interaction.guild.id, ticket["id"]))
            elif action == "remove-pick":
                await remove_participant(guild_id=interaction.guild.id, ticket_id=ticket["id"], user_id=int(values[0]), actor_id=interaction.user.id)
                await self._sync_access(interaction.guild, await load_ticket(interaction.guild.id, ticket["id"]))
            elif action == "transfer-pick":
                moved = await transfer_ticket(guild_id=interaction.guild.id, ticket_id=ticket["id"], category_id=values[0], actor_id=interaction.user.id)
                await self._sync_access(interaction.guild, await load_ticket(interaction.guild.id, ticket["id"]), moved)
                await self._log(interaction.guild.id, "ticket_transferred", interaction.user.id, ticket.get("channel_id"), f"Ticket {ticket['number']} transferred to {moved['category_name']}")
            elif action == "delete-yes":
                await self._write_transcript(interaction.guild, ticket, interaction.user.id, deliver=True)
                deleted = await mark_deleted(guild_id=interaction.guild.id, ticket_id=ticket["id"], actor_id=interaction.user.id)
                channel = interaction.guild.get_channel(int(deleted["channel_id"])) if deleted and deleted.get("channel_id") else None
                if channel is not None:
                    await channel.delete(reason="CLS ticket deleted")
                await self._log(interaction.guild.id, "ticket_deleted", interaction.user.id, None, f"Ticket {ticket['number']} deleted")
                await interaction.followup.send("Ticket channel deleted. The transcript is still stored.", ephemeral=True)
                return
        except (TicketError, discord.HTTPException) as exc:
            message = _refusal(exc) if isinstance(exc, TicketError) else "Discord refused that permission change."
            await interaction.followup.send(message, ephemeral=True)
            return
        await self._refresh_controls(interaction.guild, ticket["id"])
        await interaction.followup.send("Updated.", ephemeral=True)

    async def _sync_access(self, guild, ticket: dict | None, moved: dict | None = None):
        if ticket is None or not ticket.get("channel_id"):
            return
        channel = guild.get_channel(int(ticket["channel_id"]))
        if channel is None:
            return
        opener = guild.get_member(int(ticket["opener_id"]))
        if opener is None:
            try:
                opener = await guild.fetch_member(int(ticket["opener_id"]))
            except discord.HTTPException:
                return
        source = moved or ticket
        current_ids = {int(role_id) for role_id in (source.get("staff_role_ids") or [])}
        staff_roles = [role for role_id in current_ids if (role := guild.get_role(int(role_id)))]
        deny_roles = [
            role
            for role_id in (moved or {}).get("previous_staff_role_ids") or []
            if int(role_id) not in current_ids and (role := guild.get_role(int(role_id)))
        ]
        extra_ids = source.get("participants") or await participants(guild.id, ticket["id"])
        extras = []
        for user_id in extra_ids:
            member = guild.get_member(int(user_id))
            if member is None:
                try:
                    member = await guild.fetch_member(int(user_id))
                except discord.HTTPException:
                    continue
            extras.append(member)
        parent = None
        category_id = source.get("discord_category_id") or ticket.get("discord_category_id")
        if category_id:
            found = guild.get_channel(int(category_id))
            if isinstance(found, discord.CategoryChannel):
                parent = found
        await channel.edit(overwrites=discord_overwrites(guild, opener, staff_roles, extras, deny_roles), category=parent)

    async def _refresh_controls(self, guild, ticket_id: str):
        ticket = await load_ticket(guild.id, ticket_id)
        if ticket is None or not ticket.get("channel_id") or not ticket.get("control_message_id"):
            return
        channel = guild.get_channel(int(ticket["channel_id"]))
        if channel is None:
            return
        try:
            message = await channel.fetch_message(int(ticket["control_message_id"]))
        except discord.HTTPException:
            return
        closed = ticket["status"] != "open"
        tags = await list_tags(guild.id)
        await message.edit(view=control_view(ticket_id, closed=closed, close_mode=ticket.get("close_mode") or "direct", tags=tags))

    async def _write_transcript(self, guild, ticket: dict, actor_id: int | None, *, deliver: bool):
        stored = await transcript(guild.id, ticket["id"])
        opener = guild.get_member(int(ticket["opener_id"]))
        assignee = guild.get_member(int(ticket["assignee_id"])) if ticket.get("assignee_id") else None
        messages = stored["messages"]
        if stored["lines"] and not messages:
            messages = [{"display_name": "Form", "content": line["body"], "created_at": ticket.get("opened_at"), "attachments": [], "embeds": []} for line in stored["lines"]]
        html = render_html(
            number=ticket["number"],
            guild_name=guild.name,
            category=ticket.get("category_name") or "",
            opener=opener.display_name if opener else "Member",
            assignee=assignee.display_name if assignee else "",
            reason=stored.get("close_reason") or ticket.get("close_reason") or "",
            opened=ticket.get("opened_at"),
            closed=datetime.now(timezone.utc),
            messages=messages,
        )
        await save_html(guild_id=guild.id, ticket_id=ticket["id"], html=html, actor_id=actor_id)
        if not deliver:
            return html
        settings = await guild_settings(guild.id)
        destination = guild.get_channel(int(settings["transcript_channel_id"])) if settings.get("transcript_channel_id") else None
        file = discord.File(fp=_bytes(html), filename=f"ticket-{ticket['number']}.html")
        if destination is not None:
            try:
                await destination.send(content=f"Transcript for ticket {ticket['number']}", file=file)
            except discord.HTTPException:
                pass
        if opener is not None:
            try:
                await opener.send(content=f"Transcript for ticket {ticket['number']} in {guild.name}.", file=discord.File(fp=_bytes(html), filename=f"ticket-{ticket['number']}.html"))
            except discord.HTTPException:
                pass
        return html

    async def _finish_close(self, guild, ticket: dict, actor_id: int | None, reason: str, *, auto: bool):
        if not reason:
            return
        try:
            await close_ticket(guild_id=guild.id, ticket_id=ticket["id"], actor_id=actor_id or (guild.me.id if guild.me else ticket["opener_id"]), reason=reason)
        except TicketError:
            return
        fresh = await load_ticket(guild.id, ticket["id"])
        await self._write_transcript(guild, fresh or ticket, actor_id, deliver=True)
        await self._refresh_controls(guild, ticket["id"])
        await self._log(
            guild.id,
            "ticket_auto_closed" if auto else "ticket_closed",
            actor_id,
            ticket.get("channel_id"),
            f"Ticket {ticket['number']} closed: {reason}",
        )


def _bytes(html: str):
    import io

    return io.BytesIO(html.encode("utf-8"))


async def setup(bot):
    await bot.add_cog(TicketsV2(bot))


async def apply_dashboard_action(bot, *, guild_id: int, ticket_id: str, action: str, actor_id: int, reason: str | None = None, category_id: str | None = None, user_id: int | None = None, priority: str | None = None, tag_ids: list[str] | None = None, note: str | None = None, note_id: str | None = None, reply_id: str | None = None) -> dict:
    """Dashboard controls use the same claim, close, transfer, and permission paths as Discord."""
    cog = bot.get_cog("TicketsV2")
    if cog is None:
        raise DeliveryError("Tickets are not running.")
    guild = bot.get_guild(int(guild_id))
    if guild is None:
        raise DeliveryError("This server is not available to CLS right now.")
    ticket = await load_ticket(guild_id, ticket_id)
    if ticket is None:
        raise TicketError("missing")
    if action == "claim":
        await claim_ticket(guild_id=guild_id, ticket_id=ticket_id, actor_id=actor_id)
        await cog._log(guild_id, "ticket_claimed", actor_id, ticket.get("channel_id"), f"Ticket {ticket['number']} claimed")
    elif action == "unclaim":
        await unclaim_ticket(guild_id=guild_id, ticket_id=ticket_id, actor_id=actor_id)
        await cog._log(guild_id, "ticket_unclaimed", actor_id, ticket.get("channel_id"), f"Ticket {ticket['number']} unclaimed")
    elif action == "close":
        await cog._finish_close(guild, ticket, actor_id, (reason or "").strip(), auto=False)
    elif action == "reopen":
        await reopen_ticket(guild_id=guild_id, ticket_id=ticket_id, actor_id=actor_id)
        await cog._sync_access(guild, await load_ticket(guild_id, ticket_id))
        await cog._log(guild_id, "ticket_reopened", actor_id, ticket.get("channel_id"), f"Ticket {ticket['number']} reopened")
        await cog._arm(guild_id, ticket_id)
    elif action == "transfer":
        if not category_id:
            raise TicketError("category_missing")
        moved = await transfer_ticket(guild_id=guild_id, ticket_id=ticket_id, category_id=category_id, actor_id=actor_id)
        await cog._sync_access(guild, await load_ticket(guild_id, ticket_id), moved)
        await cog._log(guild_id, "ticket_transferred", actor_id, ticket.get("channel_id"), f"Ticket {ticket['number']} transferred to {moved['category_name']}")
    elif action == "add":
        if not user_id:
            raise TicketError("missing")
        await add_participant(guild_id=guild_id, ticket_id=ticket_id, user_id=user_id, actor_id=actor_id)
        await cog._sync_access(guild, await load_ticket(guild_id, ticket_id))
    elif action == "remove":
        if not user_id:
            raise TicketError("missing")
        await remove_participant(guild_id=guild_id, ticket_id=ticket_id, user_id=user_id, actor_id=actor_id)
        await cog._sync_access(guild, await load_ticket(guild_id, ticket_id))
    elif action == "priority":
        changed = await set_priority(guild_id=guild_id, ticket_id=ticket_id, priority=priority or "", actor_id=actor_id)
        await cog._log(guild_id, "ticket_priority", actor_id, ticket.get("channel_id"), f"Ticket {ticket['number']} priority {changed['from']} → {changed['to']}")
    elif action == "tags":
        await set_ticket_tags(guild_id=guild_id, ticket_id=ticket_id, tag_ids=tag_ids or [], actor_id=actor_id)
    elif action == "note":
        await add_note(guild_id=guild_id, ticket_id=ticket_id, author_id=actor_id, body=note or "")
    elif action == "note_delete":
        if not note_id:
            raise TicketError("missing")
        await delete_note(guild_id=guild_id, ticket_id=ticket_id, note_id=note_id, actor_id=actor_id, allow_any=True)
    elif action == "ask_close":
        marked = await mark_close_request(guild_id=guild_id, ticket_id=ticket_id, actor_id=actor_id, message=reason or "")
        channel = guild.get_channel(int(ticket["channel_id"])) if ticket.get("channel_id") else None
        if channel is not None:
            text = "Can this ticket be closed?"
            if reason:
                text = f"Can this ticket be closed?\n{reason[:300]}"
            await channel.send(text, view=close_request_view(ticket_id))
        if marked.get("timeout_minutes"):
            await arm_close_request(guild_id=guild_id, ticket_id=ticket_id, minutes=int(marked["timeout_minutes"]))
        await cog._log(guild_id, "ticket_close_requested", actor_id, ticket.get("channel_id"), f"Ticket {ticket['number']} close requested")
    elif action == "reply":
        replies = await list_replies(guild_id)
        chosen = next((item for item in replies if item["id"] == reply_id), None)
        if chosen is None:
            raise TicketError("missing")
        channel = guild.get_channel(int(ticket["channel_id"])) if ticket.get("channel_id") else None
        if channel is None:
            raise DeliveryError("The ticket channel is not available.")
        await channel.send(render_reply(chosen["content"], number=int(ticket["number"]), opener=ticket.get("opener_name") or "member"))
    else:
        raise TicketError("missing")
    if action != "close":
        await cog._refresh_controls(guild, ticket_id)
    fresh = await load_ticket(guild_id, ticket_id)
    return fresh or ticket


async def publish_from_api(bot, guild_id: int, panel: dict, mode: str):
    guild = bot.get_guild(guild_id)
    if guild is None:
        raise DeliveryError("Guild is not available to the bot.")
    try:
        message = await publish_panel(guild, panel, mode=mode)
    except discord.Forbidden as exc:
        raise DeliveryError("CLS cannot post in that channel.") from exc
    if message is None:
        return None
    return message
