"""Automod V2 engine, ledger, API, and legacy containment."""

from __future__ import annotations

import os
from pathlib import Path

import aiosqlite
import pytest

from cls_platform.automod.engine import (
    bad_word_hit,
    caps_hit,
    emoji_count,
    evaluate_message,
    fresh_config,
    highest_escalation,
    invite_hit,
    link_hit,
    normalize_duplicate,
    scope_reason,
    validate_config,
)
from cls_platform.automod.migrate import legacy_seed
from cls_platform.automod.runtime import execute_actions, reset_runtime_state
from cls_platform.automod.store import get_config, invalidate, save_config
from cls_platform.logging.present import present
from tests.conftest import TEST_GUILD_A, TEST_GUILD_B, TEST_ROOT, auth_headers

BIG = "1543105121913802823"


def _config(**overrides):
    body = fresh_config("balanced")
    body["enabled"] = True
    body.update(overrides)
    return body


def _flood():
    body = _config()
    for rule in body["rules"]:
        rule["enabled"] = rule["id"] == "flood"
        if rule["id"] == "flood":
            rule["message_action"] = "delete"
            rule["member_action"] = "timeout"
            rule["timeout_seconds"] = 600
            rule["trigger"] = {"count": 5, "window_seconds": 5, "per_channel": False}
    return body


class _Target:
    def __init__(self, **flags):
        self.deleted = 0
        self.timed_out = None
        self.kicked = 0
        self.banned = 0
        self.guild_id = 1
        self.is_owner = flags.get("owner", False)
        self.is_admin = flags.get("admin", False)
        self.hierarchy_ok = flags.get("hierarchy", True)
        self.manage_messages = flags.get("manage_messages", True)
        self.moderate_members = flags.get("moderate_members", True)
        self.kick_members = flags.get("kick_members", True)
        self.ban_members = flags.get("ban_members", True)
        self.send_messages = True

    async def delete_messages(self):
        self.deleted += 1

    async def timeout(self, seconds):
        self.timed_out = seconds

    async def kick(self):
        self.kicked += 1

    async def ban(self):
        self.banned += 1

    async def dm(self):
        return None

    async def notice(self):
        return None


def test_flood_threshold_and_duplicate_normalization():
    body = _flood()
    miss = evaluate_message(body, content="hi", ctx={"member_id": 1, "channel_id": 2, "category_id": 0, "role_ids": []}, flood_stamps=[0, 1], now=2)
    assert miss == []
    hit = evaluate_message(body, content="hi", ctx={"member_id": 1, "channel_id": 2, "category_id": 0, "role_ids": []}, flood_stamps=[0, 1, 2, 3], now=4)
    assert hit[0]["rule_id"] == "flood"
    assert len(hit[0]["actions"]) == 2
    assert normalize_duplicate("Hello   WORLD\u200b") == "hello world"


def test_caps_minimum_emoji_links_invites_and_words():
    assert caps_hit("HI", {"percent": 70, "min_length": 8}) is None
    assert caps_hit("HELLO THERE", {"percent": 70, "min_length": 8})["percent"] == 100
    assert emoji_count("😀😀 <a:party:1>") == 3
    assert link_hit("see https://evil.test/a", {"mode": "block", "allow": ["safe.test"], "deny": []}) == "evil.test"
    assert link_hit("see https://safe.test/a", {"mode": "block", "allow": ["safe.test"], "deny": []}) is None
    assert invite_hit("https://discord.gg/mine", {"block_external": True, "allow_own": True, "allow_codes": []}, own_codes={"mine"}) is None
    assert invite_hit("https://discord.gg/other", {"block_external": True, "allow_own": True, "allow_codes": []}, own_codes={"mine"}) == "other"
    assert bad_word_hit("this is baaaad", {"terms": ["bad"], "mode": "contains", "exceptions": []}) == "bad"
    assert bad_word_hit("classic", {"terms": ["ass"], "mode": "whole", "exceptions": []}) is None
    assert bad_word_hit("scammer", {"terms": ["scam"], "mode": "contains", "exceptions": ["scammer"]}) is None


def test_exclusion_precedence_and_staff_visibility():
    rule = {"scope": {"include_channels": ["9"], "exclude_channels": ["9"], "include_categories": [], "exclude_categories": [], "exclude_roles": []}}
    reason = scope_reason({"channels": [], "categories": [], "roles": [], "members": [], "staff_roles": ["4"]}, rule, {"member_id": 1, "channel_id": 9, "category_id": 0, "role_ids": ["4"]})
    assert reason == "Staff immunity"
    excluded = scope_reason({}, rule, {"member_id": 1, "channel_id": 9, "category_id": 0, "role_ids": []})
    assert excluded == "Channel exclusion"


