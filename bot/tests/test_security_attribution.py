"""Phase 2A.2 observation and attribution."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import func, select

from tests.conftest import TEST_GUILD_A, TEST_GUILD_B

ACTOR_A = 800000000000000011
ACTOR_B = 800000000000000012
TARGET = 800000000000000301
AUDIT_A = 900000000000000401
AUDIT_B = 900000000000000402


class Clock:
    def __init__(self) -> None:
        self.now = datetime(2026, 10, 1, 12, 0, tzinfo=timezone.utc)
        self.mono = 1000.0

    def __call__(self) -> datetime:
        return self.now

    async def sleep(self, seconds: float) -> None:
        self.now += timedelta(seconds=seconds)
        self.mono += seconds

    def monotonic(self) -> float:
        return self.mono


class Source:
    def __init__(self, pages) -> None:
        self.pages = list(pages)
        self.calls = []

    async def fetch(self, guild_id, discord_action, *, after_id, limit):
        from cls_platform.security.feed import FetchPage

        self.calls.append((guild_id, discord_action, after_id, limit))
        if self.pages:
            return self.pages.pop(0)
        return FetchPage(entries=[])


def _allow(monkeypatch) -> None:
    import cls_platform.security.feed as feed

    def eligible(guild_id: int) -> bool:
        return int(guild_id) in {TEST_GUILD_A, TEST_GUILD_B}

    monkeypatch.setattr(feed, "security_guild_eligible", eligible)


def _feed(monkeypatch, source=None, cls_user_id=None):
    from cls_platform.security.feed import ObservationFeed

    _allow(monkeypatch)
    clock = Clock()
    feed = ObservationFeed(
        source,
        clock=clock,
        sleep=clock.sleep,
        monotonic=clock.monotonic,
        cls_user_id=cls_user_id,
    )
    return feed, clock


def _entry(clock, **overrides):
    from cls_platform.security.attribution import AuditCandidate

    payload = dict(
        audit_entry_id=AUDIT_A,
        discord_action="channel_delete",
        action_class="channel.delete",
        target_id=TARGET,
        actor_id=ACTOR_A,
        entry_created_at=clock.now,
        change_digest="delete",
    )
    payload.update(overrides)
    return AuditCandidate(**payload)


async def _obs(guild_id=TEST_GUILD_A):
    from cls_platform.database import get_session_factory
    from cls_platform.security.models import SecurityObservation

    factory = get_session_factory()
    async with factory() as session:
        rows = (
            await session.execute(
                select(SecurityObservation).where(SecurityObservation.guild_id == guild_id)
            )
        ).scalars().all()
        return rows


async def _signals(guild_id=TEST_GUILD_A):
    from cls_platform.database import get_session_factory
    from cls_platform.security.models import SecurityGatewaySignal

    factory = get_session_factory()
    async with factory() as session:
        return (
            await session.execute(
                select(SecurityGatewaySignal).where(SecurityGatewaySignal.guild_id == guild_id)
            )
        ).scalars().all()


@pytest.mark.asyncio
async def test_push_only_confirmed(db_reset, monkeypatch):
    feed, clock = _feed(monkeypatch)
    obs_id = await feed.ingest_audit(_entry(clock), guild_id=TEST_GUILD_A, source="audit_push")
    rows = await _obs()
    assert len(rows) == 1
    assert rows[0].id == obs_id
    assert rows[0].attribution_state == "CONFIRMED"
    assert rows[0].counts_for_containment is True
    assert rows[0].late is False


@pytest.mark.asyncio
async def test_gateway_then_push_links_earliest(db_reset, monkeypatch):
    feed, clock = _feed(monkeypatch)
    first = await feed.record_gateway_signal(
        guild_id=TEST_GUILD_A,
        action_class="channel.delete",
        target_id=TARGET,
        change_digest="delete",
        discord_action="channel_delete",
        seen_at=clock.now,
        schedule=False,
    )
    clock.now += timedelta(seconds=1)
    second = await feed.record_gateway_signal(
        guild_id=TEST_GUILD_A,
        action_class="channel.delete",
        target_id=TARGET,
        change_digest="other",
        discord_action="channel_delete",
        seen_at=clock.now,
        schedule=False,
    )
    await feed.ingest_audit(_entry(clock), guild_id=TEST_GUILD_A, source="audit_push")
    signals = {row.id: row for row in await _signals()}
    assert signals[first].state == "LINKED"
    assert signals[second].state == "PENDING"
    obs = await _obs()
    assert obs[0].corroborated is True
    assert obs[0].attribution_state == "CONFIRMED"


@pytest.mark.asyncio
async def test_push_then_gateway_corroborates_without_a_second_observation(db_reset, monkeypatch):
    feed, clock = _feed(monkeypatch)
    await feed.ingest_audit(_entry(clock), guild_id=TEST_GUILD_A, source="audit_push")
    clock.now += timedelta(seconds=2)
    await feed.record_gateway_signal(
        guild_id=TEST_GUILD_A,
        action_class="channel.delete",
        target_id=TARGET,
        change_digest="delete",
        discord_action="channel_delete",
        seen_at=clock.now,
        schedule=False,
    )
    assert len(await _obs()) == 1
    signals = await _signals()
    assert signals[0].state == "LINKED"
    assert (await _obs())[0].corroborated is True


@pytest.mark.asyncio
async def test_duplicate_push_and_one_audit_id_one_observation(db_reset, monkeypatch):
    feed, clock = _feed(monkeypatch)
    first = await feed.ingest_audit(_entry(clock), guild_id=TEST_GUILD_A)
    second = await feed.ingest_audit(_entry(clock), guild_id=TEST_GUILD_A)
    assert first == second
    assert len(await _obs()) == 1
    other = await feed.ingest_audit(_entry(clock), guild_id=TEST_GUILD_B)
    assert other != first
    assert len(await _obs(TEST_GUILD_B)) == 1


@pytest.mark.asyncio
async def test_gateway_replay_merges_inside_window_and_not_outside(db_reset, monkeypatch):
    feed, clock = _feed(monkeypatch)
    await feed.record_gateway_signal(
        guild_id=TEST_GUILD_A,
        action_class="channel.delete",
        target_id=TARGET,
        change_digest="delete",
        discord_action="channel_delete",
        seen_at=clock.now,
        schedule=False,
    )
    clock.now += timedelta(seconds=3)
    await feed.record_gateway_signal(
        guild_id=TEST_GUILD_A,
        action_class="channel.delete",
        target_id=TARGET,
        change_digest="delete",
        discord_action="channel_delete",
        seen_at=clock.now,
        schedule=False,
    )
    merged = await _signals()
    assert len(merged) == 1
    assert merged[0].duplicate_count == 2
    clock.now += timedelta(seconds=11)
    await feed.record_gateway_signal(
        guild_id=TEST_GUILD_A,
        action_class="channel.delete",
        target_id=TARGET,
        change_digest="delete",
        discord_action="channel_delete",
        seen_at=clock.now,
        schedule=False,
    )
    assert len(await _signals()) == 2


@pytest.mark.asyncio
async def test_target_mismatch_and_stale_entry_do_not_link(db_reset, monkeypatch):
    feed, clock = _feed(monkeypatch)
    signal_at = clock.now
    await feed.record_gateway_signal(
        guild_id=TEST_GUILD_A,
        action_class="channel.delete",
        target_id=TARGET,
        change_digest="delete",
        discord_action="channel_delete",
        seen_at=signal_at,
        schedule=False,
    )
    await feed.ingest_audit(
        _entry(clock, target_id=TARGET + 5, audit_entry_id=AUDIT_B),
        guild_id=TEST_GUILD_A,
    )
    assert (await _signals())[0].state == "PENDING"
    stale_time = signal_at - timedelta(seconds=20)
    await feed.ingest_audit(
        _entry(clock, entry_created_at=stale_time, audit_entry_id=AUDIT_A, target_id=TARGET),
        guild_id=TEST_GUILD_A,
        received_at=clock.now,
    )
    signal = (await _signals())[0]
    assert signal.state == "PENDING"
    assert signal.linked_observation_id is None


@pytest.mark.asyncio
async def test_fallback_fetch_is_coalesced(db_reset, monkeypatch):
    from cls_platform.security.feed import FetchPage

    entry_time = datetime(2026, 10, 1, 12, 0, tzinfo=timezone.utc)
    page = FetchPage(entries=[])
    source = Source([FetchPage(entries=[]), FetchPage(entries=[]), page])
    feed, clock = _feed(monkeypatch, source)
    for offset in range(4):
        await feed.record_gateway_signal(
            guild_id=TEST_GUILD_A,
            action_class="channel.delete",
            target_id=TARGET + offset,
            change_digest=f"d{offset}",
            discord_action="channel_delete",
            seen_at=clock.now,
            schedule=False,
        )
    await feed.run_fallback(TEST_GUILD_A, "channel_delete")
    assert len(source.calls) == 3
    assert len({call[1] for call in source.calls}) == 1
    assert all(call[3] <= 25 for call in source.calls)
    assert all(row.state == "EXPIRED_UNATTRIBUTED" for row in await _signals())
    assert all(row.attribution_state == "UNATTRIBUTED" and row.actor_id is None for row in await _obs())


@pytest.mark.asyncio
async def test_fallback_attributes_matching_entry(db_reset, monkeypatch):
    from cls_platform.security.feed import FetchPage

    feed, clock = _feed(monkeypatch)
    await feed.record_gateway_signal(
        guild_id=TEST_GUILD_A,
        action_class="channel.delete",
        target_id=TARGET,
        change_digest="delete",
        discord_action="channel_delete",
        seen_at=clock.now,
        schedule=False,
    )
    source = Source([FetchPage(entries=[_entry(clock)])])
    feed.source = source
    await feed.run_fallback(TEST_GUILD_A, "channel_delete")
    assert source.calls
    signals = await _signals()
    assert signals[0].state == "LINKED"
    rows = await _obs()
    assert rows[0].attribution_state == "CONFIRMED"
    assert rows[0].source == "audit_fetch"


@pytest.mark.asyncio
async def test_two_candidates_and_no_candidate(db_reset, monkeypatch):
    feed, clock = _feed(monkeypatch)
    state = await feed.attribute_targetless(
        guild_id=TEST_GUILD_A,
        action_class="member.prune",
        candidates=[
            _entry(clock, action_class="member.prune", discord_action="member_prune", target_id=None, actor_id=ACTOR_A),
            _entry(
                clock,
                action_class="member.prune",
                discord_action="member_prune",
                target_id=None,
                actor_id=ACTOR_B,
                audit_entry_id=AUDIT_B,
            ),
        ],
        received_at=clock.now,
    )
    assert state.value == "AMBIGUOUS"
    rows = await _obs()
    assert rows[0].actor_id is None
    assert rows[0].audit_entry_id is None
    assert set(rows[0].candidate_actor_ids) == {ACTOR_A, ACTOR_B}
    assert rows[0].counts_for_containment is False
    empty = await feed.attribute_targetless(
        guild_id=TEST_GUILD_A,
        action_class="member.prune",
        candidates=[],
        received_at=clock.now,
    )
    assert empty.value == "UNATTRIBUTED"


@pytest.mark.asyncio
async def test_probable_single_targetless_candidate_never_counts(db_reset, monkeypatch):
    feed, clock = _feed(monkeypatch)
    state = await feed.attribute_targetless(
        guild_id=TEST_GUILD_A,
        action_class="member.prune",
        candidates=[
            _entry(clock, action_class="member.prune", discord_action="member_prune", target_id=None),
        ],
        received_at=clock.now,
    )
    assert state.value == "PROBABLE"
    row = (await _obs())[0]
    assert row.attribution_state == "PROBABLE"
    assert row.counts_for_containment is False


@pytest.mark.asyncio
async def test_late_reconciliation_and_resume(db_reset, monkeypatch):
    feed, clock = _feed(monkeypatch)
    entry = _entry(clock, entry_created_at=clock.now - timedelta(seconds=5))
    await feed.reconcile_new_session(resumed=True, entries=[(TEST_GUILD_A, entry)])
    assert await _obs() == []
    await feed.reconcile_new_session(resumed=False, entries=[(TEST_GUILD_A, entry)])
    row = (await _obs())[0]
    assert row.late is True
    assert row.source == "reconciliation"
    assert row.counts_for_containment is False
    late_push = await feed.ingest_audit(
        _entry(clock, audit_entry_id=AUDIT_B, entry_created_at=clock.now - timedelta(seconds=45)),
        guild_id=TEST_GUILD_A,
        received_at=clock.now,
        source="audit_push",
    )
    assert late_push is not None
    pushed = [item for item in await _obs() if item.audit_entry_id == AUDIT_B][0]
    assert pushed.late is True
    assert pushed.counts_for_containment is False


@pytest.mark.asyncio
async def test_forbidden_and_rate_limit(db_reset, monkeypatch):
    from cls_platform.security.feed import FetchPage
    from cls_platform.database import get_session_factory
    from cls_platform.security.models import SecurityAlertOutbox

    feed, clock = _feed(monkeypatch, Source([FetchPage(error="forbidden")]))
    await feed.record_gateway_signal(
        guild_id=TEST_GUILD_A,
        action_class="channel.delete",
        target_id=TARGET,
        change_digest="delete",
        discord_action="channel_delete",
        seen_at=clock.now,
        schedule=False,
    )
    await feed.run_fallback(TEST_GUILD_A, "channel_delete")
    assert (await _signals())[0].state == "EXPIRED_UNATTRIBUTED"
    factory = get_session_factory()
    async with factory() as session:
        alerts = (await session.execute(select(SecurityAlertOutbox))).scalars().all()
    assert len(alerts) == 1
    await feed.run_fallback(TEST_GUILD_A, "channel_delete")
    async with factory() as session:
        again = (await session.execute(select(func.count()).select_from(SecurityAlertOutbox))).scalar_one()
    assert again == 1

    feed2, clock2 = _feed(monkeypatch, None)
    limited = Source(
        [
            FetchPage(error="rate_limited", retry_after=4),
            FetchPage(
                entries=[
                    _entry(
                        clock2,
                        action_class="role.delete",
                        discord_action="role_delete",
                        audit_entry_id=AUDIT_B,
                    )
                ]
            ),
        ]
    )
    feed2.source = limited
    await feed2.record_gateway_signal(
        guild_id=TEST_GUILD_A,
        action_class="role.delete",
        target_id=TARGET,
        change_digest="delete",
        discord_action="role_delete",
        seen_at=clock2.now,
        schedule=False,
    )
    before = clock2.now
    await feed2.run_fallback(TEST_GUILD_A, "role_delete")
    assert clock2.now >= before + timedelta(seconds=4)
    assert len(limited.calls) == 2


@pytest.mark.asyncio
async def test_non_allowlisted_guild_is_dropped(db_reset, monkeypatch):
    feed, clock = _feed(monkeypatch)
    assert (
        await feed.record_gateway_signal(
            guild_id=100000000000000777,
            action_class="channel.delete",
            target_id=TARGET,
            change_digest="delete",
            discord_action="channel_delete",
            schedule=False,
        )
        is None
    )
    assert await feed.ingest_audit(_entry(clock), guild_id=100000000000000777) is None
    assert await _obs(TEST_GUILD_A) == []


def test_listener_does_not_mutate_members():
    from pathlib import Path

    text = Path(__file__).resolve().parents[1].joinpath("cogs", "security", "protection.py").read_text(encoding="utf-8")
    for token in ("remove_roles", "member.edit", ".kick(", ".ban(", ".timeout(", "edit_role"):
        assert token not in text


def test_windows_reject_stale_entries():
    from cls_platform.security.attribution import times_match

    signal = datetime(2026, 10, 1, tzinfo=timezone.utc)
    assert times_match(signal - timedelta(seconds=10), signal) is True
    assert times_match(signal - timedelta(seconds=20), signal) is False
