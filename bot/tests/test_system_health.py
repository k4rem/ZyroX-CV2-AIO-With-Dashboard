"""System health must not leak secrets."""

from __future__ import annotations

import pytest

from tests.conftest import auth_headers, TEST_ROOT


@pytest.mark.asyncio
async def test_system_health_safe_payload(api_client):
    client, _ = api_client
    headers = await auth_headers(TEST_ROOT)
    r = await client.get("/api/v1/system/health", headers=headers)
    assert r.status_code == 200
    body = r.text.lower()
    for forbidden in (
        "postgresql+asyncpg",
        "internal_service_key",
        "internal_identity_signing",
        "password",
        "traceback",
    ):
        assert forbidden not in body
