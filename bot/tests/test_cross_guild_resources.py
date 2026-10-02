"""Cross-guild resource ID mutation must fail closed."""

from __future__ import annotations

import pytest

from tests.conftest import TEST_CHANNEL_A, TEST_GUILD_A, TEST_GUILD_B, TEST_ROLE_B, TEST_USER, auth_headers


async def _grant_admin(api_client):
    from cls_platform.services.grants import create_grant, get_role_by_template

    role = await get_role_by_template("admin")
    await create_grant(TEST_GUILD_A, TEST_USER, role.id)


@pytest.mark.asyncio
async def test_foreign_role_id_in_body_rejected(api_client):
    client, _ = api_client
    await _grant_admin(api_client)
    headers = await auth_headers(TEST_USER)
    r = await client.patch(
        f"/api/v1/guilds/{TEST_GUILD_A}/autorole",
        headers=headers,
        json={"role_id": TEST_ROLE_B},
    )
    assert r.status_code == 403


@pytest.mark.asyncio
async def test_foreign_channel_id_in_body_rejected(api_client):
    client, _ = api_client
    await _grant_admin(api_client)
    headers = await auth_headers(TEST_USER)
    r = await client.patch(
        f"/api/v1/guilds/{TEST_GUILD_A}/logging",
        headers=headers,
        json={"log_channel_id": 200002},
    )
    assert r.status_code == 403


@pytest.mark.asyncio
async def test_same_guild_autorole_route_is_gone(api_client):
    client, _ = api_client
    await _grant_admin(api_client)
    headers = await auth_headers(TEST_USER)
    from tests.conftest import TEST_ROLE_A

    r = await client.patch(
        f"/api/v1/guilds/{TEST_GUILD_A}/autorole",
        headers=headers,
        json={"role_id": TEST_ROLE_A, "enabled": False},
    )
    assert r.status_code == 410
