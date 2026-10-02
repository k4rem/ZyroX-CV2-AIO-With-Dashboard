"""Tickets T3: priority, tags, notes, routing, hours, metrics, replies."""

from datetime import datetime, timedelta, timezone

import pytest

from cls_platform.tickets.advanced import (
    add_note,
    archive_tag,
    category_public,
    close_request_expired,
    delete_note,
    known_categories,
    metrics,
    panel_advanced,
    render_reply,
    route_category,
    save_panel_advanced,
    save_reply,
    save_tag,
    set_priority,
    set_ticket_tags,
    summarize_metrics,
    support_status,
)
from cls_platform.tickets.deliver import control_view
from cls_platform.tickets.naming import parse_custom_id
from cls_platform.tickets.store import TicketError, create_category, create_panel, list_queue, open_ticket, ticket_detail, transcript, update_category

GUILD = 1543105121804615781
OTHER = 1543105121804615782
USER = 9007199254740993


def test_routing_hours_and_close_timeout():
    billing = "bill"
    technical = "tech"
    category, status = route_category(
        rules=[{"question_label": "Issue type", "operator": "equals", "value": "Billing", "category_id": billing}],
        answers={"Issue type": "Billing"},
        default_category_id="default",
        known_category_ids={billing, technical, "default"},
    )
    assert (category, status) == (billing, "matched")
    fallback, fallback_status = route_category(
        rules=[{"question_label": "Issue type", "operator": "equals", "value": "Billing", "category_id": "missing"}],
        answers={"Issue type": "billing"},
        default_category_id="default",
        known_category_ids={"default"},
    )
    assert (fallback, fallback_status) == ("default", "fallback")
    contains, contains_status = route_category(
        rules=[{"question_label": "Details", "operator": "contains", "value": "refund", "category_id": billing}],
        answers={"Details": "I need a refund"},
        default_category_id="default",
        known_category_ids={billing},
    )
    assert (contains, contains_status) == (billing, "matched")
    noon = datetime(2026, 10, 5, 12, 0, tzinfo=timezone.utc)
    assert support_status({"hours_mode": "always"}, noon)["open"] is True
    inside = support_status({"hours_mode": "scheduled", "hours_timezone": "UTC", "hours_days": 127, "hours_start": "09:00", "hours_end": "17:00", "hours_outside": "allow"}, noon)
    assert inside["open"] is True
    night = support_status({"hours_mode": "scheduled", "hours_timezone": "UTC", "hours_days": 31, "hours_start": "09:00", "hours_end": "17:00", "hours_outside": "block"}, datetime(2026, 10, 4, 20, 0, tzinfo=timezone.utc))
    assert night["open"] is False and "offline" in (night["notice"] or "")
    assert support_status({"hours_mode": "scheduled", "hours_timezone": "Not/AZone", "hours_days": 127, "hours_start": "09:00", "hours_end": "17:00"}, noon)["invalid_timezone"] is True
    requested = datetime(2026, 10, 2, 12, 0, tzinfo=timezone.utc)
    assert close_request_expired(requested, None, requested + timedelta(hours=2)) is False
    assert close_request_expired(requested, 30, requested + timedelta(minutes=31)) is True
    assert close_request_expired(requested, 30, requested + timedelta(minutes=10)) is False
    assert "{number}" not in render_reply("Hello {opener}, ticket {number}.", number=12, opener="Aero")
    kind, action, ident = parse_custom_id("cls-ticket:pick:panel")
    assert (kind, action, ident) == ("pick", "pick", "panel")
    view = control_view("ticket", closed=False, close_mode="request", tags=[{"id": "1", "name": "Billing"}])
    assert len(view.children) == 9


def test_metrics_use_claim_and_close_times():
    opened = datetime(2026, 10, 2, 8, 0, tzinfo=timezone.utc)
    now = datetime(2026, 10, 2, 12, 0, tzinfo=timezone.utc)
    rows = [
        {"raw_status": "open", "status": "open", "assignee_id": None, "opened_at": opened, "closed_at": None, "category_name": "Billing", "tags": [{"name": "Refund"}]},
        {"raw_status": "closed", "status": "closed", "assignee_id": 1, "opened_at": opened, "closed_at": opened + timedelta(minutes=40), "category_name": "Billing", "tags": []},
    ]
    summary = summarize_metrics(rows, [(opened, opened + timedelta(minutes=10))], now, 7)
    assert summary["open"] == 1
    assert summary["unassigned"] == 1
    assert summary["opened_today"] == 2
    assert summary["closed_today"] == 1
    assert summary["median_first_claim_minutes"] == 10
    assert summary["average_resolution_minutes"] == 40
    assert summary["by_tag"] == [{"name": "Refund", "open": 1}]


