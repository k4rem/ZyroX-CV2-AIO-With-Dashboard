"""F1a shared health contract."""

from __future__ import annotations

import json

import pytest

from cls_platform.health.contract import (
    channel_checks,
    module_health,
    role_checks,
    role_is_below_bot,
    runtime_snapshot,
)
from tests.conftest import TEST_GUILD_A, TEST_ROOT, auth_headers

BIG = 1543105121913802823


def test_health_contract_schema():
    health = module_health(
        role_checks(
            managed=False,
            position=1,
            role_id=10,
            bot_position=5,
            bot_role_id=20,
            manage_roles=True,
        )
    )
    assert health["status"] in {"healthy", "warning", "error", "locked", "unavailable"}
    assert health["status"] == "healthy"
    for row in health["checks"]:
        assert set(row) == {"id", "label", "ok", "severity", "fix_hint", "scope"}


def test_role_above_or_equal_cls_is_warning():
    above = role_checks(managed=False, position=8, role_id=1, bot_position=5, bot_role_id=2, manage_roles=True)
    assert any(row["id"] == "role_hierarchy" and not row["ok"] and row["label"] == "Role above CLS" for row in above)
    assert module_health(above)["status"] == "warning"
    same_position_higher_id = role_checks(
        managed=False, position=5, role_id=30, bot_position=5, bot_role_id=20, manage_roles=True
    )
    assert any(row["id"] == "role_hierarchy" and not row["ok"] for row in same_position_higher_id)
    assert role_is_below_bot(5, 10, 5, 20)


def test_managed_role_and_missing_manage_roles():
    managed = role_checks(managed=True, position=1, role_id=3, bot_position=5, bot_role_id=9, manage_roles=True)
    assert any(row["id"] == "role_managed" and not row["ok"] for row in managed)
    missing = role_checks(managed=False, position=1, role_id=3, bot_position=5, bot_role_id=9, manage_roles=False)
    assert module_health(missing)["status"] == "error"
    assert any(row["id"] == "manage_roles" and row["label"] == "Manage Roles" for row in missing)


def test_channel_capability_health_only_checks_requested():
    caps = {"view_channel": True, "send_messages": False, "embed_links": False, "attach_files": False, "manage_channels": False}
    send = channel_checks(caps, ["send_messages"])
    assert send[0]["label"] == "Cannot send"
    assert send[0]["ok"] is False
    assert module_health(send)["status"] == "error"
    embed = channel_checks(caps, ["embed_links"])
    assert embed[0]["label"] == "Cannot embed"
    assert module_health(embed)["status"] == "warning"
    assert "observability_only" not in json.dumps(send)


def test_snapshot_keeps_large_snowflakes_as_strings_and_unavailable_without_member():
    assert runtime_snapshot(None)["status"] == "unavailable"

    class Role:
        def __init__(self, role_id, position, managed=False):
            self.id = role_id
            self.position = position
            self.managed = managed

    class Perms:
        manage_roles = True
        manage_messages = True
        moderate_members = True
        kick_members = True
        ban_members = True
        manage_channels = True
        view_audit_log = False
        send_messages = True
        embed_links = True
        attach_files = True
        view_channel = True

    class Me:
        guild_permissions = Perms()
        top_role = Role(BIG, 10)

    class Channel:
        def __init__(self, channel_id, send):
            self.id = channel_id
            self._send = send

        def permissions_for(self, _member):
            class Overwrite:
                view_channel = True
                send_messages = self._send
                embed_links = True
                attach_files = True
                manage_channels = True

            return Overwrite()

    class Guild:
        me = Me()
        roles = [Role(BIG, 10), Role(4, 20, managed=True)]
        channels = [Channel(BIG, False)]

    snap = runtime_snapshot(Guild())
    assert snap["bot"]["top_role_id"] == str(BIG)
    assert isinstance(snap["bot"]["top_role_id"], str)
    assert str(BIG) in snap["roles"]
    assert snap["roles"]["4"]["managed"] is True
    assert snap["channels"][str(BIG)]["send_messages"] is False
    raw = json.dumps(snap)
    assert f'"{BIG}"' in raw
    assert snap["status"] == "warning"


@pytest.mark.asyncio
async def test_runtime_health_route(api_client):
    client, _app = api_client
    headers = await auth_headers(TEST_ROOT)
    response = await client.get(f"/api/v1/guilds/{TEST_GUILD_A}/runtime-health", headers=headers)
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "unavailable"
    assert body["checks"][0]["id"] == "bot_member"
    assert "observability_only" not in response.text
