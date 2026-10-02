"""Role menu decisions, legacy migration, and guild-scoped API."""

import sqlite3

import pytest

from api.routes.role_menus import _health
from cls_platform.role_menus.deliver import component_view, reaction_targets
from cls_platform.role_menus.logic import (
    button_custom_id,
    emoji_identity,
    emoji_token,
    parse_custom_id,
    plan_change,
    role_block,
    same_emoji,
    select_custom_id,
)
from cls_platform.role_menus.store import (
    MenuError,
    create_menu,
    delete_menu,
    duplicate_menu,
    get_menu,
    list_menus,
    menu_for_message,
    migrate_legacy,
    set_published,
    update_menu,
)
from cogs.cog_loader import _cog_specs
from tests.conftest import TEST_GUILD_A, TEST_GUILD_B, TEST_ROOT, auth_headers

GUILD = 1543105121804615781
OTHER = 1543105121804615782
RED = 9007199254740993
BLUE = 9007199254740994
GREEN = 9007199254740995
MESSAGE = 1555268757436371007


def test_legacy_reaction_cog_is_unloaded():
    specs = {spec.class_name: spec for spec in _cog_specs()}
    assert specs["ReactionRoles"].skip is True
    assert specs["RoleMenus"].skip is False


def test_modes_limits_and_emoji_identity():
    roles = {RED, BLUE}
    unique = plan_change(mode="unique", intent="grant", held={RED}, target=BLUE, menu_roles=roles, max_roles=None)
    assert unique["add"] == [BLUE]
    assert unique["remove"] == [RED]
    add_only = plan_change(mode="add", intent="press", held={RED}, target=RED, menu_roles=roles, max_roles=None)
    assert add_only["unchanged"] is True
    remove_only = plan_change(mode="remove", intent="grant", held={RED}, target=RED, menu_roles=roles, max_roles=None)
    assert remove_only["remove"] == [RED]
    capped = plan_change(mode="toggle", intent="grant", held={RED, BLUE}, target=GREEN, menu_roles={RED, BLUE, GREEN}, max_roles=2)
    assert "maximum of 2" in capped["error"]
    assert role_block(exists=True, managed=True, bot_can_manage=True, below_bot=True).startswith("That role is managed")
    assert "above CLS" in role_block(exists=True, managed=False, bot_can_manage=True, below_bot=False)
    token = emoji_token("<:vip:9007199254740993>")
    assert emoji_identity(token) == "vip:9007199254740993"
    assert same_emoji(token, "vip", 9007199254740993)
    assert same_emoji("🔴", "🔴")
    menu_id = "11111111-1111-1111-1111-111111111111"
    option_id = "22222222-2222-2222-2222-222222222222"
    custom = button_custom_id(menu_id, option_id)
    assert custom == f"cls-rr:{menu_id}:{option_id}"
    assert len(custom) <= 100
    assert parse_custom_id(custom) == (menu_id, option_id)
    assert parse_custom_id(select_custom_id(menu_id)) == (menu_id, None)


def test_component_ids_survive_a_rebuild():
    menu = {
        "id": "11111111-1111-1111-1111-111111111111",
        "type": "button",
        "options": [{"id": "22222222-2222-2222-2222-222222222222", "emoji": "🔔", "label": "Announcements", "description": ""}],
    }
    view = component_view(menu)
    assert view.children[0].custom_id == button_custom_id(menu["id"], menu["options"][0]["id"])
    select = component_view({**menu, "type": "select", "options": [{**menu["options"][0], "label": "EU", "description": "Europe"}]})
    assert select.children[0].custom_id == select_custom_id(menu["id"])
    assert select.children[0].options[0].value == menu["options"][0]["id"]


