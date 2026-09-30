"""``/api/v1/system/health`` must be authorized server-side (Task A security closure).

These run the real FastAPI app with the real dashboard-auth middleware, real session/JWT
verification and the real grant tables (disposable Postgres). Nothing in the authorization
path is mocked; only the Discord gateway is replaced by ``FakeBot``.
"""

from __future__ import annotations

from types import SimpleNamespace

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
from tests.fixtures.fake_bot import FakeGuild

HEALTH = "/api/v1/system/health"

GUILD_C_NOT_ALLOWLISTED = 100000000000000300
OPS_GUILD = 100000000000000999

NAME_A = "Guild Alpha Visible"
NAME_B = "Guild Bravo Secret"
NAME_C = "Guild Charlie Unlisted"
NAME_OPS = "CLS Ops Internal"


class _Perms:
    """Bot guild permissions: everything granted except ``missing``."""

    def __init__(self, missing: tuple[str, ...] = ()):
        self._missing = set(missing)

    def __getattr__(self, name: str) -> bool:
        return name not in self._missing


def _me(missing: tuple[str, ...] = ()):
    return SimpleNamespace(guild_permissions=_Perms(missing), top_role=SimpleNamespace(position=7))


@pytest.fixture
def health_world(api_client, monkeypatch):
    """Four guilds: A, B (allowlisted product guilds), C (not allowlisted) and the Ops guild."""
    from api.auth import allowlist as allowlist_loader

    client, app = api_client
    bot = app.state.bot
    bot.guilds = [
        FakeGuild(id=TEST_GUILD_A, name=NAME_A, me=_me()),
        FakeGuild(id=TEST_GUILD_B, name=NAME_B, me=_me(("kick_members",))),
        FakeGuild(id=GUILD_C_NOT_ALLOWLISTED, name=NAME_C, me=_me()),
        FakeGuild(id=OPS_GUILD, name=NAME_OPS, me=_me()),
    ]
    # The Ops guild is deliberately on the allowlist so only the Ops rule can exclude it.
    monkeypatch.setenv("ALLOWED_GUILD_IDS", f"{TEST_GUILD_A},{TEST_GUILD_B},{OPS_GUILD}")
    allowlist_loader.clear_allowlist_cache()
    monkeypatch.setattr("api.auth.guilds.OPS_GUILD_ID", OPS_GUILD)
    monkeypatch.setattr("cls_platform.config.OPS_GUILD_ID", OPS_GUILD)
    yield client, bot
    allowlist_loader.clear_allowlist_cache()


async def _grant(guild_id: int, user_id: int, template: str = "admin"):
    from cls_platform.services.grants import create_grant, get_role_by_template

    role = await get_role_by_template(template)
    assert role is not None
    return await create_grant(guild_id, user_id, role.id)


def _guild_ids(body: dict) -> list[str]:
    return sorted(g["guild_id"] for g in body["permissions"]["guilds"])


def _assert_no_foreign_data(text: str, *, allowed_names: tuple[str, ...]):
    for gid, name in (
        (TEST_GUILD_B, NAME_B),
        (TEST_GUILD_A, NAME_A),
        (GUILD_C_NOT_ALLOWLISTED, NAME_C),
        (OPS_GUILD, NAME_OPS),
    ):
        if name in allowed_names:
            continue
        assert str(gid) not in text, f"leaked guild id {gid}"
        assert name not in text, f"leaked guild name {name}"


# 1. Only guild A granted: guild B is not revealed -------------------------------------------------


@pytest.mark.asyncio
async def test_granted_user_sees_only_their_guild(health_world):
    client, _ = health_world
    await _grant(TEST_GUILD_A, TEST_USER)
    r = await client.get(HEALTH, headers=await auth_headers(TEST_USER))
    assert r.status_code == 200
    body = r.json()
    assert _guild_ids(body) == [str(TEST_GUILD_A)]
    assert body["permissions"]["guilds"][0]["guild_name"] == NAME_A
    _assert_no_foreign_data(r.text, allowed_names=(NAME_A,))


