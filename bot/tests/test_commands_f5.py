"""F5 command catalog, module switches, and access checker."""

from __future__ import annotations

from cls_platform.commands.catalog import (
    MIGRATION_QUEUE,
    drift_report,
    filter_rows,
    guild_rows,
    invocation_kind,
    paginate,
    retire_unprofessional_aliases,
    visibility,
)
from cls_platform.commands.policy import (
    access_decision,
    decision,
    evaluate,
    module_is_enabled,
    policies_for,
    set_module_enabled,
    set_policy,
)
from tests.conftest import TEST_CHANNEL_A, TEST_GUILD_A, TEST_ROLE_A, TEST_ROLE_B, TEST_USER, auth_headers

GUILD = 100000000000000100
ROLE = 100000000000000401
CHANNEL = 1555268757436371007


class _Cog:
    def __init__(self, name: str):
        self.qualified_name = name


class PrefixCommand:
    def __init__(self, name: str, cog: str, help_text: str = "", aliases=None, parent=None):
        self.qualified_name = name
        self.name = name.split()[-1]
        self.cog = _Cog(cog)
        self.short_doc = help_text
        self.brief = ""
        self.aliases = list(aliases or [])
        self.parent = parent
        self.signature = ""
        self.default_member_permissions = None


class HybridCommand(PrefixCommand):
    pass


class _Bot:
    def __init__(self, commands):
        self._commands = commands

    def walk_commands(self):
        return list(self._commands)


def _sample_bot():
    ban = HybridCommand("ban", "Ban", "Bans a user from the Server", aliases=["fuckban"])
    ban_user = PrefixCommand("ban user", "Ban", "Bans one member", parent=ban)
    clear = PrefixCommand("clear", "Message", "Clears the messages")
    ping = HybridCommand("ping", "Extra", "Checks the bot's latencies.", aliases=["latency"])
    hidden = PrefixCommand("global", "Global", "Owner global ban")
    toy = PrefixCommand("slots", "Slots", "Spin the slots")
    blank = PrefixCommand("widget", "Extra", "")
    return _Bot([ban, ban_user, clear, ping, hidden, toy, blank])


def test_root_and_toys_stay_out_of_the_guild_catalog():
    bot = _sample_bot()
    rows = guild_rows(bot, {}, {})
    names = {row["name"] for row in rows}
    assert "global" not in names
    assert "slots" not in names
    assert "widget" not in names
    assert "ban" in names
    assert "fuckban" not in {alias for row in rows for alias in row["aliases"]}
    assert all(row["description"] and row["description"] != "No description" for row in rows)
    assert all(row["audience"] not in {"root", "internal"} for row in rows)


def test_search_filters_pagination_and_kinds():
    bot = _sample_bot()
    rows = guild_rows(bot, {}, {})
    assert [row["name"] for row in filter_rows(rows, query="/ban")] == ["ban", "ban user"]
    assert filter_rows(rows, module_id="utilities")[0]["name"] == "ping"
    assert filter_rows(rows, audience="member")[0]["audience"] == "member"
    assert filter_rows(rows, kind="prefix")[0]["command_type"] == "prefix"
    assert invocation_kind(HybridCommand("ping", "Extra", "Checks latency")) == "hybrid"
    page = paginate(rows, 1, 25)
    assert page["page_size"] == 25
    assert page["total"] == len(rows)
    assert all(isinstance(row["name"], str) for row in page["commands"])
    report = drift_report(bot)
    assert "widget" in report["missing_description"]
    assert "global" not in report["missing_description"]
    assert MIGRATION_QUEUE[0]["name"] == "clear"


def test_aliases_are_removed_from_the_live_command():
    ban = PrefixCommand("ban", "Ban", "Bans a user", aliases=["fuckban", "banish"])

    class Parent:
        def __init__(self):
            self.removed = []

        def remove_command(self, name):
            self.removed.append(name)

    parent = Parent()
    ban.parent = parent
    retire_unprofessional_aliases(_Bot([ban]))
    assert parent.removed == ["fuckban"]
    assert visibility(PrefixCommand("reload", "Owner", "Reloads cogs")) == "root"


