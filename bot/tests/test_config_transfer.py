"""Config backup validation, mapping, restore, and rollback."""

import os

import pytest

from cls_platform.config_transfer.mapping import decide, mapping_rows
from cls_platform.config_transfer.schema import TransferError, find_secret, scrub_private_media, strip_secrets, validate_bundle
from cls_platform.config_transfer.service import apply, build_export, plan
from cls_platform.logging.store import ignores_public, set_ignores
from cls_platform.messages.store import create_template, list_templates, update_template
from cls_platform.role_automation.store import create_rule, get_rule, list_rules, update_rule
from cls_platform.role_menus.store import list_menus
from cls_platform.tickets.store import workspace
from tests.conftest import TEST_GUILD_A, TEST_GUILD_B, TEST_ROOT, auth_headers

GUILD = TEST_GUILD_A
OTHER = TEST_GUILD_B
ROLE = "9007199254740993"
OTHER_ROLE = "9007199254740994"
REPLACEMENT = "9007199254740995"
PAYLOAD = {"content": "Hello", "embeds": [], "buttons": []}


def _bundle(modules, guild=GUILD):
    return {"format": "cls-config", "version": 1, "exported_at": "2026-10-02T00:00:00+00:00", "source": {"guild_id": str(guild), "guild_name": "Source"}, "modules": modules}


def _role(source_id, name):
    return {"source_id": str(source_id), "name": name, "type": "role"}


def test_schema_rejects_secrets_and_future_versions():
    assert find_secret({"modules": {"welcome": {"token": "x"}}}) == "token"
    assert "token" not in strip_secrets({"token": "x", "name": "ok"})
    notes = []
    assert scrub_private_media("https://cdn.example/guilds/100/media/file", cross_guild=True, notes=notes) == ""
    assert notes == ["Uploaded media needs replacement"]
    assert scrub_private_media("https://cdn.example/banner.png", cross_guild=True, notes=[]) == "https://cdn.example/banner.png"
    with pytest.raises(TransferError, match="version 1"):
        validate_bundle(_bundle({}, guild=GUILD) | {"version": 2})
    with pytest.raises(TransferError, match="secret"):
        validate_bundle(_bundle({"welcome": {"password": "no"}}))
    with pytest.raises(TransferError, match="not a CLS"):
        validate_bundle({"format": "zip"})


def test_mapping_is_exact_and_refuses_cross_guild_ids():
    catalog = {"roles": [{"id": OTHER_ROLE, "name": "Moderator"}, {"id": REPLACEMENT, "name": "Moderator"}]}
    ambiguous = decide(_role(ROLE, "Moderator"), same_guild=False, catalog=catalog, choice=None)
    assert ambiguous["status"] == "needs_mapping"
    unique = decide(_role(ROLE, "Moderator"), same_guild=False, catalog={"roles": [{"id": OTHER_ROLE, "name": "Moderator"}]}, choice=None)
    assert unique["target_id"] == OTHER_ROLE
    assert unique["target_id"] != ROLE
    missing = decide(_role(ROLE, "Gone"), same_guild=False, catalog={"roles": []}, choice=None)
    assert missing["status"] == "missing"
    same = decide(_role(ROLE, "Moderator"), same_guild=True, catalog={"roles": [{"id": ROLE, "name": "Moderator"}]}, choice=None)
    assert same["detail"] == "Still on this server"
    skipped = decide(_role(ROLE, "Moderator"), same_guild=False, catalog={"roles": []}, choice={"action": "skip"})
    assert skipped["status"] == "skip"


