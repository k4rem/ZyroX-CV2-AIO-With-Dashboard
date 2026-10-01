"""Disabled commands fail the runtime gate."""

from cls_platform.commands.policy import evaluate, is_dangerous, set_policy

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
