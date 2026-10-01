"""Security Center analytics, trap decision, phishing, and dashboard lock."""

from datetime import datetime, timedelta, timezone

from cls_platform.security.center import (
    analytics,
    incident_timeline,
    note_signal,
    phishing_match,
    save_settings,
    trap_action,
)
from cls_platform.security.models import SecurityIncident
from cls_platform.database import session_scope

GUILD = 100000000000000100
USER = 100000000000000301


def test_trap_and_phishing_rules():
    assert phishing_match("get free-nitro here")
    assert not phishing_match("hello team")
    assert trap_action(author_is_bot=True, webhook=False, trusted=False, mode="ENFORCE", enforce_locked=True) == "record"
    assert trap_action(author_is_bot=True, webhook=False, trusted=False, mode="ENFORCE", enforce_locked=False) == "ban"
    assert trap_action(author_is_bot=True, webhook=True, trusted=False, mode="ENFORCE", enforce_locked=False) == "record_webhook"
    assert trap_action(author_is_bot=True, webhook=False, trusted=True, mode="ENFORCE", enforce_locked=False) == "ignore"


async def test_center_analytics_and_timeline(db_reset):
    empty = await analytics(GUILD)
    assert empty["total"] == 0
    assert empty["heatmap"] is None
    assert empty["series"] == []
    old = datetime.now(timezone.utc) - timedelta(days=8)
    async with session_scope() as session:
        session.add(
            SecurityIncident(
                guild_id=GUILD,
                engine="human",
                status="CLOSED",
                severity="H",
                opened_at=old,
                last_activity_at=old,
                tier_map_version="v1",
            )
        )
    incident_id = await note_signal(guild_id=GUILD, subject_id=USER, engine="bot", kind="bot_trap", detail="record")
    summary = await analytics(GUILD)
    assert summary["total"] == 2
    assert summary["by_severity"]["H"] == 2
    assert summary["by_engine"]["human"] == 1
    assert summary["by_engine"]["bot"] == 1
    assert summary["heatmap"] is not None
    timeline = await incident_timeline(GUILD, incident_id)
    assert timeline["events"][0]["kind"] == "bot_trap"
    saved = await save_settings(guild_id=GUILD, dashboard_locked=True, phishing_action="delete_only", trap_channel_ids=[100000000000000401])
    assert saved["dashboard_locked"] is True
    assert saved["trap_channel_ids"] == ["100000000000000401"]