async def test_roundtrip_selective_restore_and_rollback(db_reset):
    await create_template(guild_id=GUILD, name="Hello", payload=PAYLOAD, created_by=None)
    rule = await create_rule(guild_id=GUILD, name="Customer to Verified", trigger="role_add", trigger_role_id=ROLE, conditions=[{"kind": "human"}], action="add", action_role_id=OTHER_ROLE, delay_seconds_value=0)
    catalog = {"roles": [{"id": ROLE, "name": "Customer"}, {"id": OTHER_ROLE, "name": "Verified"}], "channels": [], "emojis": []}
    bundle = await build_export(GUILD, "Source", ["messages", "role_automation"], catalog)
    assert bundle["modules"]["role_automation"]["rules"][0]["action_role"]["source_id"] == OTHER_ROLE
    assert "templates" in bundle["modules"]["messages"]
    assert find_secret(bundle) is None
    await update_template(guild_id=GUILD, template_id=(await list_templates(GUILD))[0]["id"], name=None, payload={**PAYLOAD, "content": "Changed"})
    await update_rule(guild_id=GUILD, rule_id=rule["id"], delay_seconds=30)
    preview = await plan(GUILD, "Source", bundle, catalog, {}, ["messages"], "merge")
    assert preview["mode"] == "restore"
    assert preview["ready"] is True
    assert (await get_rule(GUILD, rule["id"]))["delay_seconds"] == 30
    applied = await apply(GUILD, "Source", bundle, catalog, {}, ["messages"], "merge", TEST_ROOT)
    assert applied["ok"] is True
    assert (await list_templates(GUILD))[0]["payload"]["content"] == "Hello"
    assert (await get_rule(GUILD, rule["id"]))["delay_seconds"] == 30
    await update_template(guild_id=GUILD, template_id=(await list_templates(GUILD))[0]["id"], name=None, payload={**PAYLOAD, "content": "Again"})
    os.environ["CLS_CONFIG_TRANSFER_FAIL"] = "role_automation"
    try:
        failed = await apply(GUILD, "Source", bundle, catalog, {}, ["messages", "role_automation"], "merge", TEST_ROOT)
    finally:
        os.environ.pop("CLS_CONFIG_TRANSFER_FAIL", None)
    assert failed["result"] == "rolled_back"
    assert "restored" in failed["message"]
    assert (await list_templates(GUILD))[0]["payload"]["content"] == "Again"
    assert await list_rules(OTHER) == []


async def test_cross_guild_mapping_disables_unresolved_rules(db_reset):
    bundle = _bundle({
        "role_automation": {"rules": [{
            "name": "Customer to Verified",
            "trigger": "role_add",
            "trigger_role": _role(ROLE, "Customer"),
            "conditions": [{"kind": "has_role", "role": _role("9007199254740996", "Gate")}],
            "action": "add",
            "action_role": _role(OTHER_ROLE, "Verified"),
            "delay_seconds": 0,
            "enabled": True,
        }]},
        "logging": {"routes": [], "event_routes": [], "appearance": {}, "ignored_channels": [], "ignored_roles": [], "ignored_members": [str(TEST_ROOT)]},
    }, guild=OTHER)
    catalog = {"roles": [{"id": "111", "name": "Customer"}, {"id": "222", "name": "Verified"}], "channels": [], "emojis": []}
    planned = await plan(GUILD, "Target", bundle, catalog, {}, ["role_automation", "logging"], "merge")
    assert planned["mode"] == "transfer"
    assert any(row["status"] == "missing" and row["name"] == "Gate" for row in planned["resources"])
    mapped = await apply(GUILD, "Target", bundle, catalog, {"role:9007199254740996": {"action": "skip"}}, ["role_automation"], "merge", TEST_ROOT)
    assert mapped["ok"] is True
    saved = (await list_rules(GUILD))[0]
    assert saved["enabled"] is False
    assert saved["action_role_id"] == "222"
    assert saved["trigger_role_id"] == "111"
    assert saved["action_role_id"] != OTHER_ROLE
    await set_ignores(guild_id=GUILD, channels=[], roles=[], users=[TEST_ROOT])
    from cls_platform.config_transfer.io import apply_logging
    await apply_logging(GUILD, {"routes": [], "event_routes": [], "appearance": {}, "ignored_channels": [], "ignored_roles": [], "ignored_members": [str(TEST_ROOT)]}, same_guild=False)
    assert (await ignores_public(GUILD))["users"] == []


async def test_menus_and_panels_import_as_drafts(db_reset):
    bundle = _bundle({
        "role_menus": {"menus": [{
            "name": "Colors",
            "source": "existing",
            "type": "button",
            "mode": "toggle",
            "button_style": "toggle",
            "enabled": True,
            "max_roles": None,
            "channel": {"source_id": "555", "name": "support", "type": "channel"},
            "payload": {"content": "Pick", "embeds": [], "buttons": []},
            "publication": {"message_id": "999", "status": "published"},
            "options": [{"role": _role(ROLE, "Red"), "emoji": "🔴", "label": "Red", "description": ""}],
        }]},
        "tickets": {
            "settings": {"cooldown_seconds": 60, "max_open": 1, "auto_close_hours": None, "grace_minutes": 60, "transcript_channel": None, "name_format": "ticket-{number}"},
            "categories": [{"name": "Support", "discord_category": {"source_id": "777", "name": "Tickets", "type": "category"}, "staff_roles": [_role(ROLE, "Staff")], "required_roles": [], "blocked_roles": [], "name_format": "ticket-{number}", "ping_staff": True}],
            "panels": [{
                "title": "Help",
                "message": "Open a ticket",
                "button_label": "Open",
                "button_emoji": "",
                "button_style": "primary",
                "category_name": "Support",
                "channel": {"source_id": "555", "name": "support", "type": "channel"},
                "publication": {"message_id": "999", "status": "published"},
                "required_roles": [],
                "blocked_roles": [],
                "payload": None,
                "questions": [],
            }],
        },
    }, guild=OTHER)
    catalog = {
        "roles": [{"id": "42", "name": "Red"}, {"id": "43", "name": "Staff"}],
        "channels": [{"id": "80", "name": "support", "kind": "text"}, {"id": "81", "name": "Tickets", "kind": "category"}],
        "emojis": [],
    }
    await apply(GUILD, "Target", bundle, catalog, {}, ["role_menus", "tickets"], "merge", TEST_ROOT)
    menu = (await list_menus(GUILD))[0]
    assert menu["message_id"] is None
    assert menu["publish_status"] == "draft"
    assert menu["options"][0]["role_id"] == "42"
    home = await workspace(GUILD)
    assert home["tickets"] == [] or "transcript" not in home
    assert home["panels"][0]["published_message_id"] is None
    assert home["panels"][0]["publish_status"] == "draft"
    exported = await build_export(GUILD, "Target", ["tickets"], catalog)
    assert "tickets" not in exported["modules"]["tickets"]
    assert "transcripts" not in exported["modules"]["tickets"]


