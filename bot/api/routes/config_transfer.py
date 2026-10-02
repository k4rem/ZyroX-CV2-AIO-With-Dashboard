"""Guild configuration export and import."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field

from api.dependencies import get_bot
from cls_platform.config_transfer.schema import MAX_BYTES, TransferError, validate_bundle
from cls_platform.config_transfer.service import apply, build_export, history, plan, preview

router = APIRouter()


class ExportBody(BaseModel):
    modules: list[str] = Field(default_factory=list)


class ImportBody(BaseModel):
    bundle: dict
    modules: list[str] = Field(default_factory=list)
    mappings: dict = Field(default_factory=dict)
    strategy: str = "merge"


def _http(exc: TransferError) -> HTTPException:
    return HTTPException(status_code=422, detail=str(exc))


def _catalog(bot, guild_id: int) -> dict:
    guild = bot.get_guild(int(guild_id)) if bot is not None else None
    if guild is None:
        return {"roles": [], "channels": [], "emojis": []}
    channels = []
    for channel in getattr(guild, "channels", []) or []:
        kind = getattr(channel, "type", None)
        value = getattr(kind, "value", kind)
        channels.append({"id": str(channel.id), "name": getattr(channel, "name", ""), "kind": "category" if value == 4 else "text"})
    return {
        "roles": [{"id": str(role.id), "name": role.name} for role in getattr(guild, "roles", []) or [] if getattr(role, "name", "") != "@everyone"],
        "channels": channels,
        "emojis": [{"id": str(emoji.id), "name": emoji.name} for emoji in getattr(guild, "emojis", []) or []],
    }


def _name(bot, guild_id: int) -> str:
    guild = bot.get_guild(int(guild_id)) if bot is not None else None
    return getattr(guild, "name", "") or ""


def _ref_id(value) -> str:
    if isinstance(value, dict):
        return str(value.get("source_id") or "")
    return str(value or "")


async def _known_messages(bot, guild_id: int, bundle: dict, modules: list[str] | None) -> set[str]:
    """Keep a same-guild publication only when Discord still has that message."""
    source = str((bundle.get("source") or {}).get("guild_id") or "")
    if source != str(guild_id) or bot is None:
        return set()
    guild = bot.get_guild(int(guild_id))
    if guild is None:
        return set()
    bodies = bundle.get("modules") or {}
    chosen = set(modules or bodies.keys())
    pairs: list[tuple[str, str]] = []
    if "tickets" in chosen:
        for panel in (bodies.get("tickets") or {}).get("panels") or []:
            publication = panel.get("publication") or {}
            pairs.append((_ref_id(panel.get("channel")), str(publication.get("message_id") or "")))
    if "role_menus" in chosen:
        for menu in (bodies.get("role_menus") or {}).get("menus") or []:
            publication = menu.get("publication") or {}
            pairs.append((_ref_id(menu.get("channel")), str(publication.get("message_id") or "")))
    known: set[str] = set()
    for channel_id, message_id in pairs:
        if not channel_id.isdigit() or not message_id.isdigit():
            continue
        channel = guild.get_channel(int(channel_id))
        fetch = getattr(channel, "fetch_message", None)
        if fetch is None:
            continue
        try:
            await fetch(int(message_id))
        except Exception:
            continue
        known.add(message_id)
    return known


@router.get("/{guild_id}/config-transfer/preview")
async def transfer_preview(guild_id: int, bot=Depends(get_bot)):
    return await preview(guild_id, _catalog(bot, guild_id))


@router.post("/{guild_id}/config-transfer/export")
async def transfer_export(guild_id: int, body: ExportBody, bot=Depends(get_bot)):
    try:
        return await build_export(guild_id, _name(bot, guild_id), body.modules or None, _catalog(bot, guild_id))
    except TransferError as exc:
        raise _http(exc) from exc


@router.post("/{guild_id}/config-transfer/validate")
async def transfer_validate(guild_id: int, body: ImportBody):
    try:
        if len(str(body.bundle)) > MAX_BYTES:
            raise TransferError("This backup is too large to import.")
        bundle = validate_bundle(body.bundle)
    except TransferError as exc:
        raise _http(exc) from exc
    return {
        "ok": True,
        "source": bundle["source"],
        "exported_at": bundle.get("exported_at"),
        "version": bundle["version"],
        "modules": list(bundle["modules"].keys()),
        "mode": "restore" if str(bundle["source"]["guild_id"]) == str(guild_id) else "transfer",
    }


@router.post("/{guild_id}/config-transfer/plan")
async def transfer_plan(guild_id: int, body: ImportBody, bot=Depends(get_bot)):
    try:
        return await plan(guild_id, _name(bot, guild_id), body.bundle, _catalog(bot, guild_id), body.mappings, body.modules or None, body.strategy)
    except TransferError as exc:
        raise _http(exc) from exc


@router.post("/{guild_id}/config-transfer/apply")
async def transfer_apply(guild_id: int, body: ImportBody, request: Request, bot=Depends(get_bot)):
    actor = getattr(getattr(request.state, "dashboard_auth", None), "user_id", None)
    try:
        actor_id = int(actor) if actor and str(actor).isdigit() else None
    except (TypeError, ValueError):
        actor_id = None
    try:
        known = await _known_messages(bot, guild_id, body.bundle, body.modules or None)
        return await apply(guild_id, _name(bot, guild_id), body.bundle, _catalog(bot, guild_id), body.mappings, body.modules or None, body.strategy, actor_id, known)
    except TransferError as exc:
        raise _http(exc) from exc


@router.get("/{guild_id}/config-transfer/history")
async def transfer_history(guild_id: int):
    return {"imports": await history(guild_id)}
