"""Message builder: schema, media, templates, and CLS-owned sends."""

from __future__ import annotations

import io

import discord
import pytest
from PIL import Image

from cls_platform import storage
from cls_platform.messages.media import MediaError, inspect_image, valid_key
from cls_platform.messages.schema import MessageSchemaError, apply_variables, validate_payload
from tests.conftest import TEST_CHANNEL_A, TEST_GUILD_A, TEST_GUILD_B, TEST_ROOT, auth_headers

GUILD = str(TEST_GUILD_A)
OTHER = str(TEST_GUILD_B)


def _png(color=(120, 80, 200)) -> bytes:
    image = Image.new("RGBA", (8, 8), color + (255,))
    out = io.BytesIO()
    image.save(out, format="PNG")
    return out.getvalue()


def _payload() -> dict:
    return {
        "content": "Welcome to {server_name}",
        "embeds": [
            {
                "title": "Server Rules",
                "description": "Members: {server_membercount}",
                "color": "#9474ff",
                "author": {"name": "CLS", "url": "https://example.com", "icon": None},
                "fields": [
                    {"name": "One", "value": "A", "inline": True},
                    {"name": "Two", "value": "B", "inline": True},
                    {"name": "Three", "value": "C", "inline": False},
                ],
                "footer": {"text": "CLS", "icon": None},
                "timestamp": True,
                "image": {"kind": "url", "value": "https://example.com/banner.png"},
            },
            {"title": "Second", "description": "More", "fields": []},
        ],
        "buttons": [{"label": "Rules", "url": "https://example.com/rules", "emoji": "✅"}],
    }


def test_limits_variables_and_roundtrip():
    cleaned = validate_payload(_payload())
    assert len(cleaned["embeds"]) == 2
    assert cleaned["embeds"][0]["fields"][0]["inline"] is True
    assert cleaned["buttons"][0]["label"] == "Rules"
    again = validate_payload(cleaned)
    assert again == cleaned
    rendered = apply_variables(cleaned, {"server_name": "cls-backup", "server_membercount": "2", "server_icon": "", "timestamp": "<t:1:f>"})
    assert "cls-backup" in rendered["content"]
    assert "{server_name}" not in rendered["content"]
    assert "2" in rendered["embeds"][0]["description"]
    assert "{user}" in apply_variables({"content": "{user}", "embeds": [], "buttons": []}, {})["content"]
    with pytest.raises(MessageSchemaError):
        validate_payload({"content": "x" * 2001, "embeds": [], "buttons": []})
    with pytest.raises(MessageSchemaError):
        validate_payload({"content": "", "embeds": [{"title": "T", "fields": [{"name": "n", "value": "v"}]}] * 11, "buttons": []})
    with pytest.raises(MessageSchemaError):
        validate_payload({"content": "ok", "embeds": [{"title": "T", "fields": [{"name": "n", "value": "v"}] * 26}], "buttons": []})
    with pytest.raises(MessageSchemaError):
        validate_payload({"content": "", "embeds": [], "buttons": [], "token": "nope"})
    huge = {
        "content": "",
        "embeds": [{
            "title": "T" * 256,
            "description": "D" * 4096,
            "fields": [{"name": "N" * 256, "value": "V" * 1024}, {"name": "M" * 256, "value": "W" * 1024}],
        }],
        "buttons": [],
    }
    with pytest.raises(MessageSchemaError) as err:
        validate_payload(huge)
    assert any("6000" in item or "limit" in item for item in err.value.errors)


def test_media_magic_size_and_path():
    encoded = inspect_image(_png())
    assert encoded.startswith(b"\x89PNG")
    jpeg = io.BytesIO()
    Image.new("RGB", (4, 4), (1, 2, 3)).save(jpeg, format="JPEG")
    assert inspect_image(jpeg.getvalue()).startswith(b"\x89PNG")
    with pytest.raises(MediaError):
        inspect_image(b"<svg xmlns='http://www.w3.org/2000/svg'></svg>")
    with pytest.raises(MediaError):
        inspect_image(b"not-an-image")
    with pytest.raises(MediaError):
        inspect_image(b"\x00" * (4 * 1024 * 1024 + 1))
    assert valid_key("a" * 32 + ".png")
    assert not valid_key("../secret.png")
    assert not valid_key("..\\secret.png")
    with pytest.raises(storage.StorageError):
        storage._safe_path("g1", "../secret.png")
    with pytest.raises(storage.StorageError):
        storage._safe_path("../g1", "a" * 32 + ".png")


async def test_template_isolation_and_snowflakes(api_client):
    client, _app = api_client
    headers = await auth_headers(TEST_ROOT)
    created = await client.post(f"/api/v1/guilds/{GUILD}/messages/templates", headers=headers, json={"name": "Server Rules", "payload": _payload()})
    assert created.status_code == 200, created.text
    body = created.json()
    assert body["guild_id"] == GUILD
    assert isinstance(body["guild_id"], str)
    assert len(GUILD) >= 17
    missing = await client.get(f"/api/v1/guilds/{OTHER}/messages/templates/{body['id']}", headers=headers)
    assert missing.status_code == 404
    listed = await client.get(f"/api/v1/guilds/{OTHER}/messages/templates", headers=headers)
    assert listed.json()["templates"] == []
    renamed = await client.patch(
        f"/api/v1/guilds/{GUILD}/messages/templates/{body['id']}",
        headers=headers,
        json={"name": "Server Rules 2"},
    )
    assert renamed.status_code == 200
    assert renamed.json()["name"] == "Server Rules 2"
    exported = renamed.json()["payload"]
    imported = await client.post(
        f"/api/v1/guilds/{GUILD}/messages/templates",
        headers=headers,
        json={"name": "Imported", "payload": exported},
    )
    assert imported.status_code == 200
    assert imported.json()["payload"]["embeds"][0]["title"] == "Server Rules"
    deleted = await client.delete(f"/api/v1/guilds/{GUILD}/messages/templates/{body['id']}", headers=headers)
    assert deleted.status_code == 200