async def test_same_guild_restore_keeps_a_message_that_still_exists(db_reset):
    bundle = _bundle({
        "role_menus": {"menus": [{
            "name": "Colors",
            "source": "created",
            "type": "button",
            "mode": "toggle",
            "button_style": "toggle",
            "enabled": True,
            "max_roles": None,
            "channel": {"source_id": "555", "name": "support", "type": "channel"},
            "payload": {"content": "Pick", "embeds": [], "buttons": []},
            "publication": {"message_id": "999", "status": "published"},
            "options": [{"role": _role(ROLE, "Red"), "emoji": "🔴", "label": "Red", "description": ""}],
        }]},
        "tickets": {
            "settings": {"cooldown_seconds": 60, "max_open": 1, "auto_close_hours": None, "grace_minutes": 60, "transcript_channel": None, "name_format": "ticket-{number}"},
            "categories": [{"name": "Support", "discord_category": {"source_id": "777", "name": "Tickets", "type": "category"}, "staff_roles": [_role(ROLE, "Staff")], "required_roles": [], "blocked_roles": [], "name_format": "ticket-{number}", "ping_staff": True}],
            "panels": [{
                "title": "Help",
                "message": "Open a ticket",
                "button_label": "Open",
                "button_emoji": "",
                "button_style": "primary",
                "category_name": "Support",
                "channel": {"source_id": "555", "name": "support", "type": "channel"},
                "publication": {"message_id": "999", "status": "published"},
                "required_roles": [],
                "blocked_roles": [],
                "payload": None,
                "questions": [],
            }],
        },
    })
    catalog = {
        "roles": [{"id": ROLE, "name": "Red"}, {"id": ROLE, "name": "Staff"}],
        "channels": [{"id": "555", "name": "support", "kind": "text"}, {"id": "777", "name": "Tickets", "kind": "category"}],
        "emojis": [],
    }
    result = await apply(GUILD, "Source", bundle, catalog, {}, ["role_menus", "tickets"], "merge", TEST_ROOT, {"999"})
    assert result["result"] == "applied"
    menu = (await list_menus(GUILD))[0]
    assert menu["message_id"] == "999"
    assert menu["publish_status"] == "published"
    panel = (await workspace(GUILD))["panels"][0]
    assert panel["published_message_id"] == "999"
    assert panel["publish_status"] == "published"


def test_emoji_gap_blocks_the_menu():
    modules = {"role_menus": {"menus": [{"options": [{"emoji": "<:vip:9007199254740993>"}]}]}}
    rows = mapping_rows(modules, ["role_menus"], same_guild=False, catalog={"emojis": []}, choices=None)
    assert rows[0]["status"] == "missing"
    assert rows[0]["type"] == "emoji"


async def test_transfer_api_is_guild_scoped(api_client):
    client, _app = api_client
    headers = await auth_headers(TEST_ROOT)
    exported = await client.post(f"/api/v1/guilds/{TEST_GUILD_A}/config-transfer/export", headers=headers, json={"modules": ["join_roles"]})
    assert exported.status_code == 200, exported.text
    body = exported.json()
    assert body["source"]["guild_id"] == str(TEST_GUILD_A)
    assert isinstance(body["source"]["guild_id"], str)
    rejected = await client.post(f"/api/v1/guilds/{TEST_GUILD_A}/config-transfer/validate", headers=headers, json={"bundle": {"format": "cls-config", "version": 9, "source": {"guild_id": "1"}, "modules": {}}})
    assert rejected.status_code == 422
    assert "version" in rejected.json()["detail"]
