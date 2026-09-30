"""Route authorization policies and capability mapping."""

from __future__ import annotations

import re
from typing import Optional

from fastapi import HTTPException, Request

from api.auth.context import DashboardAuthContext
from cls_platform.services import grants as grant_service
from api.auth.allowlist import is_guild_allowed

GUILD_PATH = re.compile(r"^/api/v1/guilds/(?P<guild_id>\d+)(?P<suffix>/.*)?$")

# Explicit public or internal exemptions (no dashboard JWT)
PUBLIC_PATHS = frozenset({"/", "/health", "/openapi.json", "/docs", "/redoc"})
INTERNAL_PREFIX = "/api/internal/"

# Routes registered with this marker skip user JWT (still may need service auth)
ROUTE_POLICY_PUBLIC = "public"
ROUTE_POLICY_INTERNAL = "internal"
ROUTE_POLICY_ROOT = "root"
ROUTE_POLICY_AUTHENTICATED = "authenticated"


def mark_public(route):
    route.__dashboard_policy__ = ROUTE_POLICY_PUBLIC
    return route


def mark_internal(route):
    route.__dashboard_policy__ = ROUTE_POLICY_INTERNAL
    return route


def mark_root(route):
    route.__dashboard_policy__ = ROUTE_POLICY_ROOT
    return route


def mark_authenticated(route):
    route.__dashboard_policy__ = ROUTE_POLICY_AUTHENTICATED
    return route


def resolve_capability(method: str, suffix: Optional[str]) -> str:
    path = suffix or ""
    if method == "GET" and path in ("", "/"):
        return "guild.view"
    mapping = {
        "/prefix": "bot.settings",
        "/automod": "moderation.config",
        "/tickets": "tickets.config",
        "/leveling": "bot.settings",
        "/logging": "logging.config",
        "/welcome": "welcome.config",
        "/antinuke": "security.config",
        "/verification": "security.config",
        "/vanityroles": "bot.settings",
        "/autorole": "autorole.config",
        "/tracking": "bot.settings",
        "/j2c": "j2c.config",
        "/joindm": "welcome.config",
        "/customroles": "bot.settings",
        "/autoreact": "bot.settings",
        "/invcrole": "bot.settings",
        "/reactionroles": "reactionroles.config",
        "/invites": "invites.manage",
        "/channels": "guild.view",
        "/roles": "guild.view",
    }
    for prefix, cap in mapping.items():
        if path == prefix or path.startswith(prefix + "/"):
            if method == "GET" and cap.endswith(".config"):
                return "guild.view"
            return cap
    raise HTTPException(status_code=403, detail="Unknown guild route capability")


async def authorize_guild_request(
    auth: DashboardAuthContext,
    guild_id: int,
    capability: str,
    bot,
) -> None:
    from cls_platform.config import OPS_GUILD_ID

    if OPS_GUILD_ID is not None and guild_id == OPS_GUILD_ID and not auth.is_root:
        raise HTTPException(status_code=403, detail="Guild not available")

    if not is_guild_allowed(guild_id):
        raise HTTPException(status_code=403, detail="Guild not allowed")

    if bot.get_guild(guild_id) is None:
        raise HTTPException(status_code=404, detail="Guild not found")

    if auth.is_root:
        return

    if not await grant_service.get_active_grant(guild_id, auth.user_id):
        raise HTTPException(status_code=403, detail="No dashboard access for guild")

    if not await grant_service.user_has_capability(guild_id, auth.user_id, capability):
        raise HTTPException(status_code=403, detail="Insufficient capability")


async def apply_request_auth(request: Request, auth: DashboardAuthContext, bot) -> None:
    from api.auth.route_registry import RouteClass, classify_http_route
    from api.validators.discord_resources import validate_mutation_payload

    path = request.url.path
    route_class = classify_http_route(request.method, path)

    if route_class == RouteClass.ROOT_ONLY:
        if not auth.is_root:
            raise HTTPException(status_code=403, detail="Root access required")
        return

    if route_class == RouteClass.AUTHENTICATED_USER and path.startswith("/api/v1/system"):
        return

    if path.startswith("/api/v1/bot"):
        if auth.is_root:
            return
        user_grants = await grant_service.list_grants_for_user(auth.user_id)
        if not user_grants:
            raise HTTPException(status_code=403, detail="Dashboard access required")
        return

    if path.rstrip("/") == "/api/v1/guilds":
        return

    match = GUILD_PATH.match(path)
    if match:
        guild_id = int(match.group("guild_id"))
        suffix = match.group("suffix") or ""
        cap = resolve_capability(request.method, suffix)
        await authorize_guild_request(auth, guild_id, cap, bot)
        request.state.guild_id = guild_id
        await validate_mutation_payload(request, guild_id, bot)
        return

    raise HTTPException(status_code=403, detail="Unknown application route")
