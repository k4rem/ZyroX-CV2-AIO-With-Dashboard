"""System / module health (Dashboard-safe)."""

from __future__ import annotations

from fastapi import APIRouter, Request

from api.dependencies import get_bot
from cls_platform.config import POSTGRES_ENABLED, root_owner_configured
from cls_platform.services import scheduler as scheduler_service
from fastapi import Depends
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from core.zyrox import zyrox

router = APIRouter()


@router.get("/health")
async def system_health(
    request: Request,
    bot: "zyrox" = Depends(get_bot),
):
    from utils.module_health import required_modules_report
    from utils.api_bind import load_api_bind_config
    from cls_platform.health.permissions import permission_health_summary

    api_cfg = load_api_bind_config()
    modules = required_modules_report(bot)
    perm = await permission_health_summary(bot)

    return {
        "postgres": {"enabled": POSTGRES_ENABLED, "connected": POSTGRES_ENABLED},
        "root_owner_configured": root_owner_configured(),
        "api": {"enabled": api_cfg.enabled, "host": api_cfg.host},
        "scheduler": {"worker_running": scheduler_service._worker_running},
        "modules": modules,
        "permissions": perm,
    }
