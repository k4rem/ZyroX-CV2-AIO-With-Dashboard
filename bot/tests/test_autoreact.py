"""Auto react matches literal text inside the chosen channels."""

from cls_platform.autoreact import channel_matches, create_rule, matching_rules, text_matches, update_rule

GUILD = 100000000000000100
CHANNEL = 100000000000000401


def test_match_modes_and_channel_scope():
    assert text_matches("contains", "hello r10", "say Hello R10 please")
    assert text_matches("exact", "hello r10", "hello r10")
    assert not text_matches("exact", "hello r10", "hello r10 now")
    assert text_matches("starts", "hello", "hello r10")
    assert text_matches("ends", "r10", "hello r10")
    assert channel_matches("selected", [CHANNEL], CHANNEL)
    assert not channel_matches("selected", [CHANNEL], CHANNEL + 1)
    assert not channel_matches("excluded", [CHANNEL], CHANNEL)
    assert channel_matches("all", [], CHANNEL + 1)


async def test_saved_rule_matches_only_its_channel(db_reset):
    created = await create_rule(
        GUILD,
        {
            "name": "R10 Hello",
            "enabled": True,
            "scope": "selected",
            "channel_ids": [str(CHANNEL)],
            "mode": "contains",
            "pattern": "hello r10",
            "emojis": ["✅", "💜"],
        },
    )
    here = await matching_rules(GUILD, "hello r10", CHANNEL)
    elsewhere = await matching_rules(GUILD, "hello r10", CHANNEL + 1)
    assert [row["name"] for row in here] == ["R10 Hello"]
    assert elsewhere == []
    await update_rule(GUILD, created["id"], {**created, "enabled": False})
    assert await matching_rules(GUILD, "hello r10", CHANNEL) == []
