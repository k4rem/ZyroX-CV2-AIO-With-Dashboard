"""Phase 2A.1 foundation: schema safety, RBAC, scheduler, allowlist, snowflakes."""

from __future__ import annotations

import ast
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from tests.conftest import TEST_GUILD_A, TEST_GUILD_B, TEST_ROOT

ABOVE_JS_SAFE = 100000000000000100  # 18 digits, greater than 2^53


def test_snowflake_above_js_safe_integer_stays_exact():
    from cls_platform.discord_types import snowflake_to_str

    assert ABOVE_JS_SAFE > 2**53
    assert int(float(ABOVE_JS_SAFE)) != ABOVE_JS_SAFE
    as_str = snowflake_to_str(ABOVE_JS_SAFE)
    assert as_str == str(ABOVE_JS_SAFE)
    payload = json.loads(json.dumps({"guild_id": as_str, "actor_id": as_str}))
    assert payload["guild_id"] == str(ABOVE_JS_SAFE)
    assert int(payload["actor_id"]) == ABOVE_JS_SAFE
    huge = 2**53 + 7
    assert str(huge) == "9007199254740999"
    assert int(str(huge)) == huge
    assert int(float(huge)) != huge


def test_permission_tiers_keep_audit_log_observability_only():
    from cls_platform.health.permissions import MODULE_REQUIRED
    from cls_platform.security.tiers import (
        is_containment_signal_tier,
        is_observability_permission,
        tier_for_permission,
        tier_of_added_bits,
    )

    assert "view_audit_log" in MODULE_REQUIRED["Antinuke"]
    assert tier_for_permission("view_audit_log") == "OBSERVABILITY"
    assert is_observability_permission("view_audit_log") is True
    assert is_containment_signal_tier("OBSERVABILITY") is False
    assert is_containment_signal_tier("ELEVATED") is False
    assert is_containment_signal_tier(tier_of_added_bits(["view_audit_log"])) is False
    assert tier_of_added_bits(["administrator", "view_audit_log"]) == "CRITICAL_CONTROL"
    assert tier_of_added_bits([]) is None


def test_optional_actions_stay_inactive():
    from cls_platform.security.taxonomy import action_spec, active_action_classes

    assert "channel.delete" in active_action_classes()
    assert action_spec("member.kick").gateway_visible is False
    assert action_spec("channel.overwrite_escalation").active is False
    assert action_spec("mention.spam").phase_status == "out_of_scope"
    assert "channel.create" not in active_action_classes()


def test_root_capabilities_are_not_on_admin_template():
    from cls_platform.capabilities import ADMIN_CAPS, MODERATOR_CAPS, ROOT_ONLY

    for cap in (
        "security.enforce.manage",
        "security.trust.manage",
        "security.quarantine.release",
        "security.maintenance.manage",
    ):
        assert cap in ROOT_ONLY
        assert cap not in ADMIN_CAPS
        assert cap not in MODERATOR_CAPS
    assert "security.incidents.manage" in ADMIN_CAPS
    assert "security.incidents.manage" not in MODERATOR_CAPS
    assert "security.incidents.manage" not in ROOT_ONLY


@pytest.mark.asyncio
async def test_non_root_cannot_hold_root_security_capabilities():
    from cls_platform.services.grants import user_has_capability

    assert await user_has_capability(TEST_GUILD_A, 800000000000000099, "security.trust.manage") is False
    assert await user_has_capability(TEST_GUILD_A, 800000000000000099, "security.enforce.manage") is False


@pytest.mark.asyncio
async def test_root_holds_security_capabilities(db_reset):
    from cls_platform.services.grants import user_has_capability

    assert await user_has_capability(TEST_GUILD_A, TEST_ROOT, "security.trust.manage") is True
    assert await user_has_capability(TEST_GUILD_A, TEST_ROOT, "security.maintenance.manage") is True


def test_enforce_is_not_operational():
    from cls_platform.security.config import assert_mode_writable, effective_mode
    from cls_platform.security.constants import ENFORCE_OPERATIONALLY_AVAILABLE
    from cls_platform.security.response_protocol import EnforceUnavailable, execute_discord_containment

    assert ENFORCE_OPERATIONALLY_AVAILABLE is False
    assert effective_mode("ENFORCE") == "OBSERVE"
    assert effective_mode("OFF") == "OFF"
    assert effective_mode("OBSERVE") == "OBSERVE"
    with pytest.raises(EnforceUnavailable):
        assert_mode_writable("ENFORCE")
    with pytest.raises(EnforceUnavailable):
        execute_discord_containment(guild_id=1, user_id=2)


def test_security_package_has_no_member_mutation():
    root = Path(__file__).resolve().parents[1] / "cls_platform" / "security"
    banned = ("remove_roles", "member.edit", ".ban(", ".kick(", ".timeout(", "edit_role")
    for path in root.rglob("*.py"):
        text = path.read_text(encoding="utf-8")
        ast.parse(text)
        for token in banned:
            assert token not in text, f"{path.name} contains {token}"


