"""Structure snapshots. Snowflakes stay strings. No restore."""

from __future__ import annotations

import hashlib
import json
import os
from typing import Any

from sqlalchemy import select

from cls_platform.database import session_scope
from cls_platform.discord_types import snowflake_to_str
from cls_platform.models import SnapshotMetadata
from cls_platform.security.models import SecurityIncident

SCHEMA_VERSION = 1
SUSPECT_SEVERITIES = {"H", "C"}


def _sid(value: Any) -> str:
    return snowflake_to_str(int(value))


def canonicalize(structure: dict) -> dict:
    """Stable document. Every snowflake is a string."""
    roles = [
        {
            "id": _sid(role["id"]),
            "name": role.get("name") or "",
            "position": int(role.get("position") or 0),
            "permissions": str(role.get("permissions") or "0"),
            "managed": bool(role.get("managed")),
        }
        for role in structure.get("roles") or []
    ]
    channels = []
    for channel in structure.get("channels") or []:
        overwrites = [
            {
                "id": _sid(item["id"]),
                "type": item.get("type") or "role",
                "allow": str(item.get("allow") or "0"),
                "deny": str(item.get("deny") or "0"),
            }
            for item in channel.get("overwrites") or []
        ]
        channels.append(
            {
                "id": _sid(channel["id"]),
                "name": channel.get("name") or "",
                "type": channel.get("type") or "text",
                "parent_id": _sid(channel["parent_id"]) if channel.get("parent_id") else None,
                "position": int(channel.get("position") or 0),
                "overwrites": overwrites,
            }
        )
    bans = [_sid(item) for item in structure.get("bans") or []]
    members = [
        {"user_id": _sid(item["user_id"]), "role_ids": [_sid(role_id) for role_id in item.get("role_ids") or []]}
        for item in structure.get("members") or []
    ]
    return {
        "schema_version": SCHEMA_VERSION,
        "guild_id": _sid(structure["guild_id"]),
        "roles": roles,
        "channels": channels,
        "bans": bans,
        "members": members,
    }


def checksum(document: dict) -> str:
    raw = json.dumps(document, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(raw).hexdigest()


def encrypt_archive(payload: bytes, key: bytes | None = None) -> bytes:
    secret = key or os.getenv("CLS_SNAPSHOT_ARCHIVE_KEY", "").encode()
    if not secret:
        raise RuntimeError("CLS_SNAPSHOT_ARCHIVE_KEY is required to encrypt a legacy archive")
    stream = b""
    counter = 0
    while len(stream) < len(payload):
        stream += hashlib.sha256(secret + counter.to_bytes(8, "big")).digest()
        counter += 1
    return bytes(left ^ right for left, right in zip(payload, stream))


async def _suspect(session, guild_id: int) -> bool:
    row = (
        await session.execute(
            select(SecurityIncident.id).where(
                SecurityIncident.guild_id == guild_id,
                SecurityIncident.status == "ACTIVE",
                SecurityIncident.severity.in_(tuple(SUSPECT_SEVERITIES)),
            )
        )
    ).first()
    return row is not None


async def capture_snapshot(guild_id: int, structure: dict, *, archive: bytes | None = None, archive_key: bytes | None = None) -> dict:
    document = canonicalize({**structure, "guild_id": guild_id})
    digest = checksum(document)
    encrypted = None
    if archive is not None:
        encrypted = encrypt_archive(archive, archive_key).hex()
    async with session_scope() as session:
        state = "SUSPECT" if await _suspect(session, guild_id) else "KNOWN_GOOD"
        row = SnapshotMetadata(
            guild_id=guild_id,
            snapshot_type="structure",
            status=state,
            snapshot_meta={
                "schema_version": SCHEMA_VERSION,
                "checksum": digest,
                "source_guild": _sid(guild_id),
                "incident_state": state,
                "document": document,
                "legacy_archive_hex": encrypted,
            },
        )
        session.add(row)
        await session.flush()
        return {
            "id": str(row.id),
            "guild_id": row.guild_id,
            "status": row.status,
            "snapshot_meta": dict(row.snapshot_meta),
        }


async def list_snapshots(guild_id: int) -> list[dict]:
    async with session_scope() as session:
        rows = (
            await session.execute(
                select(SnapshotMetadata)
                .where(SnapshotMetadata.guild_id == guild_id)
                .order_by(SnapshotMetadata.created_at.desc())
            )
        ).scalars().all()
        return [
            {
                "id": str(row.id),
                "guild_id": snowflake_to_str(row.guild_id),
                "status": row.status,
                "checksum": (row.snapshot_meta or {}).get("checksum"),
                "created_at": row.created_at.isoformat() if row.created_at else None,
            }
            for row in rows
        ]