async def test_media_emoji_and_bad_upload(api_client, tmp_path, monkeypatch):
    client, _app = api_client
    headers = await auth_headers(TEST_ROOT)
    monkeypatch.setattr(storage, "STORAGE_ROOT", str(tmp_path))
    monkeypatch.setattr("cls_platform.storage.STORAGE_ROOT", str(tmp_path))
    good = await client.post(
        f"/api/v1/guilds/{GUILD}/media",
        headers=headers,
        files={"file": ("banner.png", _png(), "image/png")},
    )
    assert good.status_code == 200, good.text
    key = good.json()["key"]
    assert valid_key(key)
    fetched = await client.get(f"/api/v1/guilds/{GUILD}/media/{key}", headers=headers)
    assert fetched.status_code == 200
    assert fetched.content.startswith(b"\x89PNG")
    other = await client.get(f"/api/v1/guilds/{OTHER}/media/{key}", headers=headers)
    assert other.status_code == 404
    bad = await client.post(
        f"/api/v1/guilds/{GUILD}/media",
        headers=headers,
        files={"file": ("note.txt", b"hello", "text/plain")},
    )
    assert bad.status_code == 422
    huge = await client.post(
        f"/api/v1/guilds/{GUILD}/media",
        headers=headers,
        files={"file": ("big.png", b"\x00" * (4 * 1024 * 1024 + 8), "image/png")},
    )
    assert huge.status_code == 422
    traversal = await client.get(f"/api/v1/guilds/{GUILD}/media/..%2Fsecret.png", headers=headers)
    assert traversal.status_code in {404, 422}
    emojis = await client.get(f"/api/v1/guilds/{GUILD}/emojis", headers=headers)
    assert emojis.status_code == 200
    assert emojis.json()["emojis"] == []


def _arm_channel(fake_bot, *, author_id: int, missing: bool = False):
    guild = fake_bot.get_guild(TEST_GUILD_A)
    channel = guild.get_channel(TEST_CHANNEL_A)
    guild.me = type("Me", (), {"id": 999})()
    sent = {"id": 555000000000000111}

    class Perms:
        send_messages = True
        embed_links = True

    class Msg:
        def __init__(self, message_id, owner_id):
            self.id = message_id
            self.author = type("A", (), {"id": owner_id})()

        async def edit(self, **kwargs):
            sent["edit"] = kwargs

        async def delete(self):
            sent["deleted"] = True

    channel.permissions_for = lambda _me: Perms()

    async def send(**kwargs):
        sent["kwargs"] = kwargs
        return Msg(sent["id"], 999)

    async def fetch_message(message_id):
        if missing or message_id != sent["id"]:
            response = type("R", (), {"status": 404, "reason": "Not Found"})()
            raise discord.NotFound(response, "missing")
        return Msg(message_id, author_id)

    channel.send = send
    channel.fetch_message = fetch_message
    return sent


async def test_send_edit_owned_and_missing(api_client):
    client, app = api_client
    headers = await auth_headers(TEST_ROOT)
    sent = _arm_channel(app.state.bot, author_id=999)
    created = await client.post(
        f"/api/v1/guilds/{GUILD}/messages/send",
        headers=headers,
        json={"channel_id": str(TEST_CHANNEL_A), "payload": _payload()},
    )
    assert created.status_code == 200, created.text
    body = created.json()
    assert body["message_id"] == "555000000000000111"
    assert body["channel_id"] == str(TEST_CHANNEL_A)
    assert "cls-backup" not in (sent["kwargs"].get("content") or "")
    assert "Test Guild" in (sent["kwargs"].get("content") or "")
    updated = await client.patch(
        f"/api/v1/guilds/{GUILD}/messages/sent/{body['id']}",
        headers=headers,
        json={"payload": {**_payload(), "content": "Updated rules"}},
    )
    assert updated.status_code == 200, updated.text
    assert updated.json()["message_id"] == body["message_id"]
    assert sent["edit"]["content"] == "Updated rules"
    foreign = await client.patch(
        f"/api/v1/guilds/{OTHER}/messages/sent/{body['id']}",
        headers=headers,
        json={"payload": _payload()},
    )
    assert foreign.status_code == 404
    _arm_channel(app.state.bot, author_id=12345)
    denied = await client.patch(
        f"/api/v1/guilds/{GUILD}/messages/sent/{body['id']}",
        headers=headers,
        json={"payload": _payload()},
    )
    assert denied.status_code == 403
    _arm_channel(app.state.bot, author_id=999, missing=True)
    listed = await client.get(f"/api/v1/guilds/{GUILD}/messages/sent", headers=headers)
    row = listed.json()["sent"][0]
    assert row["missing"] is True
    resent = await client.post(f"/api/v1/guilds/{GUILD}/messages/sent/{body['id']}/resend", headers=headers)
    assert resent.status_code == 200, resent.text
    assert resent.json()["missing"] is False
    assert resent.json()["message_id"] == "555000000000000111"
