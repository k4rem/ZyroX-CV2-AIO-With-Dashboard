"""Join roles, automation rules, delays, and loop protection."""

import sqlite3
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

import pytest
from sqlalchemy import select

from cls_platform.database import session_scope
from cls_platform.models import SchedulerJob
from cls_platform.role_automation.logic import allow_fire, conditions_match, should_assign_now
from cls_platform.role_automation.store import (
    RuleError,
    create_rule,
    get_join,
    list_rules,
    migrate_legacy,
    rules_for,
    save_join,
    update_rule,
)
from cls_platform.role_menus.logic import role_block
from cogs.cog_loader import _cog_specs
from cogs.role_automation import RoleAutomation
from tests.conftest import TEST_GUILD_A, TEST_GUILD_B, TEST_ROOT, auth_headers

GUILD = 1543105121804615781
OTHER = 1543105121804615782
CUSTOMER = 9007199254740993
VERIFIED = 9007199254740994
ROLE_A = 9007199254740995
ROLE_B = 9007199254740996
ROLE_C = 9007199254740997
ROLE_D = 9007199254740998
MEMBER = 444859077823037440


def test_legacy_join_listener_is_unloaded():
    specs = {spec.class_name: spec for spec in _cog_specs()}
    assert specs["Autorole2"].skip is True
    assert specs["RoleAutomation"].skip is False


def test_conditions_screening_and_depth():
    roles = {CUSTOMER}
    assert conditions_match(is_bot=False, role_ids=roles, account_age_seconds=90000, conditions=[{"kind": "human"}])
    assert not conditions_match(is_bot=True, role_ids=roles, account_age_seconds=90000, conditions=[{"kind": "human"}])
    assert conditions_match(is_bot=True, role_ids=set(), account_age_seconds=10, conditions=[{"kind": "bot"}])
    assert conditions_match(is_bot=False, role_ids=roles, account_age_seconds=10, conditions=[{"kind": "has_role", "role_id": str(CUSTOMER)}])
    assert not conditions_match(is_bot=False, role_ids=roles, account_age_seconds=10, conditions=[{"kind": "lacks_role", "role_id": str(CUSTOMER)}])
    assert conditions_match(is_bot=False, role_ids=set(), account_age_seconds=3 * 86400, conditions=[{"kind": "account_age", "op": "gte", "amount": 2, "unit": "days"}])
    assert not conditions_match(is_bot=False, role_ids=set(), account_age_seconds=3600, conditions=[{"kind": "account_age", "op": "gt", "amount": 2, "unit": "hours"}])
    assert should_assign_now(pending=True, screening="immediate")
    assert not should_assign_now(pending=True, screening="screening")
    assert should_assign_now(pending=False, screening="screening")
    assert allow_fire(["a", "b", "c"], "d") == "Role automation stopped at 3 steps so it cannot loop."
    assert allow_fire(["a"], "a").startswith("This rule already ran")
    assert allow_fire(["a", "b"], "c") is None
    assert "managed" in role_block(exists=True, managed=True, bot_can_manage=True, below_bot=True)
    assert "above CLS" in role_block(exists=True, managed=False, bot_can_manage=True, below_bot=False)


async def test_join_roles_rules_and_legacy_migration(db_reset, tmp_path):
    saved = await save_join(guild_id=GUILD, member_role_ids=[str(CUSTOMER), "nope"], bot_role_ids=[str(VERIFIED)], delay_seconds_value=10, screening="screening")
    assert saved["member_role_ids"] == [str(CUSTOMER)]
    assert saved["bot_role_ids"] == [str(VERIFIED)]
    assert saved["guild_id"] == str(GUILD)
    rule = await create_rule(
        guild_id=GUILD,
        name="Customer to Verified",
        trigger="role_add",
        trigger_role_id=str(CUSTOMER),
        conditions=[{"kind": "human"}, {"kind": "has_role", "role_id": str(CUSTOMER)}],
        action="add",
        action_role_id=str(VERIFIED),
        delay_seconds_value=0,
    )
    assert rule["trigger_role_id"] == str(CUSTOMER)
    assert rule["action_role_id"] == str(VERIFIED)
    assert (await rules_for(GUILD, "role_add", CUSTOMER))[0]["id"] == rule["id"]
    assert await rules_for(OTHER, "role_add", CUSTOMER) == []
    disabled = await update_rule(guild_id=GUILD, rule_id=rule["id"], enabled=False)
    assert disabled["enabled"] is False
    assert await rules_for(GUILD, "role_add", CUSTOMER) == []
    path = tmp_path / "autorole.db"
    with sqlite3.connect(path) as conn:
        conn.execute("CREATE TABLE autorole (guild_id INTEGER PRIMARY KEY, bots TEXT, humans TEXT)")
        conn.execute("INSERT INTO autorole VALUES (?, ?, ?)", (OTHER, str([VERIFIED]), str([CUSTOMER])))
    before = path.read_bytes()
    assert await migrate_legacy(str(path)) == 1
    assert path.read_bytes() == before
    copied = await get_join(OTHER)
    assert copied["member_role_ids"] == [str(CUSTOMER)]
    assert copied["bot_role_ids"] == [str(VERIFIED)]
    assert await migrate_legacy(str(path)) == 0
    assert await list_rules(OTHER) == []
    with pytest.raises(RuleError):
        await create_rule(guild_id=GUILD, name="Bad", trigger="role_add", trigger_role_id=None, conditions=[], action="add", action_role_id=str(VERIFIED), delay_seconds_value=0)


