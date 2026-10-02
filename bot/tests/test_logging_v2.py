"""Logging V2 store: isolation, redaction, filters, retention, empty analytics."""

from datetime import datetime, timedelta, timezone

from sqlalchemy import text

from cls_platform.database import session_scope
from cls_platform.logging.redact import redact
from cls_platform.logging.legacy import migrate_legacy_payload
from cls_platform.logging.store import (
    EVENT_RETENTION_DAYS,
    MESSAGE_RETENTION_DAYS,
    ignores,
    list_events,
    overview,
    purge_expired,
    record_event,
    remember_message,
    set_ignores,
    set_route,
    stored_message,
)

GUILD = 100000000000000100
OTHER = 100000000000000200
ACTOR = 100000000000000301
TARGET = 100000000000000302


def test_redact_secrets():
    cleaned = redact({"token": "abc", "note": "ok mfa." + ("a" * 24) + ".bbbbbb." + ("c" * 27)})
    assert cleaned["token"] == "[redacted]"
    assert "[redacted]" in cleaned["note"]
    assert "ok" in cleaned["note"]


async def test_events_filters_retention_and_empty(db_reset):
    async with session_scope() as session:
        names = (
            await session.execute(text("SELECT tablename FROM pg_tables WHERE tablename IN ('log_events','log_message_content','log_routes')"))
        ).scalars().all()
    assert set(names) == {"log_events", "log_message_content", "log_routes"}
    empty = await overview(OTHER)
    assert empty == {"total": 0, "by_category": {}, "top_types": [], "series": [], "heatmap": None}

    old = datetime.now(timezone.utc) - timedelta(days=8)
    saved = await record_event(
        guild_id=GUILD,
        category="member_moderation",
        event_type="member_ban",
        actor_id=ACTOR,
        actor_confidence="certain",
        target_id=TARGET,
        metadata={"token": "secret-value", "reason": "spam"},
        occurred_at=old,
    )
    assert saved["actor_id"] == str(ACTOR)
    assert saved["guild_id"] == str(GUILD)
    assert saved["metadata"]["token"] == "[redacted]"
    assert saved["metadata"]["reason"] == "spam"
    await record_event(
        guild_id=GUILD,
        category="join_leave_events",
        event_type="member_join",
        actor_id=ACTOR,
        actor_confidence="certain",
        target_id=ACTOR,
    )
    await record_event(guild_id=OTHER, category="guild_events", event_type="guild_update", actor_confidence="unknown")
    page = await list_events(GUILD, category="member_moderation", actor_id=ACTOR, target_id=TARGET)
    assert len(page["events"]) == 1
    assert page["events"][0]["id"] == saved["id"]
    isolated = await list_events(OTHER, category="member_moderation")
    assert isolated["events"] == []
    summary = await overview(GUILD)
    assert summary["total"] == 2
    assert summary["by_category"]["member_moderation"] == 1
    assert summary["heatmap"] is not None
    assert summary["series"]
    fresh = await overview(OTHER)
    assert fresh["heatmap"] is None
    assert fresh["total"] == 1

    route = await set_route(guild_id=GUILD, category="member_moderation", enabled=True, channel_id=100000000000000401)
    assert route["channel_id"] == "100000000000000401"
    await remember_message(
        guild_id=GUILD,
        message_id=100000000000000501,
        channel_id=100000000000000401,
        author_id=ACTOR,
        content="hello",
    )
    assert await stored_message(GUILD, 100000000000000501) == "hello"
    purged = await purge_expired(datetime.now(timezone.utc) + timedelta(days=120))
    assert purged["events"] >= 3
    assert await overview(GUILD) == {"total": 0, "by_category": {}, "top_types": [], "series": [], "heatmap": None}
    assert await stored_message(GUILD, 100000000000000501) is None


SNOW = 1543105121804615999


