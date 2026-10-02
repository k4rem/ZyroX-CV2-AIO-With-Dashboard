"""Explicit FastAPI route classification (fail-closed default)."""

from __future__ import annotations

import re
from enum import Enum
from typing import Optional

from fastapi import HTTPException


class RouteClass(str, Enum):
    EXPLICIT_PUBLIC = "EXPLICIT_PUBLIC"
    INTERNAL_SERVICE = "INTERNAL_SERVICE"
    ROOT_ONLY = "ROOT_ONLY"
    AUTHENTICATED_USER = "AUTHENTICATED_USER"


# Known guild sub-routes (path after /api/v1/guilds/{id})
_GUILD_SUBROUTES = frozenset(
    {
        "",
        "/",
        "/prefix",
        "/automod",
        "/tickets",
        "/tickets/v2",
        "/leveling",
        "/leveling/leaderboard",
        "/welcome",
        "/antinuke",
        "/security",
        "/snapshots",
        "/verification",
        "/vanityroles",
        "/autorole",
        "/autorole/v2",
        "/tracking",
        "/j2c",
        "/joindm",
        "/customroles",
        "/logging",
        "/logging/v2",
        "/channels",
        "/commands",
        "/roles",
        "/autoreact",
        "/autoreact/v2",
        "/invcrole",
        "/invites",
        "/invites/v2",
        "/giveaways",
        "/reactionroles",
        "/reactionroles/v2",
        "/messages",
        "/config-transfer",
        "/media",
        "/emojis",
    }
)

_GUILD_SUBROUTE_PREFIXES = (
    "/vanityroles/",
    "/security/",
    "/snapshots/",
    "/tickets/v2/",
    "/logging/v2/",
    "/invites/v2/",
    "/giveaways/",
    "/reactionroles/v2/",
    "/autorole/v2/",
    "/autoreact/v2/",
    "/messages/",
    "/config-transfer/",
    "/welcome/",
    "/media/",
    "/emojis/",
)

_GUILDS_LIST = re.compile(r"^/api/v1/guilds/?$")
_GUILD_DETAIL = re.compile(r"^/api/v1/guilds/(?P<guild_id>\d+|\{guild_id\})(?P<suffix>/.*)?$")


def classify_http_route(method: str, path: str) -> RouteClass:
    """Classify application routes. Unknown protected paths → raise (fail-closed)."""
    if path in {"/", "/health"}:
        return RouteClass.EXPLICIT_PUBLIC
    if path.startswith("/api/internal/"):
        return RouteClass.INTERNAL_SERVICE
    if path.startswith("/api/v1/admin") or path.startswith("/api/v1/access"):
        return RouteClass.ROOT_ONLY
    if path.startswith("/api/v1/system"):
        return RouteClass.AUTHENTICATED_USER
    if path.startswith("/api/v1/bot"):
        return RouteClass.AUTHENTICATED_USER
    if _GUILDS_LIST.match(path):
        return RouteClass.AUTHENTICATED_USER
    match = _GUILD_DETAIL.match(path)
    if match:
        suffix = match.group("suffix") or ""
        if suffix in _GUILD_SUBROUTES:
            return RouteClass.AUTHENTICATED_USER
        for prefix in _GUILD_SUBROUTE_PREFIXES:
            if suffix.startswith(prefix):
                return RouteClass.AUTHENTICATED_USER
        raise HTTPException(status_code=403, detail="Unknown guild route")
    if path.startswith("/api/v1/"):
        raise HTTPException(status_code=403, detail="Unknown application route")
    if path.startswith("/openapi") or path.startswith("/docs") or path.startswith("/redoc"):
        return RouteClass.EXPLICIT_PUBLIC
    raise HTTPException(status_code=403, detail="Unknown application route")


def iter_application_routes(app) -> list[tuple[str, str, str]]:
    """Return (method, path, classification) for coverage tests."""
    rows: list[tuple[str, str, str]] = []
    for route in app.routes:
        path = getattr(route, "path", None)
        if not path:
            continue
        methods = getattr(route, "methods", None) or {"GET"}
        for method in sorted(methods):
            if method == "HEAD":
                continue
            try:
                cls = classify_http_route(method, path)
                rows.append((method, path, cls.value))
            except HTTPException:
                rows.append((method, path, "UNCLASSIFIED_DENY"))
    return rows
