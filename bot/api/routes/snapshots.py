"""Snapshot capture API. Restore is Phase 6."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request

from cls_platform.snapshots import capture_snapshot, list_snapshots

router = APIRouter()


def _root(request: Request) -> None:
    auth = getattr(request.state, "dashboard_auth", None)
    if auth is None or not auth.is_root:
        raise HTTPException(status_code=403, detail="Root access required")


@router.get("/{guild_id}/snapshots")
async def get_snapshots(guild_id: int):
    return await list_snapshots(guild_id)


@router.post("/{guild_id}/snapshots")
async def post_snapshot(guild_id: int, body: dict, request: Request):
    _root(request)
    try:
        return await capture_snapshot(guild_id, body)
    except (KeyError, TypeError, ValueError) as exc:
        raise HTTPException(status_code=400, detail="Snapshot structure is incomplete") from exc
