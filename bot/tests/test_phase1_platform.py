"""Phase 1 unit tests (no live Postgres/Discord required)."""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("ALLOW_EMPTY_GUILD_ALLOWLIST", "true")
os.environ.setdefault("ALLOWED_GUILD_IDS", "")

import uuid
from datetime import datetime, timedelta, timezone

import jwt
import pytest


def test_discord_snowflake_validation():
    from cls_platform.discord_types import _validate_snowflake

    assert _validate_snowflake(1) == 1
    with pytest.raises(ValueError):
        _validate_snowflake(0)


def test_internal_identity_token_roundtrip():
    os.environ["INTERNAL_IDENTITY_SIGNING_KEY"] = "phase1-test-signing-key-32bytes!!"
    os.environ["INTERNAL_IDENTITY_AUDIENCE"] = "cls-fastapi"
    from importlib import reload
    import cls_platform.config as cfg

    reload(cfg)
    from api.auth.identity import verify_internal_identity_token

    now = datetime.now(timezone.utc)
    payload = {
        "sub": "123456789012345678",
        "sid": str(uuid.uuid4()),
        "aud": "cls-fastapi",
        "jti": str(uuid.uuid4()),
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(seconds=30)).timestamp()),
    }
    token = jwt.encode(payload, os.environ["INTERNAL_IDENTITY_SIGNING_KEY"], algorithm="HS256")
    decoded = verify_internal_identity_token(token)
    assert decoded["sub"] == payload["sub"]


def test_route_policy_public_paths():
    from api.auth.policy import PUBLIC_PATHS, INTERNAL_PREFIX

    assert "/" in PUBLIC_PATHS
    assert "/health" in PUBLIC_PATHS
    assert INTERNAL_PREFIX == "/api/internal/"


def test_api_lifecycle_no_daemon_thread_in_codex():
    text = open(os.path.join(os.path.dirname(__file__), "..", "CodeX.py"), encoding="utf-8").read()
    assert "Thread(target=run_api" not in text
    assert "keep_alive()" not in text


def test_fastapi_app_has_auth_middleware():
    from api.auth.middleware import register_dashboard_auth_middleware
    from fastapi import FastAPI

    app = FastAPI()
    register_dashboard_auth_middleware(app)
    assert len(app.user_middleware) >= 1
