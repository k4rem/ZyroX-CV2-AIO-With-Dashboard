"""Phase 1 auth matrix integration tests (Postgres + FastAPI middleware)."""

from __future__ import annotations

import os
import uuid
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, patch

import jwt
import pytest

from tests.conftest import (
    TEST_GUILD_A,
    TEST_GUILD_B,
    TEST_ROOT,
    TEST_USER,
    auth_headers,
    create_test_session,
    mint_identity_token,
)


async def _grant(api_client, guild_id: int, user_id: int, template: str = "admin"):
    from cls_platform.services.grants import create_grant, get_role_by_template

    role = await get_role_by_template(template)
    assert role is not None
    await create_grant(guild_id, user_id, role.id)


@pytest.mark.asyncio
async def test_no_token_401(api_client):
    client, _ = api_client
    r = await client.get("/api/v1/guilds/")
    assert r.status_code == 401


@pytest.mark.asyncio
async def test_invalid_signature_rejected(api_client):
    client, _ = api_client
    sid = await create_test_session(TEST_USER)
    token = mint_identity_token(TEST_USER, sid)
    bad = token[:-5] + "xxxxx"
    r = await client.get("/api/v1/guilds/", headers={"Authorization": f"Bearer {bad}"})
    assert r.status_code == 401


@pytest.mark.asyncio
async def test_expired_token_rejected(api_client):
    client, _ = api_client
    sid = await create_test_session(TEST_USER)
    token = mint_identity_token(TEST_USER, sid, exp_seconds=-10)
    r = await client.get("/api/v1/guilds/", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 401


@pytest.mark.asyncio
async def test_wrong_audience_rejected(api_client):
    client, _ = api_client
    sid = await create_test_session(TEST_USER)
    now = datetime.now(timezone.utc)
    payload = {
        "sub": str(TEST_USER),
        "sid": str(sid),
        "aud": "wrong-audience",
        "jti": str(uuid.uuid4()),
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(seconds=60)).timestamp()),
    }
    token = jwt.encode(
        payload, os.environ["INTERNAL_IDENTITY_SIGNING_KEY"], algorithm="HS256"
    )
    r = await client.get("/api/v1/guilds/", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 401


@pytest.mark.asyncio
async def test_missing_session_rejected(api_client):
    client, _ = api_client
    sid = uuid.uuid4()
    token = mint_identity_token(TEST_USER, sid)
    r = await client.get("/api/v1/guilds/", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 401


@pytest.mark.asyncio
async def test_revoked_session_rejected(api_client):
    from cls_platform.services.sessions import revoke_session

    client, _ = api_client
    sid = await create_test_session(TEST_USER)
    await revoke_session(sid, reason="test")
    token = mint_identity_token(TEST_USER, sid)
    r = await client.get("/api/v1/guilds/", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 401


@pytest.mark.asyncio
async def test_expired_persistent_session_rejected(api_client, db_reset):
    from cls_platform.database import get_session_factory
    from cls_platform.models import DashboardSession
    from sqlalchemy import update

    client, _ = api_client
    sid = await create_test_session(TEST_USER)
    factory = get_session_factory()
    async with factory() as session:
        await session.execute(
            update(DashboardSession)
            .where(DashboardSession.id == sid)
            .values(expires_at=datetime.now(timezone.utc) - timedelta(hours=1))
        )
        await session.commit()
    token = mint_identity_token(TEST_USER, sid)
    r = await client.get("/api/v1/guilds/", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 401


@pytest.mark.asyncio
async def test_subject_session_mismatch_rejected(api_client):
    client, _ = api_client
    sid = await create_test_session(TEST_USER)
    token = mint_identity_token(TEST_USER + 1, sid)
    r = await client.get("/api/v1/guilds/", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 401


@pytest.mark.asyncio
async def test_no_grant_403_on_guild(api_client):
    client, _ = api_client
    headers = await auth_headers(TEST_USER)
    r = await client.get(f"/api/v1/guilds/{TEST_GUILD_A}", headers=headers)
    assert r.status_code == 403


@pytest.mark.asyncio
async def test_grant_guild_a_cannot_access_guild_b(api_client):
    client, _ = api_client
    await _grant(api_client, TEST_GUILD_A, TEST_USER, "admin")
    headers = await auth_headers(TEST_USER)
    r = await client.get(f"/api/v1/guilds/{TEST_GUILD_B}", headers=headers)
    assert r.status_code == 403


@pytest.mark.asyncio
async def test_granted_user_can_access_guild(api_client):
    client, _ = api_client
    await _grant(api_client, TEST_GUILD_A, TEST_USER, "admin")
    headers = await auth_headers(TEST_USER)
    r = await client.get(f"/api/v1/guilds/{TEST_GUILD_A}", headers=headers)
    assert r.status_code == 200


@pytest.mark.asyncio
async def test_support_missing_moderation_capability(api_client):
    client, _ = api_client
    await _grant(api_client, TEST_GUILD_A, TEST_USER, "support")
    headers = await auth_headers(TEST_USER)
    r = await client.patch(
        f"/api/v1/guilds/{TEST_GUILD_A}/automod",
        headers=headers,
        json={"enabled": True},
    )
    assert r.status_code == 403


@pytest.mark.asyncio
async def test_moderator_can_automod(api_client):
    client, _ = api_client
    await _grant(api_client, TEST_GUILD_A, TEST_USER, "moderator")
    headers = await auth_headers(TEST_USER)
    r = await client.get(f"/api/v1/guilds/{TEST_GUILD_A}/automod", headers=headers)
    assert r.status_code in (200, 500)


@pytest.mark.asyncio
async def test_root_access_admin(api_client):
    client, _ = api_client
    headers = await auth_headers(TEST_ROOT)
    r = await client.get("/api/v1/access/grants", headers=headers)
    assert r.status_code == 200


@pytest.mark.asyncio
async def test_owner_ids_not_root(api_client, monkeypatch):
    monkeypatch.setenv("OWNER_IDS", str(TEST_USER))
    headers = await auth_headers(TEST_USER)
    client, _ = api_client
    r = await client.get("/api/v1/admin/stats", headers=headers)
    assert r.status_code == 403


@pytest.mark.asyncio
async def test_access_api_root_only(api_client):
    client, _ = api_client
    await _grant(api_client, TEST_GUILD_A, TEST_USER, "admin")
    headers = await auth_headers(TEST_USER)
    r = await client.get("/api/v1/access/grants", headers=headers)
    assert r.status_code == 403


@pytest.mark.asyncio
async def test_revoked_grant_loses_access(api_client):
    from cls_platform.services.grants import get_active_grant, revoke_grant

    client, _ = api_client
    await _grant(api_client, TEST_GUILD_A, TEST_USER, "admin")
    grant = await get_active_grant(TEST_GUILD_A, TEST_USER)
    assert grant is not None
    await revoke_grant(grant.id)
    headers = await auth_headers(TEST_USER)
    r = await client.get(f"/api/v1/guilds/{TEST_GUILD_A}", headers=headers)
    assert r.status_code == 403


@pytest.mark.asyncio
async def test_internal_session_bad_service_key(api_client):
    client, _ = api_client
    r = await client.post(
        "/api/internal/v1/sessions",
        json={"discord_access_token": "fake-token-value"},
        headers={"X-Internal-Service-Key": "wrong"},
    )
    assert r.status_code == 401


@pytest.mark.asyncio
async def test_internal_session_flow(api_client):
    client, _ = api_client
    mock_resp = type(
        "R",
        (),
        {"status_code": 200, "json": lambda self: {"id": str(TEST_USER)}},
    )()
    mock_client = AsyncMock()
    mock_client.get = AsyncMock(return_value=mock_resp)
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=None)
    with patch("api.routes.internal_sessions.httpx.AsyncClient", return_value=mock_client):
        r = await client.post(
            "/api/internal/v1/sessions",
            json={"discord_access_token": "fake-oauth-token-not-stored"},
            headers={"X-Internal-Service-Key": os.environ["INTERNAL_SERVICE_KEY"]},
        )
    assert r.status_code == 200
    data = r.json()
    assert "session_id" in data
    assert data["discord_user_id"] == str(TEST_USER)
    assert "fake-oauth" not in r.text


@pytest.mark.asyncio
async def test_user_bearer_cannot_call_internal_session(api_client):
    client, _ = api_client
    headers = await auth_headers(TEST_USER)
    r = await client.post(
        "/api/internal/v1/sessions",
        json={"discord_access_token": "x" * 20},
        headers=headers,
    )
    assert r.status_code == 401


@pytest.mark.asyncio
async def test_revoked_session_rejected_after_revoke(api_client):
    from cls_platform.services.sessions import create_session, revoke_session

    client, _ = api_client
    sid = await create_session(TEST_USER)
    token = mint_identity_token(TEST_USER, sid)
    headers = {"Authorization": f"Bearer {token}"}
    ok = await client.get(f"/api/v1/guilds/{TEST_GUILD_A}", headers=headers)
    assert ok.status_code in (403, 404)  # no grant yet
    await revoke_session(sid)
    r = await client.get("/api/v1/guilds/", headers=headers)
    assert r.status_code == 401


@pytest.mark.asyncio
async def test_revoke_all_sessions(api_client):
    from cls_platform.services.sessions import create_session, revoke_all_for_user

    client, _ = api_client
    sid1 = await create_session(TEST_USER)
    sid2 = await create_session(TEST_USER)
    t1 = mint_identity_token(TEST_USER, sid1)
    t2 = mint_identity_token(TEST_USER, sid2)
    await revoke_all_for_user(TEST_USER)
    assert (await client.get("/api/v1/guilds/", headers={"Authorization": f"Bearer {t1}"})).status_code == 401
    assert (await client.get("/api/v1/guilds/", headers={"Authorization": f"Bearer {t2}"})).status_code == 401


@pytest.mark.asyncio
async def test_granted_user_sees_only_granted_guilds(api_client):
    client, _ = api_client
    await _grant(api_client, TEST_GUILD_A, TEST_USER, "admin")
    headers = await auth_headers(TEST_USER)
    r = await client.get("/api/v1/guilds/", headers=headers)
    assert r.status_code == 200
    ids = {g["id"] for g in r.json()}
    assert str(TEST_GUILD_A) in ids
    assert str(TEST_GUILD_B) not in ids


@pytest.mark.asyncio
async def test_no_grant_user_sees_no_guilds(api_client):
    client, _ = api_client
    headers = await auth_headers(TEST_USER)
    r = await client.get("/api/v1/guilds/", headers=headers)
    assert r.status_code == 200
    assert r.json() == []


@pytest.mark.asyncio
async def test_admin_capability_welcome_moderator_denied(api_client):
    client, _ = api_client
    await _grant(api_client, TEST_GUILD_A, TEST_USER, "moderator")
    headers = await auth_headers(TEST_USER)
    r = await client.patch(
        f"/api/v1/guilds/{TEST_GUILD_A}/welcome",
        headers=headers,
        json={"enabled": True},
    )
    assert r.status_code == 403
