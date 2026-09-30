"""Ensure every application API route is explicitly classified."""

from __future__ import annotations

import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("ALLOW_EMPTY_GUILD_ALLOWLIST", "true")
os.environ.setdefault("ALLOWED_GUILD_IDS", "100000000000000100")


def test_all_api_routes_classified():
    from tests.conftest import _ensure_real_utils_package

    _ensure_real_utils_package()
    from api.auth.route_registry import RouteClass, classify_http_route
    from api.server import create_app

    app = create_app()
    app.state.bot = object()
    unclassified = []
    for route in app.routes:
        path = getattr(route, "path", "")
        if not path.startswith("/api/"):
            continue
        methods = getattr(route, "methods", None) or {"GET"}
        for method in methods:
            if method == "HEAD":
                continue
            try:
                cls = classify_http_route(method, path)
                assert cls in (
                    RouteClass.EXPLICIT_PUBLIC,
                    RouteClass.INTERNAL_SERVICE,
                    RouteClass.ROOT_ONLY,
                    RouteClass.AUTHENTICATED_USER,
                )
            except Exception:
                unclassified.append((method, path))
    assert not unclassified, f"Unclassified routes: {unclassified}"