async def test_priority_tags_notes_and_isolation(db_reset):
    category = await create_category(guild_id=GUILD, name="Billing", discord_category_id=None, staff_role_ids=[USER])
    other = await create_category(guild_id=OTHER, name="Other", discord_category_id=None, staff_role_ids=[])
    opened = await open_ticket(guild_id=GUILD, category_id=category["id"], opener_id=USER, opener_name="Aero", opener_avatar="", answers={}, panel_id=None, member_role_ids=[])
    assert opened["priority"] if "priority" in opened else True
    changed = await set_priority(guild_id=GUILD, ticket_id=opened["id"], priority="high", actor_id=USER)
    assert changed["from"] == "normal" and changed["to"] == "high"
    with pytest.raises(TicketError):
        await set_priority(guild_id=OTHER, ticket_id=opened["id"], priority="urgent", actor_id=USER)
    billing = await save_tag(guild_id=GUILD, tag_id=None, name="Billing", position=0)
    refund = await save_tag(guild_id=GUILD, tag_id=None, name="Refund", position=1)
    renamed = await save_tag(guild_id=GUILD, tag_id=billing["id"], name="Account", position=0)
    assert renamed["name"] == "Account"
    await set_ticket_tags(guild_id=GUILD, ticket_id=opened["id"], tag_ids=[billing["id"], refund["id"]], actor_id=USER)
    await archive_tag(guild_id=GUILD, tag_id=refund["id"])
    detail = await ticket_detail(GUILD, opened["id"])
    assert detail["priority"] == "high"
    assert {tag["name"] for tag in detail["tags"]} == {"Account", "Refund"}
    assert any(tag["id"] is None for tag in detail["tags"])
    note = await add_note(guild_id=GUILD, ticket_id=opened["id"], author_id=USER, body="Customer requested refund review")
    stored = await transcript(GUILD, opened["id"])
    assert "Customer requested refund review" not in str(stored.get("messages"))
    assert "notes" not in stored
    with pytest.raises(TicketError):
        await delete_note(guild_id=GUILD, ticket_id=opened["id"], note_id=note["id"], actor_id=1, allow_any=False)
    await delete_note(guild_id=GUILD, ticket_id=opened["id"], note_id=note["id"], actor_id=USER, allow_any=False)
    queue = await list_queue(GUILD)
    assert queue[0]["priority"] == "high"
    assert snowflake_safe(queue[0]["opener_id"])
    with pytest.raises(TicketError):
        await update_category(guild_id=GUILD, category_id=category["id"], hours={"hours_timezone": "Not/AZone"})
    await update_category(guild_id=GUILD, category_id=category["id"], hours={"hours_mode": "scheduled", "hours_timezone": "Asia/Riyadh", "hours_days": 31, "hours_start": "09:00", "hours_end": "17:00", "hours_outside": "allow"}, close_mode="request", close_timeout_minutes=30, close_timeout_set=True)
    public = await category_public(GUILD, category["id"])
    assert public["hours_timezone"] == "Asia/Riyadh"
    assert public["close_mode"] == "request"
    assert str(other["id"]) not in await known_categories(GUILD)
    panel = await create_panel(guild_id=GUILD, category_id=category["id"], channel_id=None, title="Help", message="", button_label="Open", questions=[{"label": "Issue type", "kind": "short", "required": True}])
    await save_panel_advanced(
        guild_id=GUILD,
        panel_id=panel["id"],
        panel_type="select",
        options=[{"label": "Billing", "description": "Payments", "emoji": "💳", "category_id": category["id"], "questions": [{"label": "Order", "kind": "short", "required": True}]}],
        rules=[{"question_label": "Issue type", "operator": "equals", "value": "Billing", "category_id": category["id"]}],
    )
    loaded = await panel_advanced(panel["id"])
    assert loaded["panel_type"] == "select"
    assert loaded["options"][0]["label"] == "Billing"
    assert parse_custom_id(f"cls-ticket:pick:{panel['id']}")[2] == panel["id"]
    assert loaded["options"][0]["id"]
    reply = await save_reply(guild_id=GUILD, reply_id=None, name="Greeting", content="Hello {opener}")
    assert reply["name"] == "Greeting"
    summary = await metrics(GUILD, datetime.now(timezone.utc), 7)
    assert summary["open"] >= 1
    assert summary["average_resolution_minutes"] is None or summary["average_resolution_minutes"] >= 0


def snowflake_safe(value) -> bool:
    return isinstance(value, str) and value == str(USER)