async def test_module_toggle_denies_without_rewriting_command_policy(db_reset):
    await set_policy(
        guild_id=GUILD,
        command_name="ban",
        enabled=True,
        allowed_role_ids=[ROLE],
        blocked_role_ids=[],
        actor_id=None,
    )
    await set_module_enabled(guild_id=GUILD, module_id="moderation", enabled=False, actor_id=None)
    assert await module_is_enabled(GUILD, "moderation") is False
    assert await evaluate(GUILD, "ban", {ROLE}, module_id="moderation") is False
    reason = await decision(GUILD, "ban", {ROLE}, module_id="moderation")
    assert reason == "This module is turned off by a server admin."
    saved = await policies_for(GUILD)
    assert saved["ban"]["allowed_role_ids"] == [str(ROLE)]
    await set_module_enabled(guild_id=GUILD, module_id="moderation", enabled=True, actor_id=None)
    assert await evaluate(GUILD, "ban", {ROLE}, module_id="moderation") is True
    assert await evaluate(GUILD, "ban", set(), module_id="moderation") is False
    assert (await policies_for(GUILD))["ban"]["allowed_role_ids"] == [str(ROLE)]


async def test_access_checker_matches_runtime_decision(db_reset):
    await set_policy(
        guild_id=GUILD,
        command_name="kick",
        enabled=True,
        allowed_role_ids=[],
        blocked_role_ids=[ROLE],
        allowed_channel_ids=[CHANNEL],
        actor_id=None,
    )
    denied = await access_decision(GUILD, "kick", {ROLE}, CHANNEL, module_id="moderation")
    assert denied["allowed"] is False
    assert denied["code"] == "blocked_role"
    assert denied["message"] == await decision(GUILD, "kick", {ROLE}, CHANNEL, module_id="moderation")
    allowed = await access_decision(GUILD, "kick", set(), CHANNEL, module_id="moderation")
    assert allowed["allowed"] is True
    assert allowed["message"] == "Allowed"
    assert any(step["ok"] for step in allowed["steps"])


async def test_channel_precedence_and_messages(db_reset):
    other = CHANNEL + 1
    await set_policy(
        guild_id=GUILD,
        command_name="mute",
        enabled=False,
        allowed_role_ids=[],
        actor_id=None,
    )
    assert await decision(GUILD, "mute", set(), CHANNEL) == "Command disabled by server admin."
    await set_policy(
        guild_id=GUILD,
        command_name="mute",
        enabled=True,
        allowed_role_ids=[ROLE],
        blocked_channel_ids=[CHANNEL],
        actor_id=None,
    )
    assert await decision(GUILD, "mute", {ROLE}, CHANNEL) == "Not allowed in this channel."
    assert await decision(GUILD, "mute", set(), other) == "You do not have a role allowed to use this command."


async def _grant(api_client):
    from cls_platform.services.grants import create_grant, get_role_by_template

    role = await get_role_by_template("admin")
    await create_grant(TEST_GUILD_A, TEST_USER, role.id)


async def test_guild_api_hides_root_and_paginates(api_client):
    client, app = api_client
    bot = app.state.bot
    sample = _sample_bot()
    bot.walk_commands = sample.walk_commands
    await _grant(api_client)
    headers = await auth_headers(TEST_USER)
    listed = await client.get(f"/api/v1/guilds/{TEST_GUILD_A}/commands?q=global", headers=headers)
    assert listed.status_code == 200
    body = listed.json()
    assert body["commands"] == []
    assert body["page_size"] == 25
    assert "global" not in str(body["commands"])
    visible = await client.get(f"/api/v1/guilds/{TEST_GUILD_A}/commands?q=/ban", headers=headers)
    names = [row["name"] for row in visible.json()["commands"]]
    assert names == ["ban", "ban user"]
    assert all(isinstance(row["allowed_role_ids"], list) for row in visible.json()["commands"])
    hidden_put = await client.put(
        f"/api/v1/guilds/{TEST_GUILD_A}/commands",
        headers=headers,
        json={"command_name": "global", "enabled": False},
    )
    assert hidden_put.status_code == 422


