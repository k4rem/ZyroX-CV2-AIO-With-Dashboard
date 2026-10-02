"""Verification V2 decisions, persistence, and category denies."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from cls_platform.verification.engine import plan_member, validate_enable, verification_message_reachable
from cls_platform.verification.gate import apply_category_denies, restore_category_denies
from cls_platform.verification.store import get_config, observe_member, save_config

GUILD = 100000000000000100
OTHER = 100000000000000200
BIG = 9007199254740993
NOW = datetime(2026, 10, 1, 12, tzinfo=timezone.utc)
ROOT = {900000000000000001}


class Bits:
    def __init__(self, value):
        self.value = value


class Overwrite:
    def __init__(self):
        self.allow = Bits(8)
        self.deny = Bits(0)

    def pair(self):
        return self.allow, self.deny

    def __iter__(self):
        return iter([("send_messages", True)])


class Role:
    def __init__(self, role_id):
        self.id = role_id


class Category:
    def __init__(self, cid, overwrite=None):
        self.id = cid
        self.overwrites = {Role(1): overwrite} if overwrite else {}
        self.writes = []

    async def set_permissions(self, role, reason=None, overwrite=None, **kwargs):
        self.writes.append({"role": role.id, "reason": reason, "overwrite": overwrite, "kwargs": kwargs})


def test_owner_and_root_are_exempt_and_verified_is_not_an_allow():
    assert plan_member(
        enabled=True, user_id=1, owner_id=1, root_ids=ROOT, joined_at=NOW, enabled_at=NOW,
        state=None, grace_until=None, grace_seconds=10, now=NOW,
    ) == "exempt"
    assert plan_member(
        enabled=True, user_id=900000000000000001, owner_id=2, root_ids=ROOT, joined_at=NOW,
        enabled_at=NOW, state=None, grace_until=None, grace_seconds=10, now=NOW,
    ) == "exempt"
    assert validate_enable(unverified_role_id=None, category_ids=[1], bot_top=5, role_position=1) == "role_missing"
    assert validate_enable(unverified_role_id=3, category_ids=[], bot_top=5, role_position=1) == "category_missing"
    assert validate_enable(unverified_role_id=3, category_ids=[1], bot_top=1, role_position=1) == "hierarchy"
    assert validate_enable(unverified_role_id=3, category_ids=[1], bot_top=5, role_position=1) == "message_unpublished"
    assert validate_enable(
        unverified_role_id=3, category_ids=[1], bot_top=5, role_position=1, message_published=True,
    ) == "ok"
    assert verification_message_reachable(published_message_id=None, channel_id=99) is False
    assert verification_message_reachable(published_message_id=100, channel_id=99) is True


def test_new_existing_grace_and_verified_plans():
    assert plan_member(
        enabled=True, user_id=5, owner_id=1, root_ids=set(), joined_at=NOW, enabled_at=NOW - timedelta(days=1),
        state=None, grace_until=None, grace_seconds=60, now=NOW,
    ) == "assign_unverified"
    assert plan_member(
        enabled=True, user_id=5, owner_id=1, root_ids=set(), joined_at=NOW - timedelta(days=2),
        enabled_at=NOW - timedelta(days=1), state=None, grace_until=None, grace_seconds=60, now=NOW,
    ) == "start_grace"
    assert plan_member(
        enabled=True, user_id=5, owner_id=1, root_ids=set(), joined_at=NOW, enabled_at=NOW,
        state="grace", grace_until=NOW + timedelta(minutes=1), grace_seconds=60, now=NOW,
    ) == "grace"
    assert plan_member(
        enabled=True, user_id=5, owner_id=1, root_ids=set(), joined_at=NOW, enabled_at=NOW,
        state="grace", grace_until=NOW - timedelta(seconds=1), grace_seconds=60, now=NOW,
    ) == "assign_unverified"
    assert plan_member(
        enabled=True, user_id=5, owner_id=1, root_ids=set(), joined_at=NOW, enabled_at=NOW,
        state="verified", grace_until=None, grace_seconds=60, now=NOW,
    ) == "verified"
    assert plan_member(
        enabled=False, user_id=5, owner_id=1, root_ids=set(), joined_at=NOW, enabled_at=None,
        state=None, grace_until=None, grace_seconds=60, now=NOW,
    ) == "disabled"


async def test_deny_preserves_other_bits_and_restore():
    role = Role(11)
    previous = Overwrite()
    category = Category(22)
    category.overwrites = {role: previous}
    backups = await apply_category_denies([category], role, reason="gate")
    assert category.writes[0]["kwargs"]["view_channel"] is False
    assert category.writes[0]["kwargs"]["send_messages"] is True
    await restore_category_denies({22: category}, backups, role, reason="off")
    assert category.writes[1]["overwrite"][0] == "restore"
    missing = Category(23)
    backups = await apply_category_denies([missing], role, reason="gate")
    await restore_category_denies({23: missing}, backups, role, reason="off")
    assert missing.writes[1]["overwrite"] is None


async def test_persistence_grace_restart_isolation_and_snowflakes(db_reset):
    fresh = await get_config(GUILD)
    assert fresh["enabled"] is False
    assert fresh["can_enable"] is False
    with pytest.raises(ValueError):
        await save_config(guild_id=GUILD, actor_id=1, fields={"enabled": True}, gate_check="role_missing")
    with pytest.raises(ValueError, match="verification message"):
        await save_config(
            guild_id=GUILD,
            actor_id=1,
            fields={
                "enabled": True,
                "unverified_role_id": BIG,
                "channel_id": BIG + 5,
                "protected_category_ids": [BIG + 2],
            },
            gate_check="ok",
        )
    await save_config(
        guild_id=GUILD,
        actor_id=1,
        fields={
            "enabled": False,
            "unverified_role_id": BIG,
            "verified_role_id": BIG + 1,
            "protected_category_ids": [BIG + 2],
            "grace_seconds": 120,
            "message": "Verify to enter.",
            "method": "button",
        },
        gate_check="ok",
    )
    saved = await get_config(GUILD)
    assert saved["unverified_role_id"] == str(BIG)
    assert saved["enabled"] is False
    assert saved["stored_enabled"] is False
    blocked = await observe_member(
        guild_id=GUILD, user_id=BIG + 4, owner_id=9, root_ids=set(),
        joined_at=datetime.now(timezone.utc) + timedelta(minutes=1), now=NOW,
    )
    assert blocked == "disabled"
    assert await observe_member(
        guild_id=GUILD, user_id=9, owner_id=9, root_ids=ROOT, joined_at=NOW, now=NOW,
    ) == "exempt"
    other = await get_config(OTHER)
    assert other["enabled"] is False
    assert other["counts"]["unverified"] == 0
    disabled = await save_config(guild_id=GUILD, actor_id=1, fields={"enabled": False}, gate_check="ok")
    assert disabled["enabled"] is False
