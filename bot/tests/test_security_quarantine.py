"""Quarantine outcomes and the production ENFORCE lock."""

from __future__ import annotations

import os

import pytest

from cls_platform.security.quarantine import apply_quarantine, release_quarantine
from cls_platform.security.response_protocol import EnforceUnavailable

GUILD = 100000000000000100
USER = 900000000000000111


class Role:
    def __init__(self, role_id, *, managed=False, position=1):
        self.id = role_id
        self.managed = managed
        self.position = position


class Member:
    def __init__(self, roles):
        self.roles = list(roles)
        self.removed = []
        self.added = []
        self.fail = None

    async def remove_roles(self, *roles, reason):
        if self.fail:
            raise self.fail
        self.removed.extend(roles)
        self.roles = [role for role in self.roles if role not in roles]
        assert reason.startswith("CLS-SEC ")

    async def add_roles(self, *roles, reason):
        self.added.extend(roles)
        assert reason.startswith("CLS-SEC ")


@pytest.fixture
def unlock(monkeypatch):
    monkeypatch.setenv("CLS_SECURITY_ENFORCE_UNLOCK", "1")
    yield
    os.environ.pop("CLS_SECURITY_ENFORCE_UNLOCK", None)


async def test_observe_skips_without_mutation(db_reset):
    member = Member([Role(11), Role(12)])
    result = await apply_quarantine(
        guild_id=GUILD,
        user_id=USER,
        member=member,
        bot_top_position=50,
        mode="OBSERVE",
        is_root=False,
        is_owner=False,
        owner_known=True,
        trusted=False,
    )
    assert result.outcome == "SKIPPED_MODE"
    assert member.removed == []


async def test_root_owner_trusted_and_unknown_are_not_contained(unlock, db_reset):
    member = Member([Role(11)])
    for kwargs, outcome in (
        ({"is_root": True, "is_owner": False, "owner_known": True, "trusted": False}, "NOT_ATTEMPTED_POLICY"),
        ({"is_root": False, "is_owner": True, "owner_known": True, "trusted": False}, "NOT_ATTEMPTED_POLICY"),
        ({"is_root": False, "is_owner": False, "owner_known": False, "trusted": False}, "NOT_ATTEMPTED_POLICY"),
        ({"is_root": False, "is_owner": False, "owner_known": True, "trusted": True}, "SKIPPED_TRUSTED"),
    ):
        result = await apply_quarantine(
            guild_id=GUILD, user_id=USER + 1, member=member, bot_top_position=50, mode="ENFORCE", **kwargs
        )
        assert result.outcome == outcome
        assert member.removed == []


async def test_removes_roles_and_is_idempotent(unlock, db_reset):
    member = Member([Role(11, position=1), Role(12, managed=True, position=2), Role(13, position=80)])
    result = await apply_quarantine(
        guild_id=GUILD,
        user_id=USER + 2,
        member=member,
        bot_top_position=50,
        mode="ENFORCE",
        is_root=False,
        is_owner=False,
        owner_known=True,
        trusted=False,
    )
    assert result.outcome == "PARTIAL_QUARANTINE"
    assert [role.id for role in member.removed] == [11]
    again = await apply_quarantine(
        guild_id=GUILD,
        user_id=USER + 2,
        member=member,
        bot_top_position=50,
        mode="ENFORCE",
        is_root=False,
        is_owner=False,
        owner_known=True,
        trusted=False,
    )
    assert again.outcome == "PARTIAL_QUARANTINE"
    assert len(member.removed) == 1


async def test_hierarchy_and_permission_failures(unlock, db_reset):
    high = Member([Role(21, position=90)])
    blocked = await apply_quarantine(
        guild_id=GUILD,
        user_id=USER + 3,
        member=high,
        bot_top_position=10,
        mode="ENFORCE",
        is_root=False,
        is_owner=False,
        owner_known=True,
        trusted=False,
    )
    assert blocked.outcome == "UNCONTAINABLE_HIERARCHY"
    denied = Member([Role(22, position=1)])
    denied.fail = PermissionError("no")
    failed = await apply_quarantine(
        guild_id=GUILD,
        user_id=USER + 4,
        member=denied,
        bot_top_position=50,
        mode="ENFORCE",
        is_root=False,
        is_owner=False,
        owner_known=True,
        trusted=False,
    )
    assert failed.outcome == "FAILED_PERMISSION"


async def test_release_is_root_only(unlock, db_reset):
    member = Member([Role(31, position=1)])
    await apply_quarantine(
        guild_id=GUILD,
        user_id=USER + 5,
        member=member,
        bot_top_position=50,
        mode="ENFORCE",
        is_root=False,
        is_owner=False,
        owner_known=True,
        trusted=False,
    )
    with pytest.raises(EnforceUnavailable):
        await release_quarantine(guild_id=GUILD, user_id=USER + 5, member=member, actor_is_root=False)
    released = await release_quarantine(guild_id=GUILD, user_id=USER + 5, member=member, actor_is_root=True)
    assert released.outcome == "RELEASED"
    assert member.added