@pytest.mark.asyncio
async def test_sweep_keeps_product_and_ops_guilds():
    from cls_platform.security import allowlist_sweep as sweep

    class Guild:
        def __init__(self, gid: int):
            self.id = gid
            self.left = False

        async def leave(self):
            self.left = True

    product = Guild(TEST_GUILD_A)
    ops = Guild(100000000000000999)
    stranger = Guild(100000000000000777)

    class Bot:
        guilds = [product, ops, stranger]

    previous = (sweep.ALLOWLIST_ENFORCED, sweep.OPS_GUILD_ID, sweep.is_guild_allowed)
    sweep.ALLOWLIST_ENFORCED = True
    sweep.OPS_GUILD_ID = ops.id
    sweep.is_guild_allowed = lambda gid: gid == product.id
    try:
        left = await sweep.sweep_non_allowlisted_guilds(Bot())
    finally:
        sweep.ALLOWLIST_ENFORCED, sweep.OPS_GUILD_ID, sweep.is_guild_allowed = previous
    assert left == [stranger.id]
    assert product.left is False
    assert ops.left is False
    assert stranger.left is True


@pytest.mark.asyncio
async def test_sweep_does_nothing_when_allowlist_not_enforced():
    from cls_platform.security import allowlist_sweep as sweep

    class Guild:
        def __init__(self):
            self.id = 100000000000000777
            self.left = False

        async def leave(self):
            self.left = True

    guild = Guild()

    class Bot:
        guilds = [guild]

    previous = sweep.ALLOWLIST_ENFORCED
    sweep.ALLOWLIST_ENFORCED = False
    try:
        left = await sweep.sweep_non_allowlisted_guilds(Bot())
    finally:
        sweep.ALLOWLIST_ENFORCED = previous
    assert left == []
    assert guild.left is False


def test_ops_and_non_allowlisted_guilds_are_not_eligible(monkeypatch):
    from cls_platform.security import guild_gate

    monkeypatch.setattr(guild_gate, "OPS_GUILD_ID", 100000000000000999)
    monkeypatch.setattr(guild_gate, "is_guild_allowed", lambda gid: gid == TEST_GUILD_A)
    assert guild_gate.security_guild_eligible(TEST_GUILD_A) is True
    assert guild_gate.security_guild_eligible(100000000000000999) is False
    assert guild_gate.security_guild_eligible(100000000000000777) is False


@pytest.mark.asyncio
async def test_trust_is_root_only_and_does_not_import_legacy(db_reset):
    import inspect

    from cls_platform.security import trust
    from cls_platform.security.trust import TrustRejected, grant_trust

    source = inspect.getsource(trust)
    assert "anti.db" not in source
    assert "whitelisted_users" not in source
    assert "extraowners" not in source
    with pytest.raises(TrustRejected) as exc:
        await grant_trust(
            guild_id=TEST_GUILD_A,
            subject_id=800000000000000010,
            kind="human",
            scopes=["channel.delete"],
            actor_user_id=800000000000000099,
        )
    assert exc.value.status_code == 403
    with pytest.raises(TrustRejected) as bad:
        await grant_trust(
            guild_id=TEST_GUILD_A,
            subject_id=0,
            kind="human",
            scopes=[],
            actor_user_id=TEST_ROOT,
        )
    assert bad.value.status_code == 422


@pytest.mark.asyncio
async def test_enforce_mode_rejected_and_guilds_isolated(db_reset):
    from sqlalchemy import select, text

    from cls_platform.database import get_session_factory
    from cls_platform.security.config import ensure_guild_config, set_subsystem_mode
    from cls_platform.security.models import SecurityObservation
    from cls_platform.security.response_protocol import EnforceUnavailable

    row = await ensure_guild_config(TEST_GUILD_A)
    assert row.human_mode == "OBSERVE"
    with pytest.raises(EnforceUnavailable):
        await set_subsystem_mode(
            guild_id=TEST_GUILD_A, subsystem="human", mode="ENFORCE", expected_version=row.version
        )
    updated = await set_subsystem_mode(
        guild_id=TEST_GUILD_A, subsystem="human", mode="OFF", expected_version=row.version
    )
    assert updated.human_mode == "OFF"
    assert updated.version == row.version + 1

    now = datetime.now(timezone.utc)
    factory = get_session_factory()
    async with factory() as session:
        session.add(
            SecurityObservation(
                guild_id=TEST_GUILD_A,
                action_class="channel.delete",
                attribution_state="UNATTRIBUTED",
                late=False,
                received_at=now,
                source="gateway",
                severity="H",
                counts_for_containment=False,
            )
        )
        await session.commit()
        other = (
            await session.execute(
                select(SecurityObservation).where(SecurityObservation.guild_id == TEST_GUILD_B)
            )
        ).scalars().all()
        assert other == []
        with pytest.raises(Exception):
            await session.execute(
                text(
                    "INSERT INTO security_guild_configs (guild_id, human_mode, bot_mode) "
                    "VALUES (:gid, 'ENFORCE', 'OBSERVE')"
                ),
                {"gid": TEST_GUILD_B},
            )
            await session.commit()
        await session.rollback()