def _guild():
    roles = {role_id: SimpleNamespace(id=role_id, name=str(role_id), position=1, managed=False) for role_id in (CUSTOMER, VERIFIED, ROLE_A, ROLE_B, ROLE_C, ROLE_D)}
    me = SimpleNamespace(guild_permissions=SimpleNamespace(manage_roles=True), top_role=SimpleNamespace(id=1, position=50))
    return SimpleNamespace(id=GUILD, me=me, get_role=lambda role_id: roles.get(int(role_id)), get_member=lambda member_id: None)


def _member(guild, *, bot=False, roles=None, pending=False, age_days=30):
    member = SimpleNamespace(
        id=MEMBER,
        guild=guild,
        bot=bot,
        pending=pending,
        display_name="AERO",
        created_at=datetime.now(timezone.utc) - timedelta(days=age_days),
        roles=list(roles or []),
        added=[],
        removed=[],
    )

    async def add_roles(*items, reason=None):
        before = SimpleNamespace(roles=list(member.roles), pending=member.pending, guild=guild)
        member.roles = [*member.roles, *items]
        member.added.extend(role.id for role in items)
        await cog_holder[0].on_member_update(before, member)

    async def remove_roles(*items, reason=None):
        before = SimpleNamespace(roles=list(member.roles), pending=member.pending, guild=guild)
        drop = {role.id for role in items}
        member.roles = [role for role in member.roles if role.id not in drop]
        member.removed.extend(role.id for role in items)
        await cog_holder[0].on_member_update(before, member)

    member.add_roles = add_roles
    member.remove_roles = remove_roles
    return member


cog_holder = [None]


