"""System / module health (Dashboard-safe, authorized server-side).

Authorization model (enforced here and, for ``guild_id``, again in
``api.auth.policy.apply_request_auth``):

* Every caller is an authenticated Dashboard identity. A non-root identity also needs
  at least one active Dashboard grant (same rule as ``/api/v1/bot``).
* Per-guild permission health is only ever computed for the guilds returned by
  ``authorized_guild_ids``: allowlisted product guilds, never the CLS Ops guild, and for
  non-root callers only guilds with an active grant. Root gets every product guild.
* ``?guild_id=`` narrows the view to one guild and must itself be authorized.
  Nothing the client sends widens the view.
* Platform-global detail (API bind host, root configuration, optional modules, raw
  module error text) is root-only.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request

from api.auth.guilds import authorized_guild_ids
from api.dependencies import get_bot
from cls_platform.config import POSTGRES_ENABLED, root_owner_configured
from cls_platform.services import scheduler as scheduler_service

if TYPE_CHECKING:
    from core.zyrox import zyrox

router = APIRouter()


def _modules_for_caller(report: dict, *, is_root: bool) -> dict:
    """Root sees the full module report; everyone else sees names and state only."""
    if is_root:
        return report
    return {
        "healthy": report.get("healthy", True),
        "required_ok": list(report.get("required_ok", [])),
        "required_failed": [{"name": f.get("name")} for f in report.get("required_failed", [])],
    }


@router.get("/health")
async def system_health(
    request: Request,
    guild_id: Optional[int] = Query(default=None),
    bot: "zyrox" = Depends(get_bot),
):
    from utils.module_health import required_modules_report
    from utils.api_bind import load_api_bind_config
    from cls_platform.health.permissions import permission_health_summary

    auth = request.state.dashboard_auth
    authorized = await authorized_guild_ids(auth, bot)

    if guild_id is not None:
        if guild_id not in authorized:
            raise HTTPException(status_code=403, detail="Guild not available")
        scope = {guild_id}
    else:
        scope = authorized

    body = {
        "postgres": {"enabled": POSTGRES_ENABLED, "connected": POSTGRES_ENABLED},
        "scheduler": {"worker_running": scheduler_service._worker_running},
        "modules": _modules_for_caller(required_modules_report(bot), is_root=auth.is_root),
        "permissions": await permission_health_summary(bot, guild_ids=scope),
    }

    if auth.is_root:
        api_cfg = load_api_bind_config()
        body["root_owner_configured"] = root_owner_configured()
        body["api"] = {"enabled": api_cfg.enabled, "host": api_cfg.host}

    return body