async def test_snapshots_search_ignores_and_legacy_migration(db_reset):
    assert EVENT_RETENTION_DAYS == 90
    assert MESSAGE_RETENTION_DAYS == 30
    saved = await record_event(
        guild_id=GUILD,
        category="role_events",
        event_type="member_roles",
        actor_id=SNOW,
        actor_confidence="certain",
        target_id=TARGET,
        before={"roles": []},
        after={"roles": [{"id": "9", "name": "VIP", "color": "#c4a15a"}]},
        metadata={"entities": {"actor": {"id": str(SNOW), "display_name": "Alice", "username": "alice"}, "target": {"id": str(TARGET), "display_name": "Ahmed"}}},
    )
    assert saved["actor_id"] == str(SNOW)
    assert saved["presentation"]["title"] == "Role added"
    assert "Ahmed received VIP" in saved["presentation"]["summary"]
    assert str(SNOW) not in saved["presentation"]["summary"]
    found = await list_events(GUILD, query="alice")
    assert [row["id"] for row in found["events"]] == [saved["id"]]
    by_member = await list_events(GUILD, member_id=SNOW)
    assert by_member["events"][0]["actor_id"] == str(SNOW)
    assert (await list_events(OTHER, query="alice"))["events"] == []
    saved_ignores = await set_ignores(guild_id=GUILD, channels=[100000000000000401], roles=[100000000000000404], users=[SNOW])
    assert saved_ignores["users"] == [str(SNOW)]
    assert SNOW in (await ignores(GUILD))["users"]
    assert (await ignores(OTHER)) == {"channels": [], "roles": [], "users": []}
    migrated = await migrate_legacy_payload(
        OTHER,
        {
            "log_enabled": {"message_events": True, "system_events": True, "emoji_events": True},
            "log_channels": {"message_events": 100000000000000401, "system_events": 100000000000000402},
            "ignore_channels": [100000000000000403],
            "ignore_users": [SNOW],
        },
    )
    assert migrated == "migrated"
    from cls_platform.logging.store import routes

    copied = {row["category"]: row for row in await routes(OTHER)}
    assert copied["message_events"]["enabled"] is True
    assert copied["message_events"]["channel_id"] == "100000000000000401"
    assert copied["guild_events"]["channel_id"] == "100000000000000402"
    assert copied["role_events"]["enabled"] is False
    assert SNOW in (await ignores(OTHER))["users"]
    assert await migrate_legacy_payload(OTHER, {"log_enabled": {"voice_events": True}, "log_channels": {"voice_events": 99}}) == "skipped"
    voice = {row["category"]: row for row in await routes(OTHER)}["voice_events"]
    assert voice["enabled"] is False
    from cls_platform.logging.store import appearance_for, delivery_target, event_routes, set_appearance, set_event_route

    await set_route(guild_id=GUILD, category="message_events", enabled=True, channel_id=100000000000000501)
    inherited = await delivery_target(GUILD, "message_events", "message_edit")
    assert inherited["mode"] == "inherit" and inherited["deliver"] is True
    assert inherited["channel_id"] == 100000000000000501
    custom = await set_event_route(guild_id=GUILD, event_type="message_delete", mode="custom", channel_id=100000000000000502)
    assert custom["channel_id"] == "100000000000000502"
    deleted = await delivery_target(GUILD, "message_events", "message_delete")
    assert deleted["mode"] == "custom" and deleted["channel_id"] == 100000000000000502
    await set_event_route(guild_id=GUILD, event_type="message_bulk_delete", mode="stored_only", channel_id=None)
    bulk = await delivery_target(GUILD, "message_events", "message_bulk_delete")
    assert bulk["capture"] is True and bulk["deliver"] is False
    await set_event_route(guild_id=GUILD, event_type="message_edit", mode="disabled", channel_id=None)
    assert (await delivery_target(GUILD, "message_events", "message_edit"))["capture"] is False
    assert (await delivery_target(OTHER, "message_events", "message_delete"))["mode"] == "inherit"
    assert all(row["event_type"] != "message_delete" for row in await event_routes(OTHER))
    saved_look = await set_appearance(GUILD, {"style": "compact", "show_ids": True, "colors": {"message_events": "#112233"}, "footer_mode": "custom", "footer_text": "Ops"})
    assert saved_look["style"] == "compact"
    assert saved_look["show_ids"] is True
    assert saved_look["colors"]["message_events"] == "#112233"
    assert (await appearance_for(OTHER))["style"] == "balanced"
    assert (await appearance_for(OTHER))["show_ids"] is False
    assert (await appearance_for(GUILD))["footer_text"] == "Ops"
