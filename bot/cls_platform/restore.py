"""Disaster recovery V1 planner. Live execution stays off unless a disposable guild is explicitly allowed."""

from __future__ import annotations

import os
import uuid

from sqlalchemy import select

from cls_platform.database import session_scope
from cls_platform.models import SnapshotMetadata


class RestoreError(ValueError):
    pass


def confirmation_phrase(snapshot_id: str) -> str:
    return f"RESTORE {snapshot_id}"


def execution_allowed(guild_id: int) -> bool:
    if os.getenv("CLS_RESTORE_ALLOW") != "disposable":
        return False
    raw = os.getenv("CLS_RESTORE_GUILD_IDS", "")
    allowed = {int(item) for item in raw.split(",") if item.strip().isdigit()}
    return guild_id in allowed


def build_plan(document: dict, present_member_ids: set[str]) -> dict:
    roles = sorted(document.get("roles") or [], key=lambda item: int(item.get("position") or 0))
    channels = list(document.get("channels") or [])
    categories = [item for item in channels if str(item.get("type")) in {"category", "4"}]
    rest = [item for item in channels if item not in categories]
    categories.sort(key=lambda item: int(item.get("position") or 0))
    rest.sort(key=lambda item: (item.get("parent_id") or "", int(item.get("position") or 0)))
    members = []
    for member in document.get("members") or []:
        user_id = str(member["user_id"])
        if user_id in present_member_ids:
            members.append({"user_id": user_id, "role_ids": member.get("role_ids") or [], "status": "present"})
        else:
            members.append({"user_id": user_id, "role_ids": member.get("role_ids") or [], "status": "REQUIRES MEMBER REAUTHORIZATION"})
    return {
        "roles": roles,
        "categories": categories,
        "channels": rest,
        "bans": list(document.get("bans") or []),
        "members": members,
        "guild_settings": document.get("settings") or None,
        "unmapped": [],
    }


async def plan_for(guild_id: int, snapshot_id: str, present_member_ids: set[str]) -> dict:
    async with session_scope() as session:
        row = await session.get(SnapshotMetadata, uuid.UUID(snapshot_id))
        if row is None or row.guild_id != guild_id:
            raise RestoreError("missing")
        document = (row.snapshot_meta or {}).get("document") or {}
    plan = build_plan(document, present_member_ids)
    plan["snapshot_id"] = snapshot_id
    plan["confirmation"] = confirmation_phrase(snapshot_id)
    plan["executed"] = False
    return plan


async def execute_plan(plan: dict, guild, *, confirmation: str, allow_execution: bool) -> dict:
    if confirmation != plan.get("confirmation"):
        raise RestoreError("confirmation_required")
    if not allow_execution:
        return {**plan, "executed": False, "reason": "execution_disabled"}
    id_map: dict[str, str] = {}
    journal = []
    for role in plan["roles"]:
        if role.get("managed"):
            journal.append({"kind": "role", "old_id": role["id"], "status": "skipped_managed"})
            continue
        created = await guild.create_role(name=role["name"], permissions=int(role["permissions"]))
        id_map[role["id"]] = str(created.id)
        journal.append({"kind": "role", "old_id": role["id"], "new_id": str(created.id)})
    ordered = plan["categories"] + plan["channels"]
    for channel in ordered:
        parent = id_map.get(channel["parent_id"]) if channel.get("parent_id") else None
        if channel.get("parent_id") and parent is None:
            plan["unmapped"].append({"kind": "channel_parent", "id": channel["parent_id"]})
        created = await guild.create_channel(name=channel["name"], parent_id=parent, kind=channel.get("type"))
        id_map[channel["id"]] = str(created.id)
        for overwrite in channel.get("overwrites") or []:
            mapped = id_map.get(overwrite["id"])
            if mapped is None:
                plan["unmapped"].append({"kind": "overwrite", "id": overwrite["id"]})
                continue
            await guild.set_overwrite(created.id, mapped, overwrite.get("allow"), overwrite.get("deny"))
        journal.append({"kind": "channel", "old_id": channel["id"], "new_id": str(created.id)})
    for user_id in plan["bans"]:
        await guild.ban(user_id)
        journal.append({"kind": "ban", "user_id": user_id})
    for member in plan["members"]:
        if member["status"] != "present":
            journal.append({"kind": "member_roles", "user_id": member["user_id"], "status": member["status"]})
            continue
        mapped_roles = []
        for role_id in member["role_ids"]:
            mapped = id_map.get(role_id)
            if mapped is None:
                plan["unmapped"].append({"kind": "member_role", "id": role_id, "user_id": member["user_id"]})
            else:
                mapped_roles.append(mapped)
        await guild.set_member_roles(member["user_id"], mapped_roles)
        journal.append({"kind": "member_roles", "user_id": member["user_id"], "status": "restored"})
    if plan.get("guild_settings"):
        await guild.edit_settings(plan["guild_settings"])
        journal.append({"kind": "settings"})
    return {**plan, "executed": True, "id_map": id_map, "journal": journal}


async def latest_document(guild_id: int) -> dict | None:
    async with session_scope() as session:
        row = (
            await session.execute(
                select(SnapshotMetadata)
                .where(SnapshotMetadata.guild_id == guild_id)
                .order_by(SnapshotMetadata.created_at.desc())
            )
        ).scalars().first()
        if row is None:
            return None
        return (row.snapshot_meta or {}).get("document")
