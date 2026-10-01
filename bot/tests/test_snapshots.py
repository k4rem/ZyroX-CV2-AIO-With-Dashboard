"""Snapshot checksums, guild isolation, and SUSPECT marking."""

from __future__ import annotations

from datetime import datetime, timezone

from cls_platform.security.models import SecurityIncident
from cls_platform.snapshots import canonicalize, capture_snapshot, checksum, list_snapshots
from cls_platform.database import session_scope

GUILD = 100000000000000100
OTHER = 100000000000000200
BIG = 9007199254740993  # above 2^53


def _structure(guild_id=GUILD):
    return {
        "guild_id": guild_id,
        "roles": [{"id": BIG, "name": "mod", "position": 2, "permissions": "8"}],
        "channels": [
            {
                "id": BIG + 1,
                "name": "general",
                "type": "text",
                "position": 0,
                "overwrites": [{"id": BIG, "type": "role", "allow": "1024", "deny": "0"}],
            }
        ],
        "bans": [BIG + 2],
        "members": [{"user_id": BIG + 3, "role_ids": [BIG]}],
    }


def test_checksum_is_stable_and_keeps_large_snowflakes():
    document = canonicalize(_structure())
    assert checksum(document) == checksum(canonicalize(_structure()))
    assert document["roles"][0]["id"] == str(BIG)
    assert int(document["roles"][0]["id"]) == BIG


async def test_capture_is_guild_scoped_and_known_good(db_reset):
    row = await capture_snapshot(GUILD, _structure(), archive=b"anti-db", archive_key=b"test-key")
    assert row["status"] == "KNOWN_GOOD"
    assert row["snapshot_meta"]["checksum"]
    assert row["snapshot_meta"]["legacy_archive_hex"]
    assert row["snapshot_meta"]["document"]["bans"] == [str(BIG + 2)]
    other = await list_snapshots(OTHER)
    assert other == []
    own = await list_snapshots(GUILD)
    assert len(own) == 1


async def test_active_high_incident_marks_suspect(db_reset):
    now = datetime(2026, 10, 1, tzinfo=timezone.utc)
    async with session_scope() as session:
        session.add(
            SecurityIncident(
                guild_id=GUILD,
                engine="human",
                status="ACTIVE",
                severity="H",
                opened_at=now,
                last_activity_at=now,
                tier_map_version="v1",
            )
        )
    row = await capture_snapshot(GUILD, _structure())
    assert row["status"] == "SUSPECT"
    assert row["snapshot_meta"]["incident_state"] == "SUSPECT"