@pytest.mark.asyncio
async def test_non_root_does_not_receive_platform_internals(health_world):
    client, bot = health_world
    from utils.module_health import ModuleHealth

    mh = ModuleHealth()
    mh.record_ok("Moderation", True)
    mh.record_fail("Antinuke", True, RuntimeError("internal-path-C:/secret/stack"))
    mh.record_fail("Fun", False, RuntimeError("optional-detail"))
    bot.module_health = mh

    await _grant(TEST_GUILD_A, TEST_USER)
    r = await client.get(HEALTH, headers=await auth_headers(TEST_USER))
    assert r.status_code == 200
    body = r.json()
    assert "api" not in body
    assert "root_owner_configured" not in body
    # Names and state stay (the shell shows "required module failed"); raw error text does not.
    assert body["modules"]["required_failed"] == [{"name": "Antinuke"}]
    assert "optional_failed" not in body["modules"]
    assert "internal-path" not in r.text
    assert "optional-detail" not in r.text

    root = await client.get(HEALTH, headers=await auth_headers(TEST_ROOT))
    assert root.status_code == 200
    assert "internal-path" in root.text  # root keeps the diagnostic detail


# 2. Changing guild_id by hand does not widen access ------------------------------------------------


@pytest.mark.asyncio
async def test_granted_user_cannot_request_other_guild(health_world):
    client, _ = health_world
    await _grant(TEST_GUILD_A, TEST_USER)
    headers = await auth_headers(TEST_USER)

    denied = await client.get(HEALTH, params={"guild_id": TEST_GUILD_B}, headers=headers)
    assert denied.status_code == 403
    _assert_no_foreign_data(denied.text, allowed_names=())

    # Not allowlisted, Ops, and a guild the bot is not in: all denied for a non-root user.
    for gid in (GUILD_C_NOT_ALLOWLISTED, OPS_GUILD, 100000000000000777):
        r = await client.get(HEALTH, params={"guild_id": gid}, headers=headers)
        assert r.status_code in (403, 404), gid
        assert NAME_C not in r.text and NAME_OPS not in r.text

    # Parameter tricks cannot widen the view.
    for query in ("guild_id=abc", "guild_id=-1", "guild_id=0", f"guild_id={TEST_GUILD_A}&guild_id={TEST_GUILD_B}"):
        r = await client.get(f"{HEALTH}?{query}", headers=headers)
        assert r.status_code in (400, 403, 422), query
        assert NAME_B not in r.text

    # The granted guild itself works and is narrowed to exactly that guild.
    ok = await client.get(HEALTH, params={"guild_id": TEST_GUILD_A}, headers=headers)
    assert ok.status_code == 200
    assert _guild_ids(ok.json()) == [str(TEST_GUILD_A)]


@pytest.mark.asyncio
async def test_client_supplied_guild_list_is_ignored(health_world):
    client, _ = health_world
    await _grant(TEST_GUILD_A, TEST_USER)
    headers = await auth_headers(TEST_USER)
    r = await client.get(
        HEALTH,
        params={"guild_ids": f"{TEST_GUILD_A},{TEST_GUILD_B}", "guilds": str(TEST_GUILD_B)},
        headers={**headers, "X-Guild-Ids": f"{TEST_GUILD_B}"},
    )
    assert r.status_code == 200
    assert _guild_ids(r.json()) == [str(TEST_GUILD_A)]
    _assert_no_foreign_data(r.text, allowed_names=(NAME_A,))


# 3. Root gets the intended global + product view ----------------------------------------------------


@pytest.mark.asyncio
async def test_root_sees_global_and_product_guilds_but_not_ops(health_world):
    client, _ = health_world
    r = await client.get(HEALTH, headers=await auth_headers(TEST_ROOT))
    assert r.status_code == 200
    body = r.json()
    assert _guild_ids(body) == sorted([str(TEST_GUILD_A), str(TEST_GUILD_B)])
    assert {"postgres", "scheduler", "modules", "permissions", "api", "root_owner_configured"} <= set(body)
    # CLS Ops is not an ordinary product guild, even for root; unlisted guilds are not product guilds.
    assert str(OPS_GUILD) not in r.text and NAME_OPS not in r.text
    assert str(GUILD_C_NOT_ALLOWLISTED) not in r.text and NAME_C not in r.text


@pytest.mark.asyncio
async def test_root_can_narrow_to_one_product_guild_but_not_ops(health_world):
    client, _ = health_world
    headers = await auth_headers(TEST_ROOT)
    ok = await client.get(HEALTH, params={"guild_id": TEST_GUILD_B}, headers=headers)
    assert ok.status_code == 200
    assert _guild_ids(ok.json()) == [str(TEST_GUILD_B)]

    ops = await client.get(HEALTH, params={"guild_id": OPS_GUILD}, headers=headers)
    assert ops.status_code == 403
    assert NAME_OPS not in ops.text


