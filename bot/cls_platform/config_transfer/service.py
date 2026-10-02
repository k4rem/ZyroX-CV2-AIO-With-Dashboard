"""Export, dry-run, apply, and roll back guild configuration."""

from __future__ import annotations

import os
import uuid
from datetime import datetime, timezone

from sqlalchemy import BigInteger, DateTime, Integer, String, select
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from cls_platform.config_transfer.io import apply_module, export_module, summary_of
from cls_platform.config_transfer.mapping import apply_map, blocked_detail, group_preview, impact_for, mapping_rows, unresolved
from cls_platform.config_transfer.schema import (
    MAX_BYTES,
    TransferError,
    empty_bundle,
    scrub_private_media,
    selected,
    validate_bundle,
)
from cls_platform.database import session_scope
from cls_platform.discord_types import snowflake_to_str
from cls_platform.models import Base


class ConfigImportHistory(Base):
    __tablename__ = "config_import_history"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    guild_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    actor_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    source_guild_id: Mapped[str] = mapped_column(String(32), nullable=False)
    source_guild_name: Mapped[str] = mapped_column(String(100), nullable=False, default="")
    modules: Mapped[list] = mapped_column(JSONB, nullable=False)
    result: Mapped[str] = mapped_column(String(32), nullable=False)
    format_version: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class ConfigImportSnapshot(Base):
    __tablename__ = "config_import_snapshots"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    guild_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    modules: Mapped[list] = mapped_column(JSONB, nullable=False)
    bundle: Mapped[dict] = mapped_column(JSONB, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


def lookup_from(catalog: dict | None):
    index = {}
    for kind, key in (("role", "roles"), ("channel", "channels"), ("emoji", "emojis")):
        for item in (catalog or {}).get(key) or []:
            stored = "category" if item.get("kind") == "category" else kind
            index[(stored, str(item.get("id")))] = item.get("name") or ""
            if stored == "category":
                index[("channel", str(item.get("id")))] = item.get("name") or ""
    def lookup(kind: str, source_id: str) -> str:
        return index.get((kind, str(source_id)), "")
    return lookup


async def build_export(guild_id: int, guild_name: str, modules: list[str] | None, catalog: dict | None) -> dict:
    chosen = selected(modules)
    lookup = lookup_from(catalog)
    bundle = empty_bundle(guild_id, guild_name)
    for module_id in chosen:
        bundle["modules"][module_id] = await export_module(guild_id, module_id, lookup)
    return bundle


async def preview(guild_id: int, catalog: dict | None) -> dict:
    lookup = lookup_from(catalog)
    summaries = {}
    for module_id in selected(None):
        try:
            body = await export_module(guild_id, module_id, lookup)
        except Exception:
            body = {}
        summaries[module_id] = summary_of(module_id, body)
    return {"groups": group_preview(summaries)}


def _plan(bundle: dict, target_guild_id: int, current: dict, catalog: dict, choices: dict | None, modules: list[str] | None, strategy: str) -> dict:
    if strategy not in {"merge", "replace"}:
        raise TransferError("Choose Merge / Update or Replace.")
    chosen = [module_id for module_id in selected(modules) if module_id in bundle["modules"]]
    same = str(bundle["source"]["guild_id"]) == str(target_guild_id)
    rows = mapping_rows(bundle["modules"], chosen, same_guild=same, catalog=catalog or {}, choices=choices)
    resolved = {row["key"]: row for row in rows}
    changes = []
    for module_id in chosen:
        incoming = scrub_private_media(bundle["modules"][module_id], cross_guild=not same, notes=[])
        changes.append(impact_for(module_id, (current.get("modules") or {}).get(module_id), incoming, resolved, blocked_detail(module_id, rows)))
    return {
        "mode": "restore" if same else "transfer",
        "strategy": strategy,
        "source": bundle["source"],
        "exported_at": bundle.get("exported_at"),
        "version": bundle["version"],
        "modules": [module["id"] for module in [{"id": module_id} for module_id in chosen]],
        "resources": rows,
        "changes": changes,
        "ready": not unresolved(rows) and not any(item["action"] == "blocked" for item in changes),
    }


async def plan(target_guild_id: int, guild_name: str, raw: dict, catalog: dict | None, choices: dict | None, modules: list[str] | None, strategy: str) -> dict:
    bundle = validate_bundle(raw)
    chosen = [module_id for module_id in selected(modules) if module_id in bundle["modules"]]
    current = await build_export(target_guild_id, guild_name, chosen, catalog)
    return _plan(bundle, target_guild_id, current, catalog or {}, choices, chosen, strategy)


async def _record(guild_id: int, actor_id: int | None, bundle: dict, modules: list[str], result: str) -> None:
    async with session_scope() as session:
        session.add(ConfigImportHistory(
            guild_id=guild_id,
            actor_id=actor_id,
            source_guild_id=str(bundle["source"]["guild_id"]),
            source_guild_name=str(bundle["source"].get("guild_name") or "")[:100],
            modules=modules,
            result=result,
            format_version=int(bundle["version"]),
            created_at=datetime.now(timezone.utc),
        ))


async def history(guild_id: int) -> list[dict]:
    async with session_scope() as session:
        rows = (await session.execute(select(ConfigImportHistory).where(ConfigImportHistory.guild_id == guild_id).order_by(ConfigImportHistory.created_at.desc()).limit(20))).scalars().all()
        return [
            {
                "id": str(row.id),
                "at": row.created_at.isoformat(),
                "actor_id": snowflake_to_str(row.actor_id) if row.actor_id else None,
                "source_guild_id": row.source_guild_id,
                "source_guild_name": row.source_guild_name,
                "modules": row.modules,
                "result": row.result,
                "version": row.format_version,
            }
            for row in rows
        ]


async def apply(target_guild_id: int, guild_name: str, raw: dict, catalog: dict | None, choices: dict | None, modules: list[str] | None, strategy: str, actor_id: int | None, known_messages: set[str] | None = None) -> dict:
    payload = raw if isinstance(raw, dict) else {}
    encoded = len(str(payload))
    if encoded > MAX_BYTES:
        raise TransferError("This backup is too large to import.")
    planned = await plan(target_guild_id, guild_name, payload, catalog, choices, modules, strategy)
    if unresolved(planned["resources"]):
        raise TransferError("Map or skip every resource before applying.")
    if any(item["action"] == "blocked" for item in planned["changes"]):
        raise TransferError("Resolve blocked modules before applying.")
    bundle = validate_bundle(payload)
    chosen = planned["modules"]
    same = planned["mode"] == "restore"
    snapshot = await build_export(target_guild_id, guild_name, chosen, catalog)
    snapshot_id = uuid.uuid4()
    async with session_scope() as session:
        session.add(ConfigImportSnapshot(id=snapshot_id, guild_id=target_guild_id, modules=chosen, bundle=snapshot, created_at=datetime.now(timezone.utc)))
    resolved = {row["key"]: row for row in planned["resources"]}
    try:
        for module_id in chosen:
            if os.environ.get("CLS_CONFIG_TRANSFER_FAIL") == module_id:
                raise TransferError("The import was stopped before this module was saved.")
            incoming = apply_map(scrub_private_media(bundle["modules"][module_id], cross_guild=not same, notes=[]), resolved)
            await apply_module(target_guild_id, module_id, incoming, same_guild=same, known_messages=known_messages or set(), strategy=strategy)
    except Exception as exc:
        await _restore(target_guild_id, snapshot, same, known_messages or set())
        await _record(target_guild_id, actor_id, bundle, chosen, "rolled_back")
        await _drop_snapshot(snapshot_id)
        return {"ok": False, "result": "rolled_back", "message": "Import failed — previous configuration restored"}
    await _drop_snapshot(snapshot_id)
    await _record(target_guild_id, actor_id, bundle, chosen, "applied")
    return {"ok": True, "result": "applied", "message": "Import applied", "changes": planned["changes"]}


def _flatten(value):
    if isinstance(value, dict) and value.get("type") in {"role", "channel", "category", "emoji"} and str(value.get("source_id") or "").isdigit():
        return value["source_id"]
    if isinstance(value, dict):
        return {key: _flatten(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_flatten(item) for item in value]
    return value


async def _restore(guild_id: int, snapshot: dict, same: bool, known_messages: set[str]) -> None:
    for module_id, body in (snapshot.get("modules") or {}).items():
        await apply_module(guild_id, module_id, _flatten(body), same_guild=True, known_messages=known_messages, strategy="replace")


async def _drop_snapshot(snapshot_id: uuid.UUID) -> None:
    async with session_scope() as session:
        row = await session.get(ConfigImportSnapshot, snapshot_id)
        if row is not None:
            await session.delete(row)