def test_highest_escalation_ignores_expired_and_lower_matches():
    now = 10_000.0
    strikes = [
        {"points": 10, "created_at": now - 10, "expires_at": now + 10},
        {"points": 1, "created_at": now - 999999, "expires_at": now - 1},
    ]
    thresholds = [
        {"points": 3, "window_seconds": 1800, "action": "timeout", "duration_seconds": 600},
        {"points": 10, "window_seconds": 86400, "action": "kick", "duration_seconds": None},
    ]
    chosen = highest_escalation(strikes, thresholds, now)
    assert chosen["action"] == "kick"


@pytest.mark.asyncio
async def test_compound_actions_report_each_result():
    reset_runtime_state()
    target = _Target(hierarchy=False, moderate_members=True, manage_messages=True)
    actions = [
        {"kind": "delete", "label": "Delete message", "duration_seconds": None},
        {"kind": "timeout", "label": "Timeout 10m", "duration_seconds": 600},
    ]
    results = await execute_actions(actions, target, observe=False)
    assert results[0]["outcome"] == "succeeded"
    assert target.deleted == 1
    assert results[1]["outcome"] == "failed"
    assert "below the member's highest role" in results[1]["reason"]
    missing = await execute_actions(actions, _Target(manage_messages=False, moderate_members=False), observe=False)
    assert missing[0]["reason"].startswith("CLS needs the Manage Messages")
    assert missing[1]["reason"].startswith("CLS needs the Moderate Members")
    owner = await execute_actions([{"kind": "ban", "label": "Ban", "duration_seconds": None}], _Target(owner=True), observe=False)
    assert owner[0]["outcome"] == "skipped"
    kicked = await execute_actions([{"kind": "kick", "label": "Kick", "duration_seconds": None}], _Target(kick_members=False), observe=False)
    assert "Kick Members" in kicked[0]["reason"]
    banned = await execute_actions([{"kind": "ban", "label": "Ban", "duration_seconds": None}], _Target(), observe=False)
    assert banned[0]["outcome"] == "succeeded"


@pytest.mark.asyncio
async def test_automod_log_event_persists(api_client):
    from cls_platform.logging.store import get_event, record_event

    recorded = await record_event(
        guild_id=TEST_GUILD_A,
        category="automod",
        event_type="automod.spam",
        actor_id=TEST_ROOT,
        actor_confidence="certain",
        metadata={"sentence": "Spam detected — @ada sent 9 messages in 4.1s in #general", "rule": "Message flood"},
    )
    loaded = await get_event(TEST_GUILD_A, recorded["id"])
    assert loaded["event_type"] == "automod.spam"
    assert loaded["presentation"]["summary"].startswith("Spam detected")


def test_logging_sentence_is_human():
    view = present({
        "event_type": "automod.spam",
        "category": "automod",
        "metadata": {"sentence": "Spam detected — @ada sent 9 messages in 4.1s in #general"},
        "actor_id": "1",
        "target_id": "2",
    })
    assert view["summary"] == "Spam detected — @ada sent 9 messages in 4.1s in #general"


def test_legacy_listeners_return_immediately():
    root = Path(__file__).resolve().parents[1]
    for relative in (
        "cogs/automod/antispam.py",
        "cogs/automod/anticaps.py",
        "cogs/automod/antilink.py",
        "cogs/automod/anti_invites.py",
        "cogs/automod/anti_mass_mention.py",
        "cogs/automod/anti_emoji_spam.py",
        "cogs/commands/Media.py",
        "cogs/commands/blacklist.py",
    ):
        text = (root / relative).read_text(encoding="utf-8")
        assert "Automod V2 is the only enforcement listener." in text
    loader = (root / "cogs/cog_loader.py").read_text(encoding="utf-8")
    assert 'CogSpec("cogs.automod.antispam", "AntiSpam", O, skip=True' in loader
    assert 'CogSpec("cogs.automod_v2", "AutomodV2", O)' in loader


