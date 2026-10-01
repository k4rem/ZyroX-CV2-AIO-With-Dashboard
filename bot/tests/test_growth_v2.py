"""Invite attribution stays honest and giveaways survive as stored rows."""

import random
from datetime import datetime, timedelta, timezone

from cls_platform.growth import attribute, create_giveaway, end_giveaway, enter_giveaway, invite_history, note_join, reroll_giveaway

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