# 4. Discord permissions alone grant nothing ---------------------------------------------------------


@pytest.mark.asyncio
async def test_discord_administrator_alone_grants_nothing(health_world):
    client, bot = health_world
    # TEST_USER is the Discord owner of guild A and holds Administrator there, with no Dashboard grant.
    guild_a = bot.get_guild(TEST_GUILD_A)
    guild_a.owner_id = TEST_USER
    guild_a.members = [
        SimpleNamespace(id=TEST_USER, guild_permissions=SimpleNamespace(administrator=True, manage_guild=True))
    ]
    headers = await auth_headers(TEST_USER)

    r = await client.get(HEALTH, headers=headers)
    assert r.status_code == 403
    assert NAME_A not in r.text

    r = await client.get(HEALTH, params={"guild_id": TEST_GUILD_A}, headers=headers)
    assert r.status_code == 403
    assert NAME_A not in r.text

    # A grant elsewhere does not turn Discord ownership of guild A into Dashboard access to it.
    await _grant(TEST_GUILD_B, TEST_USER)
    r = await client.get(HEALTH, headers=headers)
    assert r.status_code == 200
    assert _guild_ids(r.json()) == [str(TEST_GUILD_B)]
    assert NAME_A not in r.text
    r = await client.get(HEALTH, params={"guild_id": TEST_GUILD_A}, headers=headers)
    assert r.status_code == 403


# 5. Revocation removes access -----------------------------------------------------------------------


@pytest.mark.asyncio
async def test_revoked_grant_loses_health_access(health_world):
    from cls_platform.services.grants import revoke_grant

    client, _ = health_world
    grant_a = await _grant(TEST_GUILD_A, TEST_USER)
    await _grant(TEST_GUILD_B, TEST_USER)
    headers = await auth_headers(TEST_USER)

    before = await client.get(HEALTH, headers=headers)
    assert _guild_ids(before.json()) == sorted([str(TEST_GUILD_A), str(TEST_GUILD_B)])

    assert await revoke_grant(grant_a.id)
    after = await client.get(HEALTH, headers=headers)
    assert after.status_code == 200
    assert _guild_ids(after.json()) == [str(TEST_GUILD_B)]
    assert NAME_A not in after.text
    assert (await client.get(HEALTH, params={"guild_id": TEST_GUILD_A}, headers=headers)).status_code == 403


@pytest.mark.asyncio
async def test_user_with_all_grants_revoked_is_rejected(health_world):
    from cls_platform.services.grants import revoke_grant

    client, _ = health_world
    grant = await _grant(TEST_GUILD_A, TEST_USER)
    headers = await auth_headers(TEST_USER)
    assert (await client.get(HEALTH, headers=headers)).status_code == 200

    assert await revoke_grant(grant.id)
    r = await client.get(HEALTH, headers=headers)
    assert r.status_code == 403
    assert NAME_A not in r.text


@pytest.mark.asyncio
async def test_user_without_any_grant_is_rejected(health_world):
    client, _ = health_world
    r = await client.get(HEALTH, headers=await auth_headers(TEST_USER))
    assert r.status_code == 403
    _assert_no_foreign_data(r.text, allowed_names=())


# 6. Unauthenticated stays rejected ------------------------------------------------------------------


@pytest.mark.asyncio
async def test_unauthenticated_request_rejected(health_world):
    client, _ = health_world
    assert (await client.get(HEALTH)).status_code == 401
    assert (await client.get(HEALTH, params={"guild_id": TEST_GUILD_A})).status_code == 401
    assert (await client.get(HEALTH, headers={"Authorization": "Bearer not-a-token"})).status_code == 401

    sid = await create_test_session(TEST_USER)
    bad = mint_identity_token(TEST_USER, sid)[:-5] + "xxxxx"
    assert (await client.get(HEALTH, headers={"Authorization": f"Bearer {bad}"})).status_code == 401


# Defence in depth: the collector itself cannot be called without a scope ---------------------------


@pytest.mark.asyncio
async def test_permission_collector_requires_explicit_scope(health_world):
    from cls_platform.health.permissions import permission_health_summary

    _, bot = health_world
    with pytest.raises(TypeError):
        await permission_health_summary(bot)  # type: ignore[call-arg]
    only_b = await permission_health_summary(bot, guild_ids={TEST_GUILD_B})
    assert [g["guild_id"] for g in only_b["guilds"]] == [str(TEST_GUILD_B)]
    assert only_b["guilds"][0]["missing_by_module"]  # B is missing kick_members
