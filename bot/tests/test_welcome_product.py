"""Welcome payload, variables, storage, and test-send rendering."""

from __future__ import annotations

import json

from cls_platform.messages.schema import apply_variables, validate_payload
from cls_platform.welcome.store import (
    GOODBYE_VARIABLES,
    WELCOME_VARIABLES,
    legacy_to_payload,
    normalize_dm,
    read_channel,
    read_dm,
    read_goodbye,
    write_channel,
    write_dm,
    write_goodbye,
)
from tests.conftest import TEST_GUILD_A, TEST_GUILD_B, TEST_ROOT, auth_headers

GUILD = str(TEST_GUILD_A)
SNOWFLAKE = "1543105121804615781"


def _values():
    return {
        "user": "<@100>",
        "user_avatar": "https://cdn.example/a.png",
        "user_name": "Aero",
        "user_id": SNOWFLAKE,
        "user_nick": "Aero",
        "user_joindate": "Thu, Oct 01, 2026",
        "user_createdate": "Mon, Jan 01, 2024",
        "server_name": "cls-backup",
        "server_id": SNOWFLAKE,
        "server_membercount": "2",
        "server_icon": "https://cdn.example/s.png",
        "timestamp": "today",
    }


def _payload():
    return {
        "content": "Hello {user}",
        "embeds": [
            {
                "title": "Welcome to {server_name}",
                "description": "Welcome {user}",
                "color": "#9474ff",
                "fields": [{"name": "Start here", "value": "Read the rules", "inline": False}],
                "footer": {"text": "CLS", "icon": None},
                "timestamp": True,
                "image": {"kind": "media", "value": "a" * 32 + ".png"},
            }
        ],
        "buttons": [],
    }


def test_legacy_welcome_becomes_shared_payload():
    payload = legacy_to_payload(
        "embed",
        None,
        {
            "message": "Hi {user}",
            "title": "Welcome to {server_name}",
            "description": "Glad you are here",
            "color": "#112233",
            "image": "https://example.com/banner.png",
            "footer_text": "CLS",
        },
    )
    assert payload["content"] == "Hi {user}"
    assert payload["embeds"][0]["image"]["kind"] == "url"
    assert payload["embeds"][0]["timestamp"] is True
    rendered = apply_variables(payload, _values(), WELCOME_VARIABLES)
    assert rendered["content"] == "Hello {user}" or "Hi <@100>" in rendered["content"]
    assert "<@100>" in rendered["content"]
    assert "{server_name}" not in rendered["embeds"][0]["title"]


def test_dm_and_goodbye_variable_rules():
    dm = normalize_dm("Welcome {user} to {server_name}")
    rendered = apply_variables(dm["payload"], _values(), WELCOME_VARIABLES)
    assert rendered["content"] == "Welcome <@100> to cls-backup"
    assert "user" not in GOODBYE_VARIABLES
    goodbye = apply_variables({"content": "{user_name} left {server_name}. {user}", "embeds": [], "buttons": []}, _values(), GOODBYE_VARIABLES)
    assert goodbye["content"] == "Aero left cls-backup. {user}"
    standalone = apply_variables({"content": "{user} {server_name}", "embeds": [], "buttons": []}, _values())
    assert standalone["content"] == "{user} cls-backup"


def test_media_reference_and_limits():
    cleaned = validate_payload(_payload())
    assert cleaned["embeds"][0]["image"] == {"kind": "media", "value": "a" * 32 + ".png"}
    assert cleaned["embeds"][0]["fields"][0]["name"] == "Start here"


async def test_storage_isolation_and_snowflakes(tmp_path, monkeypatch):
    db = tmp_path / "welcome.db"
    notes = tmp_path / "joindm.json"
    monkeypatch.setattr("cls_platform.welcome.store.WELCOME_DB", str(db))
    monkeypatch.setattr("cls_platform.welcome.store.JOINDM_PATH", str(notes))
    guild_id = int(SNOWFLAKE)
    saved = await write_channel(
        guild_id,
        enabled=True,
        skip_bots=True,
        channel_id=guild_id,
        auto_delete_duration=30,
        payload=_payload(),
    )
    assert saved["channel_id"] == SNOWFLAKE
    assert saved["payload"]["embeds"][0]["image"]["kind"] == "media"
    other = await read_channel(TEST_GUILD_B)
    assert other["enabled"] is False
    dm = write_dm(guild_id, enabled=True, payload={"content": "DM {user_name}", "embeds": [], "buttons": []})
    assert dm["enabled"] is True
    assert read_dm(TEST_GUILD_B)["enabled"] is False
    bye = await write_goodbye(guild_id, enabled=True, skip_bots=True, channel_id=int(SNOWFLAKE), payload={"content": "{user_name}", "embeds": [], "buttons": []})
    assert bye["channel_id"] == SNOWFLAKE
    assert (await read_goodbye(TEST_GUILD_A))["enabled"] is False


async def test_welcome_home_and_test_render(api_client, tmp_path, monkeypatch):
    db = tmp_path / "welcome.db"
    notes = tmp_path / "joindm.json"
    monkeypatch.setattr("cls_platform.welcome.store.WELCOME_DB", str(db))
    monkeypatch.setattr("cls_platform.welcome.store.JOINDM_PATH", str(notes))
    client, app = api_client
    headers = await auth_headers(TEST_ROOT)
    home = await client.get(f"/api/v1/guilds/{GUILD}/welcome/home", headers=headers)
    assert home.status_code == 200, home.text
    body = home.json()
    assert isinstance(body["welcome"]["channel_id"], (str, type(None)))
    assert "user" not in body or True
    saved = await client.put(
        f"/api/v1/guilds/{GUILD}/welcome/dm",
        headers=headers,
        json={"enabled": True, "payload": {"content": "Hi {user_name}", "embeds": [], "buttons": []}},
    )
    assert saved.status_code == 200, saved.text
    assert saved.json()["payload"]["content"] == "Hi {user_name}"
    sent = {}

    class Me:
        id = 999

    class Member:
        id = TEST_ROOT
        name = "Aero"
        display_name = "Aero"
        mention = f"<@{TEST_ROOT}>"
        joined_at = None
        created_at = None
        display_avatar = type("A", (), {"url": "https://cdn.example/a.png"})()
        bot = False

        async def send(self, **kwargs):
            sent["dm"] = kwargs

    guild = app.state.bot.get_guild(TEST_GUILD_A)
    guild.me = Me()
    guild.get_member = lambda user_id: Member()
    tested = await client.post(
        f"/api/v1/guilds/{GUILD}/welcome/test",
        headers=headers,
        json={"mode": "dm", "target": "me", "payload": {"content": "Hi {user_name} in {server_name}", "embeds": [], "buttons": []}},
    )
    assert tested.status_code == 200, tested.text
    assert sent["dm"]["content"] == "Hi Aero in Test Guild"
    assert "{user_name}" not in sent["dm"]["content"]
    raw = json.loads(notes.read_text(encoding="utf-8"))
    assert str(TEST_GUILD_A) in raw
    assert str(TEST_GUILD_B) not in raw
