"""Tickets V2 HTTP API. Legacy /tickets stays untouched."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field

from api.dependencies import get_bot
from cls_platform.messages.deliver import DeliveryError
from cls_platform.tickets.store import (
    TicketError,
    blacklist_user,
    claim_ticket,
    close_ticket,
    create_category,
    create_panel,
    load_panel,
    open_ticket,
    reopen_ticket,
    set_limits,
    set_publish,
    transcript,
    unblacklist_user,
    category_counts,
    delete_panel,
    duplicate_panel,
    list_blacklist,
    list_queue,
    list_transcripts,
    save_panel,
    ticket_detail,
    update_category,
    update_panel_text,
    workspace,
)

router = APIRouter()


class CategoryBody(BaseModel):
    name: str
    discord_category_id: str | None = None
    staff_role_ids: list[str] = Field(default_factory=list)
    name_format: str | None = None
    ping_staff: bool = True
    required_role_ids: list[str] = Field(default_factory=list)
    blocked_role_ids: list[str] = Field(default_factory=list)


class PanelBody(BaseModel):
    category_id: str
    channel_id: str | None = None
    title: str
    message: str = ""
    button_label: str = "Open ticket"
    questions: list[dict] = Field(default_factory=list)
    required_role_ids: list[str] = Field(default_factory=list)
    blocked_role_ids: list[str] = Field(default_factory=list)
    payload: dict | None = None
    button_emoji: str = ""
    button_style: str = "primary"


class OpenBody(BaseModel):
    category_id: str
    opener_id: str
    answers: dict = Field(default_factory=dict)


class CloseBody(BaseModel):
    actor_id: str
    reason: str


class LimitsBody(BaseModel):
    cooldown_seconds: int = 60
    max_open: int = 1
    auto_close_hours: int | None = None
    grace_minutes: int | None = None
    transcript_channel_id: str | None = None
    name_format: str | None = None


class BlacklistBody(BaseModel):
    user_id: str
    reason: str = ""
    display_name: str = ""
    avatar: str = ""


def _int(value: str | None) -> int | None:
    return int(value) if value else None


@router.get("/{guild_id}/tickets/v2")
async def tickets_home(guild_id: int):
    return await workspace(guild_id)


@router.post("/{guild_id}/tickets/v2/categories")
async def tickets_category(guild_id: int, body: CategoryBody):
    return await create_category(
        guild_id=guild_id,
        name=body.name,
        discord_category_id=_int(body.discord_category_id),
        staff_role_ids=[int(item) for item in body.staff_role_ids if item.isdigit()],
        name_format=body.name_format,
        ping_staff=body.ping_staff,
        required_role_ids=[int(item) for item in body.required_role_ids if str(item).isdigit()],
        blocked_role_ids=[int(item) for item in body.blocked_role_ids if str(item).isdigit()],
    )


@router.post("/{guild_id}/tickets/v2/panels")
async def tickets_panel(guild_id: int, body: PanelBody):
    return await create_panel(
        guild_id=guild_id,
        category_id=body.category_id,
        channel_id=_int(body.channel_id),
        title=body.title,
        message=body.message,
        button_label=body.button_label,
        questions=body.questions,
        required_role_ids=[int(item) for item in body.required_role_ids if str(item).isdigit()],
        blocked_role_ids=[int(item) for item in body.blocked_role_ids if str(item).isdigit()],
        payload=body.payload,
        button_emoji=body.button_emoji,
        button_style=body.button_style,
    )


@router.patch("/{guild_id}/tickets/v2/settings")
async def tickets_settings(guild_id: int, body: LimitsBody):
    provided = body.model_dump(exclude_unset=True)
    try:
        return await set_limits(
            guild_id=guild_id,
            cooldown_seconds=body.cooldown_seconds,
            max_open=body.max_open,
            auto_close_hours=body.auto_close_hours if "auto_close_hours" in provided else None,
            grace_minutes=body.grace_minutes if "grace_minutes" in provided else None,
            transcript_channel_id=_int(body.transcript_channel_id) if "transcript_channel_id" in provided else None,
            name_format=body.name_format if "name_format" in provided else None,
        )
    except TicketError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


class PanelTextBody(BaseModel):
    title: str | None = None
    message: str | None = None
    payload: dict | None = None


class PublishBody(BaseModel):
    channel_id: str | None = None
    mode: str = "publish"


@router.patch("/{guild_id}/tickets/v2/panels/{panel_id}")
async def tickets_panel_text(guild_id: int, panel_id: str, body: PanelTextBody):
    try:
        return await update_panel_text(guild_id=guild_id, panel_id=panel_id, title=body.title, message=body.message, payload=body.payload)
    except TicketError as exc:
        raise HTTPException(status_code=404, detail="Panel not found") from exc


@router.post("/{guild_id}/tickets/v2/panels/{panel_id}/publish")
async def tickets_publish(guild_id: int, panel_id: str, body: PublishBody, bot=Depends(get_bot)):
    panel = await load_panel(panel_id)
    if panel is None or panel["guild_id"] != guild_id:
        raise HTTPException(status_code=404, detail="Panel not found")
    if body.channel_id and str(body.channel_id).isdigit():
        panel["channel_id"] = int(body.channel_id)
    from cogs.tickets_v2 import publish_from_api

    mode = body.mode if body.mode in {"publish", "update", "resend"} else "publish"
    try:
        message = await publish_from_api(bot, guild_id, panel, "publish" if mode == "resend" else mode)
    except DeliveryError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    if message is None:
        return await set_publish(guild_id=guild_id, panel_id=panel_id, channel_id=None, message_id=None, status="missing")
    return await set_publish(
        guild_id=guild_id,
        panel_id=panel_id,
        channel_id=int(message.channel.id),
        message_id=int(message.id),
        status="published",
    )


@router.post("/{guild_id}/tickets/v2/blacklist")
async def tickets_blacklist(guild_id: int, body: BlacklistBody, request: Request):
    actor = getattr(getattr(request.state, "dashboard_auth", None), "user_id", None)
    return await blacklist_user(
        guild_id=guild_id,
        user_id=int(body.user_id),
        reason=body.reason,
        actor_id=int(actor) if actor else None,
        display_name=body.display_name,
        avatar=body.avatar,
    )


@router.delete("/{guild_id}/tickets/v2/blacklist/{user_id}")
async def tickets_unblacklist(guild_id: int, user_id: int):
    await unblacklist_user(guild_id=guild_id, user_id=user_id)
    return {"removed": str(user_id)}


@router.post("/{guild_id}/tickets/v2/open")
async def tickets_open(guild_id: int, body: OpenBody):
    try:
        return await open_ticket(
            guild_id=guild_id,
            category_id=body.category_id,
            opener_id=int(body.opener_id),
            answers=body.answers,
        )
    except TicketError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.post("/{guild_id}/tickets/v2/{ticket_id}/claim")
async def tickets_claim(guild_id: int, ticket_id: str, actor_id: str):
    try:
        return await claim_ticket(guild_id=guild_id, ticket_id=ticket_id, actor_id=int(actor_id))
    except TicketError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/{guild_id}/tickets/v2/{ticket_id}/close")
async def tickets_close(guild_id: int, ticket_id: str, body: CloseBody):
    try:
        return await close_ticket(guild_id=guild_id, ticket_id=ticket_id, actor_id=int(body.actor_id), reason=body.reason)
    except TicketError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.post("/{guild_id}/tickets/v2/{ticket_id}/reopen")
async def tickets_reopen(guild_id: int, ticket_id: str, actor_id: str):
    try:
        return await reopen_ticket(guild_id=guild_id, ticket_id=ticket_id, actor_id=int(actor_id))
    except TicketError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


def _ids(values: list[str] | None) -> list[int] | None:
    if values is None:
        return None
    return [int(item) for item in values if str(item).isdigit()]


def _named(bot, guild_id: int, rows: list[dict]) -> list[dict]:
    guild = bot.get_guild(int(guild_id)) if bot is not None else None

    def person(user_id: str | None, fallback: str = "") -> tuple[str, str]:
        if guild is None or not user_id:
            return fallback, ""
        member = guild.get_member(int(user_id))
        if member is None:
            return fallback, ""
        avatar = str(member.display_avatar.url) if getattr(member, "display_avatar", None) else ""
        return member.display_name, avatar

    for row in rows:
        if not row.get("opener_name"):
            name, avatar = person(row.get("opener_id"), "Member")
            row["opener_name"] = name or "Member"
            if avatar:
                row["opener_avatar"] = avatar
        assignee_name, _avatar = person(row.get("assignee_id"), "Staff" if row.get("assignee_id") else "")
        row["assignee_name"] = assignee_name
    return rows


@router.get("/{guild_id}/tickets/v2/queue")
async def tickets_queue(guild_id: int, bot=Depends(get_bot)):
    return {"tickets": _named(bot, guild_id, await list_queue(guild_id))}


@router.get("/{guild_id}/tickets/v2/transcripts")
async def tickets_transcripts(guild_id: int, bot=Depends(get_bot)):
    return {"transcripts": _named(bot, guild_id, await list_transcripts(guild_id))}


@router.get("/{guild_id}/tickets/v2/blacklist")
async def tickets_blocklist(guild_id: int, bot=Depends(get_bot)):
    rows = await list_blacklist(guild_id)
    guild = bot.get_guild(int(guild_id)) if bot is not None else None
    for row in rows:
        member = guild.get_member(int(row["user_id"])) if guild and row.get("user_id") else None
        row["display_name"] = member.display_name if member else "Member"
        row["avatar"] = str(member.display_avatar.url) if member and getattr(member, "display_avatar", None) else ""
        actor = guild.get_member(int(row["actor_id"])) if guild and row.get("actor_id") else None
        row["actor_name"] = actor.display_name if actor else ""
    return {"blocked": rows}


@router.get("/{guild_id}/tickets/v2/members")
async def tickets_members(guild_id: int, q: str = "", bot=Depends(get_bot)):
    guild = bot.get_guild(int(guild_id)) if bot is not None else None
    if guild is None:
        return {"members": []}
    needle = q.strip().lower()
    found = []
    if needle:
        try:
            found = await guild.query_members(query=needle, limit=8)
        except Exception:
            found = [member for member in guild.members if needle in (member.display_name or "").lower() or needle in (member.name or "").lower()][:8]
    return {
        "members": [
            {
                "id": str(member.id),
                "display_name": member.display_name,
                "username": member.name,
                "avatar": str(member.display_avatar.url) if member.display_avatar else "",
            }
            for member in found
        ]
    }


@router.get("/{guild_id}/tickets/v2/categories/summary")
async def tickets_category_summary(guild_id: int):
    return {"counts": await category_counts(guild_id)}


class CategoryUpdate(BaseModel):
    name: str | None = None
    discord_category_id: str | None = None
    clear_discord_category: bool = False
    staff_role_ids: list[str] | None = None
    name_format: str | None = None
    ping_staff: bool | None = None
    required_role_ids: list[str] | None = None
    blocked_role_ids: list[str] | None = None
    close_mode: str | None = None
    close_timeout_minutes: int | None = None
    clear_close_timeout: bool = False
    hours_mode: str | None = None
    hours_timezone: str | None = None
    hours_days: int | None = None
    hours_start: str | None = None
    hours_end: str | None = None
    hours_outside: str | None = None


@router.patch("/{guild_id}/tickets/v2/categories/{category_id}")
async def tickets_category_update(guild_id: int, category_id: str, body: CategoryUpdate):
    try:
        return await update_category(
            guild_id=guild_id,
            category_id=category_id,
            name=body.name,
            discord_category_id=None if body.clear_discord_category else _int(body.discord_category_id),
            staff_role_ids=_ids(body.staff_role_ids),
            name_format=body.name_format,
            ping_staff=body.ping_staff,
            required_role_ids=_ids(body.required_role_ids),
            blocked_role_ids=_ids(body.blocked_role_ids),
            discord_category_set=body.clear_discord_category or body.discord_category_id is not None,
            close_mode=body.close_mode,
            close_timeout_minutes=None if body.clear_close_timeout else body.close_timeout_minutes,
            close_timeout_set=body.clear_close_timeout or body.close_timeout_minutes is not None,
            hours={
                "hours_mode": body.hours_mode,
                "hours_timezone": body.hours_timezone,
                "hours_days": body.hours_days,
                "hours_start": body.hours_start,
                "hours_end": body.hours_end,
                "hours_outside": body.hours_outside,
            },
        )
    except TicketError as exc:
        if str(exc) == "timezone":
            raise HTTPException(status_code=422, detail="That timezone is not recognized.") from exc
        raise HTTPException(status_code=404, detail="Category not found") from exc


class PanelSaveBody(BaseModel):
    category_id: str | None = None
    channel_id: str | None = None
    clear_channel: bool = False
    title: str | None = None
    message: str | None = None
    button_label: str | None = None
    button_emoji: str | None = None
    button_style: str | None = None
    questions: list[dict] | None = None
    required_role_ids: list[str] | None = None
    blocked_role_ids: list[str] | None = None
    payload: dict | None = None
    panel_type: str | None = None
    options: list[dict] | None = None
    rules: list[dict] | None = None


def _ticket_detail(exc: TicketError) -> str:
    return {
        "priority": "Choose Low, Normal, High, or Urgent.",
        "tag_missing": "That tag is no longer available.",
        "tag_name": "A tag needs a name.",
        "note_empty": "Write a note before saving.",
        "note_forbidden": "You can only delete your own note.",
        "reply": "A saved reply needs a name and some text.",
        "timezone": "That timezone is not recognized.",
        "missing": "This ticket is no longer available.",
    }.get(str(exc), "That ticket action could not be completed.")


async def _shown_panel(guild_id: int, panel_id: str) -> dict | None:
    from cls_platform.tickets.advanced import panel_advanced

    panel = _public_panel(await load_panel(panel_id))
    if panel is None or panel["guild_id"] != guild_id:
        return None
    extra = await panel_advanced(panel_id)
    panel.update(extra)
    rules = []
    for rule in extra["rules"]:
        rules.append(f"When {rule['question_label']} {rule['operator']} {rule['value']}")
    panel["routing_summary"] = rules
    return panel


def _public_panel(panel: dict | None) -> dict | None:
    if panel is None:
        return None
    shown = dict(panel)
    for key in ("channel_id", "published_message_id", "discord_category_id"):
        if shown.get(key) is not None:
            shown[key] = str(shown[key])
    for key in ("required_role_ids", "blocked_role_ids", "staff_role_ids"):
        shown[key] = [str(item) for item in shown.get(key) or []]
    return shown


@router.get("/{guild_id}/tickets/v2/panels/{panel_id}")
async def tickets_panel_get(guild_id: int, panel_id: str):
    panel = await load_panel(panel_id)
    if panel is None or panel["guild_id"] != guild_id:
        raise HTTPException(status_code=404, detail="Panel not found")
    return await _shown_panel(guild_id, panel_id)


@router.put("/{guild_id}/tickets/v2/panels/{panel_id}")
async def tickets_panel_save(guild_id: int, panel_id: str, body: PanelSaveBody):
    try:
        await save_panel(
            guild_id=guild_id,
            panel_id=panel_id,
            category_id=body.category_id,
            channel_id=None if body.clear_channel else _int(body.channel_id),
            title=body.title,
            message=body.message,
            button_label=body.button_label,
            button_emoji=body.button_emoji,
            button_style=body.button_style,
            questions=body.questions,
            required_role_ids=_ids(body.required_role_ids),
            blocked_role_ids=_ids(body.blocked_role_ids),
            payload=body.payload,
            channel_set=body.clear_channel or body.channel_id is not None,
        )
        from cls_platform.tickets.advanced import save_panel_advanced

        await save_panel_advanced(guild_id=guild_id, panel_id=panel_id, panel_type=body.panel_type, options=body.options, rules=body.rules)
    except TicketError as exc:
        raise HTTPException(status_code=404, detail="Panel not found") from exc
    return await _shown_panel(guild_id, panel_id)


@router.post("/{guild_id}/tickets/v2/panels/{panel_id}/duplicate")
async def tickets_panel_duplicate(guild_id: int, panel_id: str):
    try:
        return await duplicate_panel(guild_id=guild_id, panel_id=panel_id)
    except TicketError as exc:
        raise HTTPException(status_code=404, detail="Panel not found") from exc


@router.delete("/{guild_id}/tickets/v2/panels/{panel_id}")
async def tickets_panel_delete(guild_id: int, panel_id: str, bot=Depends(get_bot)):
    try:
        removed = await delete_panel(guild_id=guild_id, panel_id=panel_id)
    except TicketError as exc:
        raise HTTPException(status_code=404, detail="Panel not found") from exc
    guild = bot.get_guild(int(guild_id)) if bot is not None else None
    if guild and removed.get("channel_id") and removed.get("message_id"):
        channel = guild.get_channel(int(removed["channel_id"]))
        if channel is not None:
            try:
                message = await channel.fetch_message(int(removed["message_id"]))
                await message.delete()
            except Exception:
                pass
    return {"deleted": True}


@router.get("/{guild_id}/tickets/v2/{ticket_id}/detail")
async def tickets_detail(guild_id: int, ticket_id: str, bot=Depends(get_bot)):
    try:
        detail = await ticket_detail(guild_id, ticket_id)
    except TicketError as exc:
        raise HTTPException(status_code=404, detail="Ticket not found") from exc
    _named(bot, guild_id, [detail])
    guild = bot.get_guild(int(guild_id)) if bot is not None else None
    names = {}
    if guild:
        for event in detail["events"]:
            actor = event.get("actor_id")
            if not actor or actor in names:
                continue
            member = guild.get_member(int(actor))
            if member:
                names[actor] = member.display_name
    for event in detail["events"]:
        event["actor_name"] = names.get(event.get("actor_id") or "", "")
    detail["participant_names"] = []
    if guild:
        for user_id in detail["participants"]:
            member = guild.get_member(int(user_id))
            detail["participant_names"].append({"id": user_id, "display_name": member.display_name if member else "Member", "avatar": str(member.display_avatar.url) if member and member.display_avatar else ""})
    return detail


class ActionBody(BaseModel):
    action: str
    reason: str = ""
    category_id: str | None = None
    user_id: str | None = None
    priority: str | None = None
    tag_ids: list[str] | None = None
    note: str | None = None
    note_id: str | None = None
    reply_id: str | None = None


@router.post("/{guild_id}/tickets/v2/{ticket_id}/action")
async def tickets_action(guild_id: int, ticket_id: str, body: ActionBody, request: Request, bot=Depends(get_bot)):
    actor = getattr(getattr(request.state, "dashboard_auth", None), "user_id", None)
    if not actor:
        raise HTTPException(status_code=401, detail="Authentication required")
    from cogs.tickets_v2 import apply_dashboard_action
    from cls_platform.messages.deliver import DeliveryError

    try:
        return await apply_dashboard_action(
            bot,
            guild_id=guild_id,
            ticket_id=ticket_id,
            action=body.action,
            actor_id=int(actor),
            reason=body.reason,
            category_id=body.category_id,
            user_id=int(body.user_id) if body.user_id and str(body.user_id).isdigit() else None,
            priority=body.priority,
            tag_ids=body.tag_ids,
            note=body.note,
            note_id=body.note_id,
            reply_id=body.reply_id,
        )
    except TicketError as exc:
        raise HTTPException(status_code=409, detail=_ticket_detail(exc)) from exc
    except DeliveryError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


class TagBody(BaseModel):
    name: str
    position: int | None = None


class ReplyBody(BaseModel):
    name: str
    content: str


@router.get("/{guild_id}/tickets/v2/tags")
async def tickets_tags(guild_id: int):
    from cls_platform.tickets.advanced import list_tags

    return {"tags": await list_tags(guild_id)}


@router.post("/{guild_id}/tickets/v2/tags")
async def tickets_tag_create(guild_id: int, body: TagBody):
    from cls_platform.tickets.advanced import save_tag

    try:
        return await save_tag(guild_id=guild_id, tag_id=None, name=body.name, position=body.position)
    except TicketError as exc:
        raise HTTPException(status_code=422, detail=_ticket_detail(exc)) from exc


@router.patch("/{guild_id}/tickets/v2/tags/{tag_id}")
async def tickets_tag_update(guild_id: int, tag_id: str, body: TagBody):
    from cls_platform.tickets.advanced import save_tag

    try:
        return await save_tag(guild_id=guild_id, tag_id=tag_id, name=body.name, position=body.position)
    except TicketError as exc:
        raise HTTPException(status_code=422, detail=_ticket_detail(exc)) from exc


@router.delete("/{guild_id}/tickets/v2/tags/{tag_id}")
async def tickets_tag_delete(guild_id: int, tag_id: str):
    from cls_platform.tickets.advanced import archive_tag

    try:
        return await archive_tag(guild_id=guild_id, tag_id=tag_id)
    except TicketError as exc:
        raise HTTPException(status_code=404, detail="That tag is no longer available.") from exc


@router.get("/{guild_id}/tickets/v2/metrics")
async def tickets_metrics(guild_id: int, days: int = 7):
    from datetime import datetime, timezone

    from cls_platform.tickets.advanced import metrics

    window = 30 if days >= 30 else 7
    return await metrics(guild_id, datetime.now(timezone.utc), window)


@router.get("/{guild_id}/tickets/v2/replies")
async def tickets_replies(guild_id: int):
    from cls_platform.tickets.advanced import list_replies

    return {"replies": await list_replies(guild_id)}


@router.post("/{guild_id}/tickets/v2/replies")
async def tickets_reply_create(guild_id: int, body: ReplyBody):
    from cls_platform.tickets.advanced import save_reply

    try:
        return await save_reply(guild_id=guild_id, reply_id=None, name=body.name, content=body.content)
    except TicketError as exc:
        raise HTTPException(status_code=422, detail=_ticket_detail(exc)) from exc


@router.delete("/{guild_id}/tickets/v2/replies/{reply_id}")
async def tickets_reply_delete(guild_id: int, reply_id: str):
    from cls_platform.tickets.advanced import delete_reply

    try:
        await delete_reply(guild_id=guild_id, reply_id=reply_id)
    except TicketError as exc:
        raise HTTPException(status_code=404, detail="That saved reply is no longer available.") from exc
    return {"ok": True}


@router.get("/{guild_id}/tickets/v2/{ticket_id}")
async def tickets_transcript(guild_id: int, ticket_id: str):
    try:
        return await transcript(guild_id, ticket_id)
    except TicketError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
