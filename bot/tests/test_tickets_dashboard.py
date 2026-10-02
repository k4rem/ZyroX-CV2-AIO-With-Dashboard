"""Dashboard-facing ticket reads. Runtime open/claim behavior stays in the other suite."""

from cls_platform.tickets.store import (
    TicketError,
    blacklist_user,
    close_ticket,
    create_category,
    create_panel,
    guild_settings,
    list_blacklist,
    list_queue,
    list_transcripts,
    load_panel,
    open_ticket,
    save_panel,
    set_limits,
    set_publish,
    ticket_detail,
    unblacklist_user,
    update_category,
)

GUILD = 1543105121804615781
OTHER = 1543105121804615782
USER = 9007199254740993


async def test_panel_order_blacklist_and_queue(db_reset):
    category = await create_category(guild_id=GUILD, name="Billing", discord_category_id=None, staff_role_ids=[USER], name_format="ticket-{number}-{username}")
    panel = await create_panel(
        guild_id=GUILD,
        category_id=category["id"],
        channel_id=None,
        title="Contact us",
        message="Hello",
        button_label="Open ticket",
        button_emoji="🎫",
        button_style="secondary",
        questions=[{"label": "Order number", "kind": "short", "required": True}, {"label": "Describe the issue", "kind": "paragraph", "required": False}],
    )
    await save_panel(
        guild_id=GUILD,
        panel_id=panel["id"],
        category_id=None,
        channel_id=None,
        title="Contact us",
        message="Hello",
        button_label="Open ticket",
        button_emoji="🎫",
        button_style="secondary",
        questions=[{"label": "Describe the issue", "kind": "paragraph", "required": False}, {"label": "Order number", "kind": "short", "required": True}],
        required_role_ids=None,
        blocked_role_ids=None,
        payload=None,
    )
    loaded = await load_panel(panel["id"])
    assert [item["label"] for item in loaded["questions"]] == ["Describe the issue", "Order number"]
    assert loaded["questions"][0]["kind"] == "paragraph"
    assert loaded["button_style"] == "secondary"
    opened = await open_ticket(guild_id=GUILD, category_id=category["id"], opener_id=USER, opener_name="Aero", answers={"Order number": "100"})
    queue = await list_queue(GUILD)
    assert queue[0]["number"] == opened["number"]
    assert queue[0]["opener_name"] == "Aero"
    assert queue[0]["status"] == "open"
    assert str(queue[0]["opener_id"]) == str(USER)
    await blacklist_user(guild_id=GUILD, user_id=USER, reason="Abuse", actor_id=USER)
    blocked = await list_blacklist(GUILD)
    assert blocked[0]["reason"] == "Abuse"
    await unblacklist_user(guild_id=GUILD, user_id=USER)
    assert await list_blacklist(GUILD) == []
    try:
        await ticket_detail(OTHER, opened["id"])
        assert False, "isolation"
    except TicketError:
        pass
    updated = await update_category(guild_id=GUILD, category_id=category["id"], name="Billing desk", staff_role_ids=[USER], ping_staff=True, required_role_ids=[USER], blocked_role_ids=[])
    assert updated["name"] == "Billing desk"
    assert str(USER) in [str(item) for item in updated["staff_role_ids"]]
    limits = await set_limits(guild_id=GUILD, cooldown_seconds=30, max_open=2, auto_close_hours=24, grace_minutes=15, name_format="ticket-{number}")
    assert limits["name_format"] == "ticket-{number}"
    stored = await guild_settings(GUILD)
    assert limits["cooldown_seconds"] == 30
    assert stored["name_format"] == "ticket-{number}"
    assert stored["auto_close_hours"] == 24
    published = await set_publish(guild_id=GUILD, panel_id=panel["id"], channel_id=1555268757436371007, message_id=1555495512470331413, status="published")
    assert published["publish_status"] == "published"
    assert published["published_message_id"] == "1555495512470331413"
    await close_ticket(guild_id=GUILD, ticket_id=opened["id"], actor_id=USER, reason="Resolved from dashboard")
    transcripts = await list_transcripts(GUILD)
    assert transcripts[0]["close_reason"] == "Resolved from dashboard"
    assert transcripts[0]["opener_name"] == "Aero"
    try:
        await list_transcripts(OTHER)
    except Exception:
        raise
    assert await list_transcripts(OTHER) == []