async def test_runtime_assigns_guards_and_delays(db_reset):
    guild = _guild()
    bot = SimpleNamespace(get_guild=lambda guild_id: guild if guild_id == GUILD else None)
    cog = RoleAutomation(bot)
    cog_holder[0] = cog
    human = _member(guild)
    robot = _member(guild, bot=True)
    await save_join(guild_id=GUILD, member_role_ids=[str(CUSTOMER)], bot_role_ids=[str(VERIFIED)], delay_seconds_value=0, screening="immediate")
    cog.caused.clear()
    await cog.apply_join(human)
    cog.caused.clear()
    await cog.apply_join(robot)
    assert human.added == [CUSTOMER]
    assert robot.added == [VERIFIED]

    waiting = _member(guild, pending=True)
    await save_join(guild_id=GUILD, member_role_ids=[str(ROLE_A)], bot_role_ids=[], delay_seconds_value=0, screening="screening")
    cog.caused.clear()
    await cog.apply_join(waiting)
    assert waiting.added == []
    waiting.pending = False
    cog.caused.clear()
    await cog.on_member_update(SimpleNamespace(roles=list(waiting.roles), pending=True, guild=guild), waiting)
    assert ROLE_A in waiting.added

    gain = await create_rule(guild_id=GUILD, name="Customer to Verified", trigger="role_add", trigger_role_id=str(CUSTOMER), conditions=[{"kind": "human"}], action="add", action_role_id=str(VERIFIED), delay_seconds_value=0)
    loss = await create_rule(guild_id=GUILD, name="Drop verified", trigger="role_remove", trigger_role_id=str(CUSTOMER), conditions=[], action="remove", action_role_id=str(VERIFIED), delay_seconds_value=0)
    member = _member(guild)
    cog.caused.clear()
    await cog.dispatch(member, "role_add", CUSTOMER)
    assert VERIFIED in member.added
    member.roles.append(guild.get_role(CUSTOMER))
    cog.caused.clear()
    await cog.dispatch(member, "role_remove", CUSTOMER)
    assert VERIFIED in member.removed
    await update_rule(guild_id=GUILD, rule_id=gain["id"], enabled=False)
    quiet = _member(guild)
    cog.caused.clear()
    await cog.dispatch(quiet, "role_add", CUSTOMER)
    assert quiet.added == []
    await update_rule(guild_id=GUILD, rule_id=gain["id"], enabled=True)

    needs = await create_rule(guild_id=GUILD, name="Needs customer", trigger="join", trigger_role_id=None, conditions=[{"kind": "has_role", "role_id": str(CUSTOMER)}], action="add", action_role_id=str(ROLE_B), delay_seconds_value=0)
    lacking = await create_rule(guild_id=GUILD, name="Missing customer", trigger="join", trigger_role_id=None, conditions=[{"kind": "lacks_role", "role_id": str(CUSTOMER)}], action="add", action_role_id=str(ROLE_C), delay_seconds_value=0)
    aged = await create_rule(guild_id=GUILD, name="Old account", trigger="join", trigger_role_id=None, conditions=[{"kind": "account_age", "op": "gte", "amount": 7, "unit": "days"}], action="add", action_role_id=str(ROLE_D), delay_seconds_value=0)
    fresh = _member(guild, age_days=1)
    held = _member(guild, roles=[guild.get_role(CUSTOMER)], age_days=1)
    cog.caused.clear()
    await cog.dispatch(fresh, "join", None)
    cog.caused.clear()
    await cog.dispatch(held, "join", None)
    assert ROLE_C in fresh.added and ROLE_B not in fresh.added and ROLE_D not in fresh.added
    assert ROLE_B in held.added and ROLE_D not in held.added
    old = _member(guild, age_days=20)
    cog.caused.clear()
    await cog.dispatch(old, "join", None)
    assert ROLE_D in old.added

    delayed = await create_rule(guild_id=GUILD, name="Wait", trigger="role_add", trigger_role_id=str(ROLE_A), conditions=[{"kind": "human"}], action="add", action_role_id=str(ROLE_B), delay_seconds_value=10)
    later = _member(guild)
    cog.caused.clear()
    await cog.dispatch(later, "role_add", ROLE_A)
    assert later.added == []
    async with session_scope() as session:
        job = (await session.execute(select(SchedulerJob).where(SchedulerJob.dedupe_key == f"role-rule:{delayed['id']}:{MEMBER}"))).scalar_one()
        assert job.payload["rule_id"] == delayed["id"]
        assert job.payload["guild_id"] == GUILD
        assert job.status == "pending"
    guild.get_member = lambda member_id: later if int(member_id) == MEMBER else None
    await cog.handle_job(job)
    assert ROLE_B in later.added

    first = await create_rule(guild_id=GUILD, name="A to B", trigger="role_add", trigger_role_id=str(ROLE_A), conditions=[], action="add", action_role_id=str(ROLE_B), delay_seconds_value=0)
    second = await create_rule(guild_id=GUILD, name="B to C", trigger="role_add", trigger_role_id=str(ROLE_B), conditions=[], action="add", action_role_id=str(ROLE_C), delay_seconds_value=0)
    third = await create_rule(guild_id=GUILD, name="C to D", trigger="role_add", trigger_role_id=str(ROLE_C), conditions=[], action="add", action_role_id=str(ROLE_D), delay_seconds_value=0)
    fourth = await create_rule(guild_id=GUILD, name="D to customer", trigger="role_add", trigger_role_id=str(ROLE_D), conditions=[], action="add", action_role_id=str(CUSTOMER), delay_seconds_value=0)
    looped = _member(guild)
    cog.caused.clear()
    await cog.dispatch(looped, "role_add", ROLE_A)
    assert ROLE_B in looped.added and ROLE_C in looped.added and ROLE_D in looped.added
    assert CUSTOMER not in looped.added
    assert loss["id"]
    assert needs["id"] and lacking["id"] and aged["id"] and first["id"] and second["id"] and third["id"] and fourth["id"]


async def test_role_automation_api(api_client):
    client, _app = api_client
    headers = await auth_headers(TEST_ROOT)
    saved = await client.put(
        f"/api/v1/guilds/{TEST_GUILD_A}/autorole/v2/join",
        headers=headers,
        json={"member_role_ids": ["100001"], "bot_role_ids": [], "delay_seconds": 0, "screening": "immediate"},
    )
    assert saved.status_code == 200, saved.text
    assert saved.json()["member_role_ids"] == ["100001"]
    created = await client.post(
        f"/api/v1/guilds/{TEST_GUILD_A}/autorole/v2/rules",
        headers=headers,
        json={"name": "Customer to Verified", "trigger": "role_add", "trigger_role_id": "100001", "conditions": [{"kind": "human"}], "action": "add", "action_role_id": "100001", "delay_seconds": 0},
    )
    assert created.status_code == 200, created.text
    body = created.json()
    assert body["trigger_role_id"] == "100001"
    assert body["warnings"]
    listed = await client.get(f"/api/v1/guilds/{TEST_GUILD_B}/autorole/v2", headers=headers)
    assert listed.status_code == 200
    assert listed.json()["rules"] == []
    toggled = await client.patch(f"/api/v1/guilds/{TEST_GUILD_A}/autorole/v2/rules/{body['id']}", headers=headers, json={"enabled": False})
    assert toggled.json()["status"] == "Disabled"