@pytest.mark.asyncio
async def test_schema_constraints_audit_unique_and_gateway_not_unique(db_reset):
    from sqlalchemy import text

    from cls_platform.database import get_session_factory

    now = datetime.now(timezone.utc)
    factory = get_session_factory()
    async with factory() as session:
        await session.execute(
            text(
                """
                INSERT INTO security_observations (
                  id, guild_id, audit_entry_id, action_class, attribution_state, late,
                  received_at, source, severity, counts_for_containment
                ) VALUES (
                  gen_random_uuid(), :gid, :audit, 'channel.delete', 'CONFIRMED', false,
                  :now, 'audit_push', 'H', true
                )
                """
            ),
            {"gid": TEST_GUILD_A, "audit": ABOVE_JS_SAFE, "now": now},
        )
        await session.commit()
        with pytest.raises(Exception):
            await session.execute(
                text(
                    """
                    INSERT INTO security_observations (
                      id, guild_id, audit_entry_id, action_class, attribution_state, late,
                      received_at, source, severity, counts_for_containment
                    ) VALUES (
                      gen_random_uuid(), :gid, :audit, 'channel.delete', 'CONFIRMED', false,
                      :now, 'audit_push', 'H', true
                    )
                    """
                ),
                {"gid": TEST_GUILD_A, "audit": ABOVE_JS_SAFE, "now": now},
            )
            await session.commit()
        await session.rollback()
        with pytest.raises(Exception):
            await session.execute(
                text(
                    """
                    INSERT INTO security_observations (
                      id, guild_id, audit_entry_id, action_class, attribution_state, late,
                      received_at, source, severity, counts_for_containment
                    ) VALUES (
                      gen_random_uuid(), :gid, 42, 'channel.delete', 'CONFIRMED', true,
                      :now, 'audit_push', 'H', true
                    )
                    """
                ),
                {"gid": TEST_GUILD_A, "now": now},
            )
            await session.commit()
        await session.rollback()
        await session.execute(
            text(
                """
                INSERT INTO security_gateway_signals (
                  id, guild_id, action_class, change_digest, correlation_key, state,
                  first_seen_at, last_seen_at
                ) VALUES
                  (gen_random_uuid(), :gid, 'channel.delete', 'd', 'k', 'PENDING', :now, :now),
                  (gen_random_uuid(), :gid, 'channel.delete', 'd', 'k', 'PENDING', :now, :now)
                """
            ),
            {"gid": TEST_GUILD_A, "now": now},
        )
        await session.commit()
        with pytest.raises(Exception):
            await session.execute(
                text(
                    """
                    INSERT INTO security_response_actions (
                      id, guild_id, idempotency_key, outcome, effective_mode, discord_mutation
                    ) VALUES (
                      gen_random_uuid(), :gid, 'mut', 'WOULD_CONTAIN', 'OBSERVE', true
                    )
                    """
                ),
                {"gid": TEST_GUILD_A},
            )
            await session.commit()
        await session.rollback()


@pytest.mark.asyncio
async def test_scheduler_backoff_reclaim_and_idempotent_enqueue(db_reset):
    from sqlalchemy import select, text

    from cls_platform.database import get_session_factory
    from cls_platform.models import SchedulerJob
    from cls_platform.services.scheduler import enqueue_job, register_job_handler, run_scheduler_tick

    calls = {"n": 0}

    async def boom(job):
        calls["n"] += 1
        raise RuntimeError("again")

    register_job_handler("backoff_job", boom)
    first = await enqueue_job("backoff_job", datetime.now(timezone.utc), {}, dedupe_key="same-key")
    second = await enqueue_job("backoff_job", datetime.now(timezone.utc), {}, dedupe_key="same-key")
    assert first == second
    assert await run_scheduler_tick() == 1
    assert await run_scheduler_tick() == 0
    factory = get_session_factory()
    async with factory() as session:
        row = (await session.execute(select(SchedulerJob).where(SchedulerJob.id == first))).scalar_one()
        assert row.status == "pending"
        assert row.run_at > datetime.now(timezone.utc)
        assert row.attempt_count == 1
        row.status = "running"
        row.lease_until = datetime.now(timezone.utc) - timedelta(seconds=5)
        await session.commit()
    assert await run_scheduler_tick() == 1
    async with factory() as session:
        row = (await session.execute(select(SchedulerJob).where(SchedulerJob.id == first))).scalar_one()
        assert row.attempt_count == 2
        row.status = "running"
        row.lease_until = datetime.now(timezone.utc) + timedelta(minutes=5)
        await session.commit()
        await session.execute(text("SELECT 1"))
    assert await run_scheduler_tick() == 0
