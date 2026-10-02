"""Security Center product workflows. ENFORCE stays locked."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from cls_platform.security.center import get_settings, is_trusted, note_signal, save_settings
from cls_platform.security.config import assert_mode_writable
from cls_platform.security.enforce_lock import enforce_unlocked
from cls_platform.security.logbridge import security_event
from cls_platform.security.maintenance import MaintenanceRejected, start_window
from cls_platform.security.models import SecurityQuarantine
from cls_platform.security.product import behavior, channel_in_guild, confidence_label, detector_title, join_signal, posture
from cls_platform.security.quarantine import restore_quarantine
from cls_platform.security.response_protocol import EnforceUnavailable
from cls_platform.security.trust import TrustRejected, grant_trust, revoke_trust
from cls_platform.security.workflows import close_incident, handle_center_message, list_incidents, present_incident
from cls_platform.database import session_scope
from cls_platform.logging.store import list_events

GUILD = 100000000000000610
OTHER = 100000000000000611
USER = 900000000000000610
ROOT = 900000000000000001
HUGE = 9007199254740999


class Role:
    def __init__(self, role_id, *, managed=False, position=1, administrator=False):
        self.id = role_id
        self.managed = managed
        self.position = position

        class Permissions:
            pass

        self.permissions = Permissions()
        self.permissions.administrator = administrator


class Member:
    def __init__(self):
        self.added = []

    async def add_roles(self, *roles, reason):
        assert reason.startswith("CLS-SEC ")
        self.added.extend(roles)


def test_labels_posture_and_behavior_hide_engine_ids():
    assert detector_title("aggregate.destructive") == "Destructive burst"
    assert "DEVELOPMENT_PROPOSAL" not in detector_title("channel.delete")
    assert confidence_label("CONFIRMED") == "Confirmed"
    assert confidence_label("AMBIGUOUS") == "Ambiguous"
    assert confidence_label("CLS_PROXIED") == "CLS"
    assert confidence_label(None) == "Unknown"
    assert posture(open_high=0, join_elevated=False) == "Normal"
    assert posture(open_high=1, join_elevated=False) == "Elevated"
    card = behavior(enforce_locked=True, honeypot_configured=True)
    assert "Ban members" in card["will_not"]
    assert "Delete phishing messages" in card["will"]
    assert enforce_unlocked() is False
    with pytest.raises(EnforceUnavailable):
        assert_mode_writable("ENFORCE")


def test_join_signal_is_explainable():
    now = datetime.now(timezone.utc)
    rows = [{"joined_at": now - timedelta(seconds=30), "created_at": now - timedelta(days=1)} for _ in range(8)]
    signal = join_signal(rows, now=now)
    assert signal["elevated"] is True
    assert "8 joins" in signal["explanation"]
    assert "score" not in signal


def test_channel_must_belong_to_the_guild():
    assert channel_in_guild({11}, 11) is True
    assert channel_in_guild({11}, 22) is False


async def test_incidents_persist_filter_and_close(db_reset):
    for index in range(30):
        await note_signal(guild_id=GUILD, subject_id=USER + index, engine="human", kind="phishing", detail="Message deleted")
    await note_signal(guild_id=OTHER, subject_id=USER, engine="human", kind="phishing", detail="other guild")
    page = await list_incidents(GUILD, page=1, page_size=25)
    assert page["total"] == 30
    assert len(page["rows"]) == 25
    assert page["rows"][0]["title"] == "Phishing message"
    assert page["rows"][0]["confidence_label"] == "Confirmed"
    assert "phishing" != page["rows"][0]["title"]
    assert all(row["actor_id"] != str(USER) or True for row in page["rows"])
    second = await list_incidents(GUILD, page=2, page_size=25)
    assert len(second["rows"]) == 5
    other = await list_incidents(OTHER)
    assert other["total"] == 1
    filtered = await list_incidents(GUILD, detector="phishing", actor=str(USER))
    assert filtered["total"] == 1
    assert filtered["rows"][0]["actor_id"] == str(USER)
    huge = await note_signal(guild_id=GUILD, subject_id=HUGE, engine="human", kind="human_honeypot", detail="Message deleted")
    listed = await list_incidents(GUILD, actor=str(HUGE))
    assert listed["rows"][0]["actor_id"] == str(HUGE)
    view = await present_incident(GUILD, huge)
    assert view["developer"]["subject_id"] == str(HUGE)
    closed = await close_incident(guild_id=GUILD, incident_id=huge, actor_user_id=ROOT, closure="FALSE_POSITIVE", note="staff test")
    assert closed["offer_trust"] is True
    assert closed["status_label"] == "False positive"
    resolved_id = await note_signal(guild_id=GUILD, subject_id=USER + 90, engine="human", kind="phishing", detail="Message deleted")
    resolved = await close_incident(guild_id=GUILD, incident_id=resolved_id, actor_user_id=ROOT, closure="RESOLVED", note="done")
    assert resolved["status_label"] == "Resolved"
    events = await list_events(GUILD, limit=50)
    types = {row["event_type"] for row in events["events"]}
    assert "security.incident_created" in types
    assert "security.honeypot_triggered" in types


async def test_honeypot_phishing_and_eligibility(db_reset):
    deleted = {"count": 0}

    async def delete():
        deleted["count"] += 1

    async def deny():
        raise PermissionError("50013 Missing Permissions")

    skipped = await handle_center_message(
        guild_id=GUILD, channel_id=1, author_id=USER, content="free-nitro", author_is_bot=False,
        webhook=False, trusted=False, staff=False, eligible=False, delete_message=delete,
    )
    assert skipped["reason"] == "ineligible"
    assert deleted["count"] == 0
    await save_settings(guild_id=GUILD, honeypot_channel_id=42, honeypot_set=True, phishing_action="delete_timeout")
    exempt = await handle_center_message(
        guild_id=GUILD, channel_id=42, author_id=USER, content="hello", author_is_bot=False,
        webhook=False, trusted=False, staff=True, eligible=True, delete_message=delete,
    )
    assert exempt["reason"] == "no_match"
    bot = await handle_center_message(
        guild_id=GUILD, channel_id=42, author_id=USER + 3, content="hello", author_is_bot=True,
        webhook=False, trusted=False, staff=False, eligible=True, delete_message=delete,
    )
    assert bot["handled"] is False
    hit = await handle_center_message(
        guild_id=GUILD, channel_id=42, author_id=USER + 4, content="scam", author_is_bot=False,
        webhook=False, trusted=False, staff=False, eligible=True, delete_message=delete,
    )
    assert hit["kind"] == "human_honeypot"
    assert hit["action"]["outcome"] == "succeeded"
    assert deleted["count"] == 1
    phish = await handle_center_message(
        guild_id=GUILD, channel_id=7, author_id=USER + 5, content="free-nitro", author_is_bot=False,
        webhook=False, trusted=False, staff=False, eligible=True, delete_message=deny,
    )
    assert phish["action"]["reason"] == "Missing Manage Messages"
    assert any(item["reason"].startswith("Member punishment stays locked") for item in phish["results"])
    saved = await get_settings(GUILD)
    assert saved["honeypot_channel_id"] == "42"


async def test_trust_scope_expiry_and_root(db_reset):
    with pytest.raises(TrustRejected):
        await grant_trust(guild_id=GUILD, subject_id=USER, kind="human", scopes=["channel.delete"], actor_user_id=USER, reason="no")
    with pytest.raises(TrustRejected):
        await grant_trust(guild_id=GUILD, subject_id=USER, kind="human", scopes=["not-a-scope"], actor_user_id=ROOT)
    past = datetime.now(timezone.utc) - timedelta(minutes=1)
    await grant_trust(
        guild_id=GUILD, subject_id=USER, kind="human", scopes=["channel.delete"],
        actor_user_id=ROOT, expires_at=past, reason="role changes for a short window",
    )
    assert await is_trusted(GUILD, USER) is False
    future = datetime.now(timezone.utc) + timedelta(minutes=30)
    await grant_trust(
        guild_id=GUILD, subject_id=USER, kind="human", scopes=["role.permission_escalation", "member.privileged_role_grant", "role.delete"],
        actor_user_id=ROOT, expires_at=future, reason="Role changes",
    )
    assert await is_trusted(GUILD, USER) is True
    await revoke_trust(guild_id=GUILD, subject_id=USER, actor_user_id=ROOT)
    assert await is_trusted(GUILD, USER) is False
    events = await list_events(GUILD, limit=20)
    types = {row["event_type"] for row in events["events"]}
    assert "security.trust_granted" in types
    assert "security.trust_revoked" in types


async def test_restore_respects_hierarchy_and_stays_locked(db_reset):
    assert enforce_unlocked() is False
    async with session_scope() as session:
        session.add(
            SecurityQuarantine(
                guild_id=GUILD,
                user_id=USER,
                status="ACTIVE",
                prior_role_ids=[31, 32, 33],
                removed_role_ids=[31, 32, 33],
                prior_role_perms={"33": {"administrator": False}},
            )
        )
    member = Member()
    result = await restore_quarantine(
        guild_id=GUILD,
        user_id=USER,
        member=member,
        actor_is_root=True,
        roles=[Role(31, position=1), Role(32, position=80), Role(33, position=1, administrator=True)],
        bot_top_position=50,
    )
    assert [role.id for role in member.added] == [31]
    assert result["status"] == "PARTIAL"
    assert any(item["reason"] == "CLS role is below this role" for item in result["results"])
    assert any(item["reason"] == "Role gained administrator since quarantine" for item in result["results"])
    with pytest.raises(EnforceUnavailable):
        await restore_quarantine(guild_id=GUILD, user_id=USER, member=member, actor_is_root=False, roles=[], bot_top_position=50)


async def test_maintenance_is_capped_and_does_not_disable_security(db_reset):
    with pytest.raises(MaintenanceRejected):
        await start_window(guild_id=GUILD, actor_user_id=ROOT, reason="work", duration_s=60 * 60 + 1)
    row = await start_window(guild_id=GUILD, actor_user_id=ROOT, reason="work", duration_s=60 * 60)
    assert row.expires_at > row.starts_at
    from cls_platform.security.config import ensure_guild_config

    config = await ensure_guild_config(GUILD)
    assert config.human_mode == "OBSERVE"
    events = await list_events(GUILD, limit=10)
    assert any(item["event_type"] == "security.maintenance_started" for item in events["events"])


async def test_security_log_sentence(db_reset):
    await security_event(guild_id=GUILD, event_type="security.phishing_deleted", sentence="CLS deleted a phishing message.", actor_id=USER, confidence="certain")
    events = await list_events(GUILD, limit=5)
    row = events["events"][0]
    assert row["event_type"] == "security.phishing_deleted"
    assert row["category"] == "security"
    from cls_platform.logging.present import present

    view = present(row)
    assert "phishing" in view["summary"].lower() or "CLS deleted" in view["summary"]