@pytest.mark.asyncio
async def test_legacy_warn_is_not_migrated_as_an_action(tmp_path, monkeypatch):
    path = tmp_path / "automod.db"
    async with aiosqlite.connect(path) as db:
        await db.execute("CREATE TABLE automod (guild_id INTEGER PRIMARY KEY, enabled INTEGER)")
        await db.execute("CREATE TABLE automod_punishments (guild_id INTEGER, event TEXT, punishment TEXT)")
        await db.execute("CREATE TABLE automod_ignored (guild_id INTEGER, type TEXT, id INTEGER)")
        await db.execute("INSERT INTO automod VALUES (42, 1)")
        await db.execute("INSERT INTO automod_punishments VALUES (42, 'Anti spam', 'Warn')")
        await db.execute("INSERT INTO automod_punishments VALUES (42, 'Anti link', 'delete')")
        await db.commit()
    monkeypatch.setenv("AUTOMOD_DB", str(path))
    seed, notes, migrated = await legacy_seed(42)
    assert migrated is True
    flood = next(rule for rule in seed["rules"] if rule["id"] == "flood")
    links = next(rule for rule in seed["rules"] if rule["id"] == "links")
    assert flood["enabled"] is False
    assert links["enabled"] is True
    assert links["message_action"] == "delete"
    assert any("Warn" in note for note in notes)
    monkeypatch.delenv("AUTOMOD_DB", raising=False)


@pytest.mark.asyncio
async def test_api_persistence_isolation_pagination_and_false_positive(api_client):
    client, _ = api_client
    headers = await auth_headers(TEST_ROOT)
    body = _flood()
    body["exclusions"]["members"] = [BIG]
    saved = await client.put(f"/api/v1/guilds/{TEST_GUILD_A}/automod/v2", headers=headers, json=body)
    assert saved.status_code == 200, saved.text
    payload = saved.json()
    assert payload["guild_id"] == str(TEST_GUILD_A)
    assert payload["exclusions"]["members"] == [BIG]
    assert payload["rules"][0]["engine"] == "cls"
    invalidate(TEST_GUILD_A)
    again = await get_config(TEST_GUILD_A)
    assert again["enabled"] is True
    assert again["exclusions"]["members"] == [BIG]

    other = await client.get(f"/api/v1/guilds/{TEST_GUILD_B}/automod/v2", headers=headers)
    assert other.status_code == 200
    assert other.json()["enabled"] is False

    from cls_platform.automod.store import add_violation
    from datetime import datetime, timezone

    for index in range(30):
        await add_violation(
            guild_id=TEST_GUILD_A,
            member_id=100 + index,
            channel_id=200,
            message_id=300 + index,
            rule_id="flood",
            summary=f"sent {index}",
            excerpt="hi",
            detail={"actions": [{"kind": "delete", "outcome": "succeeded", "reason": "Deleted."}], "threshold": {"count": 5}, "engine": "cls"},
            actions=[{"kind": "delete", "outcome": "succeeded", "reason": "Deleted."}],
            log_event_id=None,
            occurred_at=datetime.now(timezone.utc),
        )
    page = await client.get(f"/api/v1/guilds/{TEST_GUILD_B}/automod/v2/violations?page_size=25", headers=headers)
    assert page.json()["total"] == 0
    listed = await client.get(
        f"/api/v1/guilds/{TEST_GUILD_A}/automod/v2/violations?page=2&page_size=25&rule=flood&action=delete&result=succeeded",
        headers=headers,
    )
    assert listed.status_code == 200
    assert listed.json()["total"] == 30
    assert len(listed.json()["rows"]) == 5
    assert isinstance(listed.json()["rows"][0]["member_id"], str)
    first = listed.json()["rows"][0]["id"]
    marked = await client.post(f"/api/v1/guilds/{TEST_GUILD_A}/automod/v2/violations/{first}/false-positive", headers=headers)
    assert marked.json()["false_positive"] is True
    refused = await client.post(
        f"/api/v1/guilds/{TEST_GUILD_A}/automod/v2/violations/{first}/follow-up",
        headers=headers,
        json={"confirm": False, "kind": "channel_exclusion", "value": "9"},
    )
    assert refused.status_code == 422
    legacy = await client.patch(f"/api/v1/guilds/{TEST_GUILD_A}/automod", headers=headers, json={"enabled": False})
    assert legacy.status_code == 410
    still = await get_config(TEST_GUILD_A)
    assert still["enabled"] is True


def test_timeout_range_rejected():
    body = _flood()
    body["rules"][0]["timeout_seconds"] = 10
    with pytest.raises(ValueError):
        validate_config(body)


def test_simulator_does_not_need_a_saved_punishment_flag():
    body = _config()
    for rule in body["rules"]:
        rule["enabled"] = rule["id"] == "caps"
        if rule["id"] == "caps":
            rule["mode"] = "observe"
    hits = evaluate_message(body, content="THIS IS ALL CAPS NOW", ctx={"member_id": 1, "channel_id": 2, "category_id": 0, "role_ids": []}, now=1)
    assert hits[0]["mode"] == "observe"
    assert hits[0]["actions"][0]["outcome"] == "skipped"