async def test_migration_crud_and_isolation(db_reset, tmp_path):
    path = tmp_path / "rr.db"
    with sqlite3.connect(path) as conn:
        conn.execute("CREATE TABLE reaction_roles (guild_id INTEGER, message_id INTEGER, emoji TEXT, role_id INTEGER)")
        conn.execute("INSERT INTO reaction_roles VALUES (?, ?, ?, ?)", (GUILD, MESSAGE, "🔴", RED))
    assert await migrate_legacy(str(path)) == 1
    with sqlite3.connect(path) as conn:
        assert conn.execute("SELECT COUNT(*) FROM reaction_roles").fetchone()[0] == 1
    migrated = await menu_for_message(GUILD, MESSAGE)
    assert migrated["type"] == "reaction"
    assert migrated["source"] == "existing"
    assert migrated["mode"] == "toggle"
    assert migrated["options"][0]["emoji"] == "🔴"
    assert migrated["options"][0]["role_id"] == str(RED)
    assert await migrate_legacy(str(path)) == 0
    created = await create_menu(
        guild_id=GUILD,
        name="Pick your color",
        source="created",
        menu_type="reaction",
        mode="unique",
        channel_id=1555268757436371006,
        payload={"content": "Pick your color", "embeds": [], "buttons": []},
        options=[{"role_id": str(RED), "emoji": "🔴", "label": "Red"}, {"role_id": str(BLUE), "emoji": "🔵", "label": "Blue"}],
    )
    assert created["guild_id"] == str(GUILD)
    assert created["max_roles"] is None
    assert reaction_targets(created)["🔵"]["role_id"] == str(BLUE)
    edited = await update_menu(guild_id=GUILD, menu_id=created["id"], options=[{"role_id": str(RED), "emoji": "🔴", "label": "Red"}, {"role_id": str(GREEN), "emoji": "🟢", "label": "Green"}])
    assert "🔵" not in reaction_targets(edited)
    assert reaction_targets(edited)["🟢"]["role_id"] == str(GREEN)
    disabled = await update_menu(guild_id=GUILD, menu_id=created["id"], enabled=False)
    assert disabled["enabled"] is False
    missing = await set_published(guild_id=GUILD, menu_id=created["id"], channel_id=1555268757436371006, message_id=MESSAGE, status="missing")
    health = _health(None, missing)
    assert health["status"] == "Disabled"
    assert "gone" in health["warnings"][0]
    enabled = await update_menu(guild_id=GUILD, menu_id=created["id"], enabled=True)
    assert _health(None, {**enabled, "publish_status": "missing", "message_id": str(MESSAGE)})["status"] == "Message missing"
    copy = await duplicate_menu(guild_id=GUILD, menu_id=created["id"])
    assert copy["publish_status"] == "draft"
    assert copy["message_id"] is None
    assert copy["source"] == "created"
    assert copy["name"].endswith("copy")
    with pytest.raises(MenuError):
        await get_menu(OTHER, created["id"])
    assert await list_menus(OTHER) == []
    with pytest.raises(MenuError):
        await create_menu(guild_id=GUILD, name="Bad", source="existing", menu_type="button", mode="toggle")
    await delete_menu(guild_id=GUILD, menu_id=copy["id"])
    assert all(item["id"] != copy["id"] for item in await list_menus(GUILD))


async def test_role_menu_api_is_guild_scoped(api_client):
    client, _app = api_client
    headers = await auth_headers(TEST_ROOT)
    created = await client.post(
        f"/api/v1/guilds/{TEST_GUILD_A}/reactionroles/v2",
        headers=headers,
        json={"name": "Regions", "source": "created", "type": "select", "mode": "unique", "options": [{"role_id": "100001", "emoji": "🇪🇺", "label": "EU"}]},
    )
    assert created.status_code == 200, created.text
    body = created.json()
    assert isinstance(body["guild_id"], str)
    assert body["options"][0]["role_id"] == "100001"
    foreign = await client.get(f"/api/v1/guilds/{TEST_GUILD_B}/reactionroles/v2/{body['id']}", headers=headers)
    assert foreign.status_code == 404
    listed = await client.get(f"/api/v1/guilds/{TEST_GUILD_B}/reactionroles/v2", headers=headers)
    assert listed.json()["menus"] == []
    edited = await client.patch(
        f"/api/v1/guilds/{TEST_GUILD_A}/reactionroles/v2/{body['id']}",
        headers=headers,
        json={"enabled": False},
    )
    assert edited.status_code == 200
    assert edited.json()["status"] == "Disabled"
    publish = await client.post(f"/api/v1/guilds/{TEST_GUILD_A}/reactionroles/v2/{body['id']}/publish", headers=headers, json={})
    assert publish.status_code == 422
