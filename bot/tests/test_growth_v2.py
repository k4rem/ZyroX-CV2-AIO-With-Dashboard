"""Invite attribution stays honest and giveaways survive as stored rows."""

import random
from datetime import datetime, timedelta, timezone

from cls_platform.growth import (
    attribute,
    create_giveaway,
    end_giveaway,
    enter_giveaway,
    entry_block,
    invite_history,
    leave_giveaway,
    message_body,
    note_join,
    reroll_giveaway,
    select_winners,
)

GUILD = 100000000000000100
USER = 100000000000000301


def test_attribute_is_honest():
    assert attribute({"a": 1}, {"a": 2}) == ("certain", "a")
    assert attribute({"a": 1, "b": 1}, {"a": 2, "b": 2})[0] == "ambiguous"
    assert attribute({"a": 1}, {"a": 1}) == ("unknown", None)


async def test_history_and_giveaway(db_reset):
    await note_join(GUILD, USER, {"a": 1}, {"a": 2})
    history = await invite_history(GUILD)
    assert history[0]["status"] == "certain"
    assert history[0]["user_id"] == str(USER)
    assert await invite_history(100000000000000200) == []
    created = await create_giveaway(
        guild_id=GUILD,
        channel_id=100000000000000401,
        prize="sticker",
        ends_at=datetime.now(timezone.utc) + timedelta(hours=1),
    )
    await enter_giveaway(GUILD, created["id"], USER)
    await enter_giveaway(GUILD, created["id"], USER + 1)
    ended = await end_giveaway(GUILD, created["id"], rng=random.Random(1))
    assert ended["status"] == "ended"
    assert len(ended["winner_ids"]) == 1
    again = await reroll_giveaway(GUILD, created["id"], rng=random.Random(2))
    assert len(again["winner_ids"]) == 2
    assert again["winner_ids"][0] != again["winner_ids"][1]
    assert await enter_giveaway(GUILD, created["id"], USER) == "closed"


def test_winner_draw_is_unique_and_eligible():
    rng = random.Random(3)
    entries = [1, 1, 2, 3, 4]
    first = select_winners(entries, [], 2, {1, 2, 3}, rng)
    assert len(first) == 2
    assert len(set(first)) == 2
    assert 4 not in first
    reroll = select_winners(entries, first, 1, {1, 2, 3}, rng)
    assert reroll
    assert reroll[0] not in first


def test_entry_rules_and_message_time():
    assert entry_block({1}, required=2, blocked=None, is_bot=False)
    assert entry_block({9}, required=None, blocked=9, is_bot=False)
    assert entry_block(set(), required=None, blocked=None, is_bot=True)
    assert entry_block({2}, required=2, blocked=None, is_bot=False) is None
    body = message_body(
        prize="R10 Test Prize",
        description="A short test",
        winner_count=1,
        ends_at=datetime(2026, 10, 2, tzinfo=timezone.utc),
        host_id=5,
        entry_count=2,
        status="open",
        winner_ids=[],
    )
    assert "R10 Test Prize" in body
    assert "<t:" in body
    assert "Host: <@5>" in body


async def test_duplicate_entry_and_leave(db_reset):
    created = await create_giveaway(
        guild_id=GUILD,
        channel_id=100000000000000401,
        prize="R10 Test Prize",
        ends_at=datetime.now(timezone.utc) + timedelta(minutes=10),
        winner_count=1,
    )
    assert await enter_giveaway(GUILD, created["id"], USER) == "entered"
    assert await enter_giveaway(GUILD, created["id"], USER) == "duplicate"
    assert await leave_giveaway(GUILD, created["id"], USER) == "left"
    assert await leave_giveaway(GUILD, created["id"], USER) == "absent"
