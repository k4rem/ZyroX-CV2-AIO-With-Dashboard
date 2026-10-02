"""Tickets V2 HTTP API. Legacy /tickets stays untouched."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
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


class BlacklistBody(BaseModel):
    user_id: str


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
async def tickets_blacklist(guild_id: int, body: BlacklistBody):
    return await blacklist_user(guild_id=guild_id, user_id=int(body.user_id))


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


@router.get("/{guild_id}/tickets/v2/{ticket_id}")
async def tickets_transcript(guild_id: int, ticket_id: str):
    try:
        return await transcript(guild_id, ticket_id)
    except TicketError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
