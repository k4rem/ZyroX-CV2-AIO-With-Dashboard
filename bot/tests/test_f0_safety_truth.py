"""F0 safety and truth regressions."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import aiosqlite
import pytest

from api.validators.discord_resources import _collect_resource_ids, _parse_snowflake
from cls_platform.automod_compat import (
    apply_punishment_update,
    effective_punishments,
    enforce,
    normalize_action,
    prepare_punishment_rows,
    rule_action,
)
from cls_platform.invc_gate import invc_role_should_apply
from cls_platform.vanity_safety import VANITY_UNAVAILABLE, vanity_automation_allowed
from cls_platform.verification.engine import VERIFICATION_ENABLE_BLOCK
from tests.conftest import TEST_CHANNEL_A, TEST_GUILD_A, TEST_ROLE_A, TEST_ROLE_B, TEST_USER, auth_headers

BIG = 1543105121804615781
ROOT = Path(__file__).resolve().parents[1]


class _Perms:
    def __init__(self, **flags):
        for name, value in flags.items():
            setattr(self, name, value)


class _Role:
    def __init__(self, position):
        self.position = position


class _Member:
    def __init__(self, member_id=5, owner=False, admin=False, position=1):
        self.id = member_id
        self.mention = f"<@{member_id}>"
        self.guild_permissions = _Perms(administrator=admin, manage_messages=False, moderate_members=False, kick_members=False, ban_members=False)
        self.top_role = _Role(position)
        self.owner = owner
        self.edits = []
        self.kicks = []
        self.bans = []

    async def edit(self, **kwargs):
        self.edits.append(kwargs)

    async def kick(self, reason=None):
        self.kicks.append(reason)

    async def ban(self, reason=None):
        self.bans.append(reason)


class _Message:
    def __init__(self, member, manage_messages=True):
        self.author = member
        self.deleted = 0
        self.channel = type("C", (), {"id": 9, "mention": "<#9>"})()
        me = type("Me", (), {"guild_permissions": _Perms(manage_messages=manage_messages, moderate_members=True, kick_members=True, ban_members=True), "top_role": _Role(10)})()
        self.guild = type("G", (), {"id": 42, "owner_id": 2, "me": me, "get_channel": lambda self, _cid: None})()

    async def delete(self):
        self.deleted += 1


async def _punish_db(path: Path):
    async with aiosqlite.connect(path) as db:
        await db.execute(
            """
            CREATE TABLE automod_punishments (
                guild_id INTEGER,
                event TEXT,
                punishment TEXT,
                PRIMARY KEY (guild_id, event)
            )
            """
        )
        await db.commit()


def test_allowlist_cog_imports_without_building_a_client():
    import cogs.events.on_guild as mod

    assert not hasattr(mod, "client")
    cog = mod.Guild(object())
    assert cog.bot is not None


async def test_allowlist_join_leaves_and_records_the_reason(capsys):
    import cogs.events.on_guild as mod

    left = []

    class Guild:
        id = 555000000000000555
        name = "stranger"

        async def leave(self):
            left.append(self.id)

    cog = mod.Guild(object())
    with (
        patch("cls_platform.security.allowlist_sweep.allowlist_config_status", return_value="ok"),
        patch("utils.guild_allowlist.ALLOWLIST_ENFORCED", True),
        patch("utils.guild_allowlist.is_guild_allowed", return_value=False),
        patch("cls_platform.config.OPS_GUILD_ID", None),
    ):
        await cog.on_guild_join(Guild())
    assert left == [555000000000000555]
    assert "not on ALLOWED_GUILD_IDS" in capsys.readouterr().out


async def test_allowlist_join_keeps_allowed_ops_and_broken_config():
    import cogs.events.on_guild as mod

    class Guild:
        id = 555
        name = "kept"

        def __init__(self):
            self.left = False

        async def leave(self):
            self.left = True

    cog = mod.Guild(object())
    allowed = Guild()
    with (
        patch("cls_platform.security.allowlist_sweep.allowlist_config_status", return_value="ok"),
        patch("utils.guild_allowlist.ALLOWLIST_ENFORCED", True),
        patch("utils.guild_allowlist.is_guild_allowed", return_value=True),
        patch("cls_platform.config.OPS_GUILD_ID", None),
    ):
        await cog.on_guild_join(allowed)
    assert allowed.left is False

    ops = Guild()
    with (
        patch("cls_platform.security.allowlist_sweep.allowlist_config_status", return_value="ok"),
        patch("utils.guild_allowlist.ALLOWLIST_ENFORCED", True),
        patch("utils.guild_allowlist.is_guild_allowed", return_value=False),
        patch("cls_platform.config.OPS_GUILD_ID", 555),
    ):
        await cog.on_guild_join(ops)
    assert ops.left is False

    broken = Guild()
    with patch("cls_platform.security.allowlist_sweep.allowlist_config_status", return_value="malformed"):
        await cog.on_guild_join(broken)
    assert broken.left is False


async def test_allowlist_leave_failure_is_logged_and_does_not_crash():
    import cogs.events.on_guild as mod

    class Guild:
        id = 777
        name = "stuck"

        async def leave(self):
            raise RuntimeError("discord down")

    cog = mod.Guild(object())
    with (
        patch("cls_platform.security.allowlist_sweep.allowlist_config_status", return_value="ok"),
        patch("utils.guild_allowlist.ALLOWLIST_ENFORCED", True),
        patch("utils.guild_allowlist.is_guild_allowed", return_value=False),
        patch("cls_platform.config.OPS_GUILD_ID", None),
    ):
        await cog.on_guild_join(Guild())


def test_vanity_runtime_cannot_mass_assign():
    assert vanity_automation_allowed() is False
    source = (ROOT / "cogs" / "commands" / "vanityroles.py").read_text(encoding="utf-8")
    assert "add_roles" not in source
    assert "remove_roles" not in source
    assert "vanity_checker.start" not in source
    assert "VANITY_UNAVAILABLE" in source


def test_invc_enabled_switch():
    assert invc_role_should_apply(BIG, 0) is False
    assert invc_role_should_apply(BIG, None) is False
    assert invc_role_should_apply(0, 1) is False
    assert invc_role_should_apply(BIG, 1) is True
    assert invc_role_should_apply(str(BIG), "1") is True


def test_automod_normalizes_dashboard_keys_and_actions():
    assert normalize_action("delete") == "delete"
    assert normalize_action("Mute") == "mute"
    assert normalize_action("Kick") == "kick"
    assert normalize_action("Ban") == "ban"
    assert normalize_action("warn") is None
    assert prepare_punishment_rows({"anti_spam": "delete", "anti_mentions": "Mute"}) == [
        ("Anti spam", "delete"),
        ("Anti mass mention", "mute"),
    ]
    with pytest.raises(ValueError, match="not available"):
        prepare_punishment_rows({"anti_spam": "warn"})
    assert effective_punishments({"anti_spam": "warn", "Anti spam": "Mute", "Anti link": "delete"}) == {
        "anti_spam": "mute",
        "anti_links": "delete",
    }


async def test_automod_disable_removes_stale_rows(tmp_path):
    path = tmp_path / "automod.db"
    await _punish_db(path)
    async with aiosqlite.connect(path) as db:
        await db.execute(
            "INSERT INTO automod_punishments (guild_id, event, punishment) VALUES (?, ?, ?)",
            (42, "anti_spam", "warn"),
        )
        await db.execute(
            "INSERT INTO automod_punishments (guild_id, event, punishment) VALUES (?, ?, ?)",
            (42, "Anti spam", "Mute"),
        )
        await db.execute(
            "INSERT INTO automod_punishments (guild_id, event, punishment) VALUES (?, ?, ?)",
            (42, "Anti emoji spam", "Mute"),
        )
        await db.commit()
        await apply_punishment_update(db, 42, {})
        await db.commit()
        cursor = await db.execute("SELECT event, punishment FROM automod_punishments WHERE guild_id = ?", (42,))
        rows = await cursor.fetchall()
    assert rows == [("Anti emoji spam", "Mute")]
    assert await rule_action(42, "anti_spam", db_path=str(path)) is None


async def test_automod_delete_action_and_permission_failures(tmp_path):
    path = str(tmp_path / "automod.db")
    message = _Message(_Member())
    result = await enforce(None, message, rule="anti_spam", action="delete", reason="Spamming", messages=[message], db_path=path)
    assert result["ok"] is True
    assert message.deleted == 1
    async with aiosqlite.connect(path) as db:
        cursor = await db.execute("SELECT result, detail FROM automod_events")
        row = await cursor.fetchone()
    assert row[0] == "ok"

    blocked = _Message(_Member(), manage_messages=False)
    missing = await enforce(None, blocked, rule="anti_spam", action="delete", reason="Spamming", messages=[blocked], db_path=path)
    assert missing["ok"] is False
    assert missing["detail"] == "missing Manage Messages"
    assert blocked.deleted == 0

    owner = _Member(member_id=2)
    owner_message = _Message(owner)
    refused = await enforce(None, owner_message, rule="anti_spam", action="kick", reason="Spamming", messages=[], db_path=path)
    assert refused["detail"] == "target is the server owner"

    admin = _Member(admin=True)
    admin_message = _Message(admin)
    admin_result = await enforce(None, admin_message, rule="anti_links", action="ban", reason="link", messages=[], db_path=path)
    assert admin_result["detail"] == "target is an administrator"

    high = _Member(position=50)
    high_message = _Message(high)
    high_message.guild.me.guild_permissions.moderate_members = True
    hierarchy = await enforce(None, high_message, rule="anti_caps", action="mute", reason="caps", messages=[], db_path=path)
    assert hierarchy["detail"] == "hierarchy failure"


def test_large_snowflake_strings_are_not_truncated():
    raw = "9007199254740993"
    parsed = _parse_snowflake(raw)
    assert parsed == 9007199254740993
    assert parsed != int(float(raw))
    found: dict[str, set[int]] = {}
    _collect_resource_ids(
        {
            "allowed_role_ids": [str(BIG)],
            "blocked_role_ids": [],
            "allowed_channel_ids": [str(BIG + 1)],
            "blocked_channel_ids": ["200002"],
        },
        found,
    )
    assert BIG in found["role"]
    assert BIG + 1 in found["channel"]
    assert 200002 in found["channel"]


async def _grant_admin(api_client):
    from cls_platform.services.grants import create_grant, get_role_by_template

    role = await get_role_by_template("admin")
    await create_grant(TEST_GUILD_A, TEST_USER, role.id)


async def test_verification_enable_is_refused_without_a_published_message(api_client):
    client, _app = api_client
    await _grant_admin(api_client)
    headers = await auth_headers(TEST_USER)
    response = await client.patch(
        f"/api/v1/guilds/{TEST_GUILD_A}/verification",
        headers=headers,
        json={"enabled": True, "unverified_role_id": str(TEST_ROLE_A), "protected_category_ids": [str(TEST_CHANNEL_A)]},
    )
    assert response.status_code == 409
    assert response.json()["detail"] == VERIFICATION_ENABLE_BLOCK
    current = await client.get(f"/api/v1/guilds/{TEST_GUILD_A}/verification", headers=headers)
    assert current.status_code == 200
    assert current.json()["enabled"] is False
    assert current.json()["can_enable"] is False


async def test_vanity_save_is_refused_and_does_not_write(api_client):
    client, _app = api_client
    await _grant_admin(api_client)
    headers = await auth_headers(TEST_USER)
    response = await client.post(
        f"/api/v1/guilds/{TEST_GUILD_A}/vanityroles",
        headers=headers,
        json={"vanity": "cls", "role_id": str(TEST_ROLE_A), "log_channel_id": str(TEST_CHANNEL_A)},
    )
    assert response.status_code == 409
    assert response.json()["detail"] == VANITY_UNAVAILABLE


async def test_commands_reject_foreign_guild_resources_and_keep_large_ids(api_client):
    from cls_platform.commands.policy import policies_for
    from tests.fixtures.fake_bot import FakeRole

    client, app = api_client
    await _grant_admin(api_client)
    headers = await auth_headers(TEST_USER)
    guild = app.state.bot.get_guild(TEST_GUILD_A)
    guild.roles.append(FakeRole(id=BIG))

    foreign_role = await client.put(
        f"/api/v1/guilds/{TEST_GUILD_A}/commands",
        headers=headers,
        json={"command_name": "ping", "enabled": True, "allowed_role_ids": [str(TEST_ROLE_B)]},
    )
    assert foreign_role.status_code == 403
    assert "role" in foreign_role.json()["detail"].lower()

    foreign_channel = await client.put(
        f"/api/v1/guilds/{TEST_GUILD_A}/commands",
        headers=headers,
        json={"command_name": "ping", "enabled": True, "blocked_channel_ids": ["200002"]},
    )
    assert foreign_channel.status_code == 403
    assert "channel" in foreign_channel.json()["detail"].lower()
    assert "ping" not in await policies_for(TEST_GUILD_A)

    saved = await client.put(
        f"/api/v1/guilds/{TEST_GUILD_A}/commands",
        headers=headers,
        json={
            "command_name": "ping",
            "enabled": True,
            "allowed_role_ids": [str(BIG)],
            "allowed_channel_ids": [str(TEST_CHANNEL_A)],
        },
    )
    assert saved.status_code == 200
    body = saved.json()
    assert body["allowed_role_ids"] == [str(BIG)]
    assert body["allowed_channel_ids"] == [str(TEST_CHANNEL_A)]
    stored = await policies_for(TEST_GUILD_A)
    assert stored["ping"]["allowed_role_ids"] == [str(BIG)]


def test_loader_still_registers_allowlist_cog():
    from cogs.cog_loader import _cog_specs

    match = [spec for spec in _cog_specs() if spec.module == "cogs.events.on_guild"]
    assert match and match[0].class_name == "Guild"
