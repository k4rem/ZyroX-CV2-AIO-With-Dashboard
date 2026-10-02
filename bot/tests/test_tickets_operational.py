"""Tickets T1: privacy, forms, publish identity, transcript, inactivity."""

from datetime import datetime, timezone

from cls_platform.logging.present import category_for_event, present
from cls_platform.tickets.access import access_overwrites
from cls_platform.tickets.html_transcript import render_html
from cls_platform.tickets.naming import channel_name, parse_custom_id
from cls_platform.tickets.schedule import inactivity_still_due
from cls_platform.tickets.store import (
    TicketError,
    add_participant,
    bind_channel,
    capture_message,
    create_category,
    create_panel,
    load_panel,
    mark_degraded,
    open_ticket,
    remove_participant,
    save_html,
    set_publish,
    transcript,
    transfer_ticket,
)

GUILD = 100000000000000100
OTHER = 100000000000000200
USER = 9007199254740993
STAFF = 1543105121804615781
CHANNEL = 1555268757436371007


def test_private_overwrites_and_transfer_shape():
    opened = access_overwrites(everyone_id=1, opener_id=2, staff_role_ids=[STAFF], bot_id=9, extra_user_ids=[4])
    assert opened[1]["view"] is False
    assert opened[2]["view"] is True and opened[2]["send"] is True
    assert opened[STAFF]["view"] is True
    assert opened[9]["manage"] is True
    moved = access_overwrites(everyone_id=1, opener_id=2, staff_role_ids=[8], bot_id=9, extra_user_ids=[4])
    assert STAFF not in moved
    assert moved[8]["view"] is True
    assert moved[2]["view"] is True and moved[4]["view"] is True
    denied = access_overwrites(everyone_id=1, opener_id=2, staff_role_ids=[8], bot_id=9, extra_user_ids=[4], deny_role_ids=[STAFF])
    assert denied[STAFF]["view"] is False
    assert denied[8]["view"] is True


def test_custom_ids_and_names_and_html():
    kind, action, ident = parse_custom_id(f"cls-ticket:open:{STAFF}")
    assert (kind, action, ident) == ("open", "open", str(STAFF))
    assert parse_custom_id(f"cls-t:claim:{USER}")[1] == "claim"
    assert channel_name("ticket-{number}-{username}", 1, "Aero User!") == "ticket-1-aero-user"
    html = render_html(
        number=1,
        guild_name="cls-backup",
        category="Billing",
        opener="Aero",
        assignee="Staff",
        reason="Resolved",
        opened=datetime(2026, 10, 2, tzinfo=timezone.utc),
        closed=None,
        messages=[{"display_name": "<script>", "content": "<script>alert(1)</script>", "attachments": [{"filename": "a.png", "url": "https://cdn.example/a.png"}], "embeds": [{"title": "Hi", "description": "There"}], "reference_id": CHANNEL, "created_at": datetime(2026, 10, 2, tzinfo=timezone.utc)}],
    )
    assert "<script>alert" not in html
    assert "&lt;script&gt;" in html
    assert "a.png" in html
    assert "Resolved" in html


def test_inactivity_ignores_stale_generation():
    assert inactivity_still_due("open", 2, 2) is True
    assert inactivity_still_due("open", 3, 2) is False
    assert inactivity_still_due("closed", 2, 2) is False
    from cls_platform.tickets.schedule import payload_generation

    assert payload_generation({"generation": 0}) == 0
    assert inactivity_still_due("open", 0, payload_generation({"generation": 0})) is True


def test_ticket_logs_are_bot_actions():
    view = present({"event_type": "ticket_opened", "category": "bot_actions", "metadata": {"summary": "Ticket 1 opened"}})
    assert view["title"] == "Ticket opened"
    assert category_for_event("ticket_closed") == "bot_actions"


