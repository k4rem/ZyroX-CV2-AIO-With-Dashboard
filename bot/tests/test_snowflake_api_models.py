"""API models must serialize Discord IDs as JSON strings (JS safe)."""

from __future__ import annotations

import json

from api.schemas import TicketCategory, TicketConfig, TicketEmbed


def test_ticket_config_json_preserves_snowflake_digits():
    gid = "1543105121804615781"
    ch = "100000000000000001"
    tc = TicketConfig(
        guild_id=gid,
        panel_channel=ch,
        panel_message=None,
        logging_channel=ch,
        closed_category=None,
        panel_type="button",
        embed=TicketEmbed(title="T", description="D"),
        categories=[
            TicketCategory(
                name="General",
                emoji="📩",
                staff_roles=[ch],
                discord_category_id=ch,
            )
        ],
        staff_roles=[ch],
        open_ticket_count=0,
    )
    dumped = tc.model_dump()
    assert dumped["guild_id"] == gid
    assert dumped["panel_channel"] == ch
    assert dumped["categories"][0]["staff_roles"] == [ch]
    encoded = json.dumps(dumped)
    assert ch in encoded
    assert "100000000000000000" not in encoded


def test_ticket_config_model_dump_json_uses_string_snowflakes():
    gid = "1543105121804615781"
    ch = "100000000000000001"
    tc = TicketConfig(
        guild_id=gid,
        panel_channel=ch,
        panel_message=None,
        logging_channel=ch,
        closed_category=None,
        panel_type="button",
        embed=TicketEmbed(title="T", description="D"),
        categories=[],
        staff_roles=[ch],
        open_ticket_count=0,
    )
    encoded = tc.model_dump_json()
    assert f'"guild_id":"{gid}"' in encoded or f'"guild_id": "{gid}"' in encoded.replace(" ", "")
    assert f'"panel_channel":"{ch}"' in encoded.replace(" ", "")
    assert "100000000000000000" not in encoded


def test_grant_body_accepts_string_ids():
    from api.routes.access import GrantCreateBody

    body = GrantCreateBody(
        guild_id="100000000000000001",
        discord_user_id="1543105121804615781",
        template_key="admin",
    )
    assert body.guild_id == "100000000000000001"
    assert body.discord_user_id == "1543105121804615781"
