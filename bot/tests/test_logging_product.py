"""Logging product: snapshots, permission language, embeds, and a single pipeline."""

from pathlib import Path

from cls_platform.logging.entities import snapshot_channel, snapshot_role, snapshot_user
from cls_platform.logging.permissions import overwrite_diff, permission_diff
from cls_platform.logging.pipeline import LEGACY_DELIVERY_DISABLED, delivery_state, message_ignored, resolve_delivery
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
            "category": "role_events",
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
    assert roles["title"] == "Member roles updated"
    assert roles["summary"] == "Karim updated Ahmed's roles"
    assert "+ VIP" in roles["change_line"]
    assert SNOW not in roles["summary"]
    assert SNOW not in roles["change_line"]
    assert any(change["label"] == "Roles added" and change["value"] == "VIP" for change in roles["changes"])
    assert any(change["label"] == "Moderator" and change["value"] == "Karim" for change in roles["changes"])
    assert "User ID: 222" in roles["identifiers"]
    assert "User ID" not in (roles["footer"] or "")
    assert SNOW not in roles["footer"]
    embed = render_discord({"event_type": "member_roles", "presentation": roles, "metadata": {}})
    assert embed["title"] == "Member roles updated"
    assert embed["author_name"] == "Ahmed"
    assert embed["author_icon"] == "https://cdn.example/a.png"
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
    assert values["Before"] == "hello"
    assert values["After"] == "hello there"
    assert "hello" in edited["change_line"] and "hello there" in edited["change_line"]
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
    assert rendered["jump_url"] == "https://discord.com/channels/1/300/900"
    assert all("Jump to message" not in field["value"] for field in rendered["fields"])
    assert "Message ID" not in rendered["footer"]
    assert rendered["footer"].startswith("CLS •")
    assert "Message Edited" in rendered["title"]
    assert rendered["title"] != SNOW
    identified = render_discord(
        {
            "category": "message_events",
            "event_type": "message_edit",
            "actor_id": SNOW,
            "target_id": "900",
            "before": {"content": "hello"},
            "after": {"content": "hello there"},
            "presentation": edited,
            "metadata": {"jump_url": "https://discord.com/channels/1/300/900"},
        },
        {"show_ids": True, "colors": {"message_events": "#112233"}, "style": "detailed", "show_jump": False},
    )
    assert identified["color"] == 0x112233
    assert "Message ID: 900" in identified["footer"]
    assert identified["jump_url"] is None
    compact = render_discord(
        {"category": "message_events", "event_type": "message_edit", "presentation": edited, "metadata": {}},
        {"style": "compact"},
    )
    assert compact["fields"] == []
    assert "hello" in compact["description"]


def test_event_delivery_inherits_category_until_overridden():
    inherited = resolve_delivery(category_enabled=True, category_channel_id="10", mode="inherit")
    assert inherited == {"capture": True, "deliver": True, "channel_id": "10", "mode": "inherit"}
    assert resolve_delivery(category_enabled=False, category_channel_id="10")["deliver"] is False
    custom = resolve_delivery(category_enabled=True, category_channel_id="10", mode="custom", event_channel_id="20")
    assert custom["channel_id"] == "20" and custom["deliver"] is True
    stored = resolve_delivery(category_enabled=True, category_channel_id="10", mode="stored_only")
    assert stored["capture"] is True and stored["deliver"] is False
    disabled = resolve_delivery(category_enabled=True, category_channel_id="10", mode="disabled")
    assert disabled["capture"] is False and disabled["deliver"] is False


def test_routing_ignores_and_legacy_pipeline_is_off():
    assert message_ignored(channel_id=5, author_id=1, author_role_ids=[2], ignores={"channels": [5], "roles": [], "users": []})
    assert message_ignored(channel_id=1, author_id=9, author_role_ids=[], ignores={"channels": [], "roles": [], "users": [9]})
    assert message_ignored(channel_id=1, author_id=3, author_role_ids=[8], ignores={"channels": [], "roles": [8], "users": []})
    assert not message_ignored(channel_id=1, author_id=3, author_role_ids=[4], ignores={"channels": [], "roles": [], "users": []})
    assert delivery_state(enabled=True, channel_id=SNOW, resolution="found", can_view=True, can_send=True, can_embed=True) == "delivering"
    assert delivery_state(enabled=False, channel_id=SNOW, resolution="found", can_view=True, can_send=True, can_embed=True) == "stored_only"
    assert delivery_state(enabled=True, channel_id=None, resolution="missing") == "missing_channel"
    assert delivery_state(enabled=True, channel_id=SNOW, resolution="unavailable") == "channel_unavailable"
    assert delivery_state(enabled=True, channel_id=SNOW, resolution="forbidden") == "bot_cannot_view"
    assert delivery_state(enabled=True, channel_id=SNOW, resolution="found", can_view=True, can_send=False, can_embed=False) == "bot_cannot_send"
    assert delivery_state(enabled=True, channel_id=SNOW, resolution="found", can_view=True, can_send=True, can_embed=False) == "bot_cannot_embed"
    specs = {spec.class_name: spec for spec in _cog_specs()}
    assert specs["Logging"].skip is True
    assert specs["LoggingV2"].skip is False
    assert specs["LoggingV2"].required is True
    assert LEGACY_DELIVERY_DISABLED is True
    source = Path(__file__).resolve().parents[1].joinpath("cogs", "commands", "logging.py").read_text(encoding="utf-8")
    assert "PIPELINE_RETIRED = True" in source
    assert "if PIPELINE_RETIRED:" in source
