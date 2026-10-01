"""Tickets V2 HTTP API. Legacy /tickets stays untouched."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from cls_platform.tickets.store import (
    TicketError,
    blacklist_user,
    claim_ticket,
    close_ticket,
    create_category,
    create_panel,
    open_ticket,
    reopen_ticket,
    set_limits,
    transcript,
    unblacklist_user,
    workspace,
)

router = APIRouter()


class CategoryBody(BaseModel):
    name: str
    discord_category_id: str | None = None
    staff_role_ids: list[str] = Field(default_factory=list)


class PanelBody(BaseModel):
    category_id: str
    channel_id: str | None = None
    title: str
    message: str = ""
    button_label: str = "Open ticket"
    questions: list[dict] = Field(default_factory=list)


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
        staff_role_ids=[int(item) for item in body.staff_role_ids],
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
    )


@router.patch("/{guild_id}/tickets/v2/settings")
async def tickets_settings(guild_id: int, body: LimitsBody):
    try:
        return await set_limits(guild_id=guild_id, cooldown_seconds=body.cooldown_seconds, max_open=body.max_open)
    except TicketError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


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
