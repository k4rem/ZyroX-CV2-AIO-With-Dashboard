"""Logging product: snapshots, permission language, embeds, and a single pipeline."""

from pathlib import Path

from cls_platform.logging.entities import snapshot_channel, snapshot_role, snapshot_user
from cls_platform.logging.permissions import overwrite_diff, permission_diff
from cls_platform.logging.pipeline import LEGACY_DELIVERY_DISABLED, delivery_state, message_ignored
from cls_platform.logging.present import present
from cls_platform.logging.render import render_discord
from cogs.cog_loader import _cog_specs

SNOW = "1543105121804615999"


class _Avatar:
    url = "https://cdn.example/avatar.png"


class _User:
    id = int(SNOW)
    display_name = "Alice"
    name = "alice"
    display_avatar = _Avatar()


class _Role:
    id = 200
    name = "VIP"
    color = type("Color", (), {"value": 0xC4A15A})()


class _Channel:
    id = 300
    name = "mod-log"
    type = type("Kind", (), {"name": "text"})()


def test_entity_snapshots_keep_snowflakes_as_strings():
    user = snapshot_user(_User())
    assert user["id"] == SNOW
    assert user["display_name"] == "Alice"
    assert user["username"] == "alice"
    assert user["avatar_url"] == "https://cdn.example/avatar.png"
    assert snapshot_role(_Role()) == {"id": "200", "name": "VIP", "color": "#c4a15a"}
    assert snapshot_channel(_Channel())["type"] == "text"
    assert snapshot_user(None) is None


def test_permission_diff_is_readable():
    manage_messages = 1 << 13
    manage_roles = 1 << 28
    mention_everyone = 1 << 17
    diff = permission_diff(mention_everyone, manage_messages | manage_roles)
    assert diff["granted"] == ["Manage Messages", "Manage Roles"]
    assert diff["revoked"] == ["Mention Everyone"]
    lines = overwrite_diff(
        [{"id": "9", "name": "Mod", "kind": "role", "allow": 0, "deny": 0}],
        [{"id": "9", "name": "Mod", "kind": "role", "allow": manage_messages, "deny": mention_everyone}],
    )
    assert any(line["dashboard"] == "Manage Messages" for line in lines)
    assert any("Mention Everyone" in line["dashboard"] for line in lines)
    assert all(SNOW not in line["dashboard"] for line in lines)


def test_member_roles_and_message_edit_read_without_raw_ids():
    roles = present(
        {
            "category": "member_moderation",
            "event_type": "member_roles",
            "actor_id": SNOW,
            "target_id": "222",
            "before": {"roles": [{"id": "2", "name": "Muted", "color": None}]},
            "after": {"roles": [{"id": "2", "name": "Muted", "color": None}, {"id": "9", "name": "VIP", "color": "#c4a15a"}]},
            "metadata": {
                "entities": {
                    "actor": {"id": SNOW, "display_name": "Karim", "username": "karim", "avatar_url": "https://cdn.example/k.png"},
                    "target": {"id": "222", "display_name": "Ahmed", "username": "ahmed", "avatar_url": "https://cdn.example/a.png"},
                },
                "reason": "promo",
            },
        }
    )
    assert roles["title"] == "Member role updated"
    assert roles["summary"] == "Karim updated Ahmed's roles"
    assert "+ VIP" in roles["change_line"]
    assert SNOW not in roles["summary"]
    assert SNOW not in roles["change_line"]
    assert any(change["label"] == "Roles added" and change["value"] == "VIP" for change in roles["changes"])
    assert any(change["label"] == "Moderator" and change["value"] == "Karim" for change in roles["changes"])
    assert "User ID: 222" in roles["footer"]
    assert SNOW not in roles["footer"]
    embed = render_discord({"event_type": "member_roles", "presentation": roles, "metadata": {}})
    assert embed["title"] == "Member role updated"
    assert embed["author_name"] == "Karim"
    assert any("<@&9>" in field["value"] for field in embed["fields"])

    edited = present(
        {
            "category": "message_events",
            "event_type": "message_edit",
            "actor_id": SNOW,
            "target_id": "900",
            "channel_id": "300",
            "before": {"content": "hello"},
            "after": {"content": "hello there"},
            "metadata": {
                "entities": {
                    "actor": {"id": SNOW, "display_name": "Alice", "username": "alice", "avatar_url": None},
                    "channel": {"id": "300", "name": "general", "type": "text"},
                },
                "jump_url": "https://discord.com/channels/1/300/900",
            },
        }
    )
    assert edited["title"] == "Message edited"
    assert "Alice" in edited["summary"]
    assert "#general" in edited["summary"]
    assert SNOW not in edited["summary"]
    values = {change["label"]: change["value"] for change in edited["changes"]}
    assert values["Old"] == "hello"
    assert values["New"] == "hello there"
    assert "Jump to message" in values
    rendered = render_discord(
        {
            "category": "message_events",
            "event_type": "message_edit",
            "actor_id": SNOW,
            "target_id": "900",
            "before": {"content": "hello"},
            "after": {"content": "hello there"},
            "metadata": {
                "entities": {
                    "actor": {"id": SNOW, "display_name": "Alice", "username": "alice"},
                    "channel": {"id": "300", "name": "general", "type": "text"},
                },
                "jump_url": "https://discord.com/channels/1/300/900",
            },
        }
    )
    assert any("Jump to message" in field["value"] for field in rendered["fields"])
    assert "Message ID: 900" in rendered["footer"]
    assert rendered["title"] != SNOW


def test_routing_ignores_and_legacy_pipeline_is_off():
    assert message_ignored(channel_id=5, author_id=1, author_role_ids=[2], ignores={"channels": [5], "roles": [], "users": []})
    assert message_ignored(channel_id=1, author_id=9, author_role_ids=[], ignores={"channels": [], "roles": [], "users": [9]})
    assert message_ignored(channel_id=1, author_id=3, author_role_ids=[8], ignores={"channels": [], "roles": [8], "users": []})
    assert not message_ignored(channel_id=1, author_id=3, author_role_ids=[4], ignores={"channels": [], "roles": [], "users": []})
    assert delivery_state(enabled=True, channel_id=SNOW, channel_found=True, can_send=True, checked=True) == "delivering"
    assert delivery_state(enabled=True, channel_id=None, channel_found=False, can_send=False, checked=True) == "stored_only"
    assert delivery_state(enabled=True, channel_id=SNOW, channel_found=False, can_send=False, checked=True) == "channel_unavailable"
    assert delivery_state(enabled=True, channel_id=SNOW, channel_found=True, can_send=False, checked=True) == "missing_permission"
    specs = {spec.class_name: spec for spec in _cog_specs()}
    assert specs["Logging"].skip is True
    assert specs["LoggingV2"].skip is False
    assert specs["LoggingV2"].required is True
    assert LEGACY_DELIVERY_DISABLED is True
    source = Path(__file__).resolve().parents[1].joinpath("cogs", "commands", "logging.py").read_text(encoding="utf-8")
    assert "PIPELINE_RETIRED = True" in source
    assert "if PIPELINE_RETIRED:" in source
