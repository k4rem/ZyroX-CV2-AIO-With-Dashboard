"""Disabled commands fail the runtime gate."""

import pytest

from cls_platform.commands.policy import PolicyError, evaluate, is_dangerous, set_policy

GUILD = 100000000000000100
ROLE = 100000000000000401


def test_dangerous_marker():
    assert is_dangerous("ban", "General")
    assert is_dangerous("fun", "Ban")
    assert not is_dangerous("ping", "General")


async def test_disabled_command_is_blocked(db_reset):
    assert await evaluate(GUILD, "ban", set()) is True
    await set_policy(guild_id=GUILD, command_name="ban", enabled=False, allowed_role_ids=[], actor_id=None)
    assert await evaluate(GUILD, "ban", set()) is False
    assert await evaluate(GUILD, "ban user", set()) is False
    await set_policy(guild_id=GUILD, command_name="kick", enabled=True, allowed_role_ids=[ROLE], actor_id=None)
    assert await evaluate(GUILD, "kick", set()) is False
    assert await evaluate(GUILD, "kick", {ROLE}) is True


async def test_channel_and_blocked_role_are_enforced(db_reset):
    channel = 1555268757436371007
    other = 1555268757436371008
    await set_policy(
        guild_id=GUILD,
        command_name="ping",
        enabled=True,
        allowed_role_ids=[],
        blocked_role_ids=[ROLE],
        allowed_channel_ids=[channel],
        blocked_channel_ids=[],
        actor_id=None,
    )
    assert await evaluate(GUILD, "ping", {ROLE}, channel) is False
    assert await evaluate(GUILD, "ping", set(), other) is False
    assert await evaluate(GUILD, "ping", set(), channel) is True
    await set_policy(
        guild_id=GUILD,
        command_name="ping",
        enabled=False,
        allowed_role_ids=[],
        actor_id=None,
    )
    assert await evaluate(GUILD, "ping", set(), channel) is False
    await set_policy(guild_id=GUILD, command_name="ping", enabled=True, allowed_role_ids=[], actor_id=None)
    assert await evaluate(GUILD, "ping", set(), channel) is True


async def test_recovery_commands_stay_available(db_reset):
    with pytest.raises(PolicyError):
        await set_policy(guild_id=GUILD, command_name="reload", enabled=False, allowed_role_ids=[], actor_id=None)
    assert await evaluate(GUILD, "reload", set(), 1) is True