async def test_bulk_reset_and_foreign_role_rejected(api_client):
    client, app = api_client
    bot = app.state.bot
    bot.walk_commands = _sample_bot().walk_commands
    await _grant(api_client)
    headers = await auth_headers(TEST_USER)
    saved = await client.put(
        f"/api/v1/guilds/{TEST_GUILD_A}/commands",
        headers=headers,
        json={"command_name": "ban", "enabled": False, "allowed_role_ids": [str(TEST_ROLE_A)]},
    )
    assert saved.status_code == 200
    assert saved.json()["allowed_role_ids"] == [str(TEST_ROLE_A)]
    foreign = await client.post(
        f"/api/v1/guilds/{TEST_GUILD_A}/commands/bulk",
        headers=headers,
        json={"action": "block_role", "command_names": ["ban"], "blocked_role_ids": [str(TEST_ROLE_B)]},
    )
    assert foreign.status_code == 403
    reset = await client.post(
        f"/api/v1/guilds/{TEST_GUILD_A}/commands/bulk",
        headers=headers,
        json={"action": "reset", "command_names": ["ban"]},
    )
    assert reset.status_code == 200
    assert reset.json()["affected"] == 1
    again = await client.get(f"/api/v1/guilds/{TEST_GUILD_A}/commands?q=ban", headers=headers)
    ban = next(row for row in again.json()["commands"] if row["name"] == "ban")
    assert ban["enabled"] is True
    assert ban["allowed_role_ids"] == []
    module = await client.post(
        f"/api/v1/guilds/{TEST_GUILD_A}/commands/modules",
        headers=headers,
        json={"module_id": "moderation", "enabled": False},
    )
    assert module.status_code == 200
    access = await client.post(
        f"/api/v1/guilds/{TEST_GUILD_A}/commands/access",
        headers=headers,
        json={"command_name": "ban", "role_ids": [str(TEST_ROLE_A)], "channel_id": str(TEST_CHANNEL_A)},
    )
    assert access.status_code == 200
    assert access.json()["code"] == "module_disabled"
    await client.post(
        f"/api/v1/guilds/{TEST_GUILD_A}/commands/modules",
        headers=headers,
        json={"module_id": "moderation", "enabled": True},
    )


async def test_bulk_disable_keeps_role_limits(api_client):
    client, app = api_client
    bot = app.state.bot
    bot.walk_commands = _sample_bot().walk_commands
    await _grant(api_client)
    headers = await auth_headers(TEST_USER)
    await client.put(
        f"/api/v1/guilds/{TEST_GUILD_A}/commands",
        headers=headers,
        json={"command_name": "ping", "enabled": True, "allowed_role_ids": [str(TEST_ROLE_A)]},
    )
    disabled = await client.post(
        f"/api/v1/guilds/{TEST_GUILD_A}/commands/bulk",
        headers=headers,
        json={"action": "disable", "command_names": ["ping"]},
    )
    assert disabled.status_code == 200
    listed = await client.get(f"/api/v1/guilds/{TEST_GUILD_A}/commands?q=ping", headers=headers)
    ping = listed.json()["commands"][0]
    assert ping["enabled"] is False
    assert ping["allowed_role_ids"] == [str(TEST_ROLE_A)]
    enabled = await client.post(
        f"/api/v1/guilds/{TEST_GUILD_A}/commands/bulk",
        headers=headers,
        json={"action": "enable", "command_names": ["ping"]},
    )
    assert enabled.status_code == 200
