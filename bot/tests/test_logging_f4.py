"""Logging V2 completion: pages, attribution, diffs, coverage, and isolation."""

from cls_platform.logging.attribution import classify_matches
from cls_platform.logging.permissions import overwrite_diff
from cls_platform.logging.pipeline import NOISY_DEFAULT_OFF, event_ignored
from cls_platform.logging.present import present
from cls_platform.logging.source import note_source, read_source
from cls_platform.logging.store import delivery_target, list_events, record_event, set_appearance, set_event_route, set_ignores, set_route

GUILD = 100000000000000110
OTHER = 100000000000000210
ACTOR = 100000000000000311
TARGET = 100000000000000312


class _User:
    def __init__(self, user_id):
        self.id = user_id


def test_attribution_never_guesses_a_tie():
    one = classify_matches([(_User(1), "spam")])
    assert one[1] == "certain" and one[0].id == 1
    same = classify_matches([(_User(1), "a"), (_User(1), "b")])
    assert same[1] == "probable" and same[0].id == 1
    tie = classify_matches([(_User(1), "a"), (_User(2), "b")])
    assert tie[0] is None and tie[1] == "unknown" and tie[3] == "ambiguous"
    assert classify_matches([])[1] == "unknown"


def test_source_module_is_explicit():
    note_source(guild_id=GUILD, target_id=TARGET, module="Role Automation")
    assert read_source(guild_id=GUILD, target_id=TARGET) == "Role Automation"
    assert read_source(guild_id=GUILD, target_id=ACTOR) is None


def test_channel_permission_diff_is_a_sentence():
    send = 1 << 11
    manage = 1 << 13
    lines = overwrite_diff(
        [{"id": "9", "name": "Moderator", "kind": "role", "allow": send, "deny": 0}],
        [{"id": "9", "name": "Moderator", "kind": "role", "allow": 0, "deny": send}],
    )
    assert any(line["dashboard"] == "Send Messages: Allow → Deny" for line in lines)
    assert all("8192" not in line["dashboard"] for line in lines)
    assert manage


def test_role_and_security_sentences():
    roles = present(
        {
            "category": "role_events",
            "event_type": "member_roles",
            "actor_id": str(ACTOR),
            "target_id": str(TARGET),
            "actor_confidence": "certain",
            "before": {"roles": []},
            "after": {"roles": [{"id": "9", "name": "R7 Extra"}]},
            "metadata": {
                "entities": {
                    "actor": {"id": str(ACTOR), "display_name": "CLS SYSTEM"},
                    "target": {"id": str(TARGET), "display_name": "+EVO+"},
                },
                "source_module": "Role Automation",
            },
        }
    )
    assert roles["summary"] == "+EVO+ received R7 Extra"
    assert roles["source_line"] == "CLS SYSTEM · Role Automation"
    assert roles["attribution"] == "CLS"
    unknown = present(
        {
            "category": "role_events",
            "event_type": "role_update",
            "actor_confidence": "unknown",
            "before": {"name": "VIP", "color": "#6025E2"},
            "after": {"name": "VIP Customer", "color": "#2ECC71"},
            "metadata": {"audit_unavailable": True, "entities": {"target": {"id": "1", "name": "VIP Customer"}}},
        }
    )
    assert "VIP → VIP Customer" in unknown["changes"][1]["value"] or any("VIP" in change["value"] for change in unknown["changes"])
    assert unknown["source_line"] == "Actor unknown · View Audit Log unavailable"
    security = present(
        {
            "category": "security",
            "event_type": "security.incident_created",
            "actor_confidence": "unknown",
            "metadata": {"sentence": "Role deletion", "source_module": "Security Center"},
        }
    )
    assert security["summary"] == "Role deletion"
    assert security["source_line"] == "CLS SYSTEM · Security Center"


async def test_pages_filters_routes_and_isolation(db_reset):
    for index in range(30):
        await record_event(
            guild_id=GUILD,
            category="role_events",
            event_type="role_update",
            actor_id=ACTOR,
            actor_confidence="certain" if index % 2 == 0 else "probable",
            target_id=TARGET,
            metadata={"note": f"row-{index}"},
        )
    await record_event(guild_id=OTHER, category="guild_events", event_type="guild_update", actor_confidence="unknown")
    first = await list_events(GUILD, page=1, page_size=25)
    assert len(first["events"]) == 25
    assert first["total"] == 30
    assert first["pages"] == 2
    assert first["page_size"] == 25
    second = await list_events(GUILD, page=2, page_size=25)
    assert len(second["events"]) == 5
    sized = await list_events(GUILD, page=1, page_size=100)
    assert len(sized["events"]) == 30
    probable = await list_events(GUILD, page=1, page_size=100, confidence="probable")
    assert probable["total"] == 15
    assert all(row["actor_id"] == str(ACTOR) for row in first["events"])
    assert (await list_events(OTHER, page=1, page_size=25))["total"] == 1
    noisy = await delivery_target(GUILD, "voice_events", "voice_self_mute")
    assert noisy["capture"] is False
    assert "voice_self_mute" in NOISY_DEFAULT_OFF
    await set_route(guild_id=GUILD, category="voice_events", enabled=True, channel_id=100000000000000401)
    enabled = await set_event_route(guild_id=GUILD, event_type="voice_self_mute", mode="inherit", channel_id=None)
    assert enabled["kept"] is True
    assert (await delivery_target(GUILD, "voice_events", "voice_self_mute"))["capture"] is True
    await set_ignores(guild_id=GUILD, channels=[], roles=[], users=[TARGET])
    await set_appearance(GUILD, {"ignore_scope": "all"})
    assert event_ignored(channel_id=None, actor_id=None, target_id=TARGET, ignores={"channels": [], "users": [TARGET], "roles": []})
    appearance = await set_appearance(
        GUILD,
        {"event_styles": {"role_update": {"use_default": False, "color": "#C4A15A", "title": "Role changed", "icon": "edit"}}},
    )
    assert appearance["event_styles"]["role_update"]["title"] == "Role changed"
    assert appearance["ignore_scope"] == "all"