async def test_forms_publish_participants_and_messages(db_reset):
    billing = await create_category(guild_id=GUILD, name="Billing", discord_category_id=CHANNEL, staff_role_ids=[STAFF], name_format="ticket-{number}-{username}")
    technical = await create_category(guild_id=GUILD, name="Technical", discord_category_id=CHANNEL + 1, staff_role_ids=[STAFF + 1])
    panel = await create_panel(
        guild_id=GUILD,
        category_id=billing["id"],
        channel_id=CHANNEL,
        title="Contact us",
        message="We can help.",
        button_label="Open ticket",
        questions=[
            {"label": "Order number", "kind": "short", "required": True, "min_length": 1, "max_length": 20},
            {"label": "Describe the issue", "kind": "paragraph", "required": False, "max_length": 500},
        ],
        required_role_ids=[USER],
        blocked_role_ids=[USER + 1],
    )
    loaded = await load_panel(panel["id"])
    assert loaded["questions"][0]["kind"] == "short"
    assert loaded["questions"][1]["kind"] == "paragraph"
    assert loaded["questions"][0]["min_length"] == 1
    try:
        await open_ticket(guild_id=GUILD, category_id=billing["id"], opener_id=USER + 2, panel_id=panel["id"], member_role_ids=[])
        assert False, "required role"
    except TicketError as exc:
        assert str(exc) == "required_role"
    try:
        await open_ticket(guild_id=GUILD, category_id=billing["id"], opener_id=USER + 2, panel_id=panel["id"], member_role_ids=[USER, USER + 1])
        assert False, "blocked role"
    except TicketError as exc:
        assert str(exc) == "blocked_role"
    opened = await open_ticket(
        guild_id=GUILD,
        category_id=billing["id"],
        opener_id=USER + 2,
        opener_name="Aero",
        panel_id=panel["id"],
        member_role_ids=[USER],
        answers={"Order number": "100"},
    )
    assert opened["name"] == "ticket-1-aero"
    assert str(STAFF) == str(opened["staff_role_ids"][0]) or opened["staff_role_ids"][0] == STAFF
    await bind_channel(guild_id=GUILD, ticket_id=opened["id"], channel_id=CHANNEL, control_message_id=CHANNEL + 5)
    published = await set_publish(guild_id=GUILD, panel_id=panel["id"], channel_id=CHANNEL, message_id=CHANNEL + 9, status="published")
    assert published["published_message_id"] == str(CHANNEL + 9)
    assert published["publish_status"] == "published"
    await capture_message(
        guild_id=GUILD,
        channel_id=CHANNEL,
        message_id=CHANNEL + 8,
        author_id=USER + 2,
        author_name="aero",
        display_name="Aero",
        avatar="https://cdn.example/a.png",
        content="hello <b>",
        attachments=[{"filename": "note.txt", "url": "https://cdn.example/note.txt", "size": 12}],
        embeds=[],
        reference_id=None,
        created_at=datetime.now(timezone.utc),
    )
    await add_participant(guild_id=GUILD, ticket_id=opened["id"], user_id=USER + 4, actor_id=STAFF)
    await remove_participant(guild_id=GUILD, ticket_id=opened["id"], user_id=USER + 4, actor_id=STAFF)
    try:
        await remove_participant(guild_id=GUILD, ticket_id=opened["id"], user_id=USER + 2, actor_id=STAFF)
        assert False, "opener"
    except TicketError as exc:
        assert str(exc) == "is_opener"
    moved = await transfer_ticket(guild_id=GUILD, ticket_id=opened["id"], category_id=technical["id"], actor_id=STAFF)
    assert moved["staff_role_ids"] == [STAFF + 1]
    assert STAFF in moved["previous_staff_role_ids"]
    await mark_degraded(guild_id=OTHER, ticket_id=opened["id"], reason="nope")
    body = await transcript(GUILD, opened["id"])
    assert body["messages"][0]["content"] == "hello <b>"
    assert body["messages"][0]["attachments"][0]["filename"] == "note.txt"
    await save_html(guild_id=GUILD, ticket_id=opened["id"], html="<p>safe</p>", actor_id=STAFF)
    stored = await transcript(GUILD, opened["id"])
    assert stored["html"] == "<p>safe</p>"
    try:
        await transcript(OTHER, opened["id"])
        assert False, "isolation"
    except TicketError:
        pass
