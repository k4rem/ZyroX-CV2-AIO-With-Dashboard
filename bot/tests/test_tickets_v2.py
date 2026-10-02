"""Ticket open, duplicate guard, claim, close, transcript, guild isolation."""

from cls_platform.tickets.store import (
    TicketError,
    claim_ticket,
    close_ticket,
    create_category,
    create_panel,
    open_ticket,
    panel_preview,
    reopen_ticket,
    transcript,
    workspace,
    add_transcript,
    blacklist_user,
    set_limits,
)

GUILD = 100000000000000100
OTHER = 100000000000000200
USER = 9007199254740993


def test_preview_uses_panel_button():
    preview = panel_preview("Help", "Describe the issue", "Open", "abc")
    assert preview["components"][0]["custom_id"] == "cls-ticket:abc"
    assert "Describe the issue" in preview["message"]


async def test_ticket_flow_and_isolation(db_reset):
    category = await create_category(guild_id=GUILD, name="Support", discord_category_id=USER, staff_role_ids=[USER + 1])
    panel = await create_panel(
        guild_id=GUILD,
        category_id=category["id"],
        channel_id=USER + 2,
        title="Support",
        message="Tell us what happened.",
        button_label="Open",
        questions=[{"label": "What happened?", "kind": "long", "required": True}],
    )
    assert panel["preview"]["title"] == "Support"
    opened = await open_ticket(guild_id=GUILD, category_id=category["id"], opener_id=USER, answers={"What happened?": "login"})
    assert opened["name"] == "ticket-1"
    try:
        await open_ticket(guild_id=GUILD, category_id=category["id"], opener_id=USER)
        assert False, "duplicate should fail"
    except TicketError as exc:
        assert str(exc) == "duplicate_open"
    claimed = await claim_ticket(guild_id=GUILD, ticket_id=opened["id"], actor_id=USER + 5)
    assert claimed["assignee_id"] == str(USER + 5)
    await add_transcript(guild_id=GUILD, ticket_id=opened["id"], author_id=USER + 5, body="Looking now")
    try:
        await close_ticket(guild_id=GUILD, ticket_id=opened["id"], actor_id=USER + 5, reason="  ")
        assert False, "reason required"
    except TicketError:
        pass
    closed = await close_ticket(guild_id=GUILD, ticket_id=opened["id"], actor_id=USER + 5, reason="fixed")
    assert closed["status"] == "closed"
    reopened = await reopen_ticket(guild_id=GUILD, ticket_id=opened["id"], actor_id=USER + 5)
    assert reopened["status"] == "open"
    body = await transcript(guild_id=GUILD, ticket_id=opened["id"])
    assert any("login" in line["body"] for line in body["lines"])
    summary = await workspace(GUILD)
    assert summary["open_now"] == 1
    other = await workspace(OTHER)
    assert other["opened"] == 0
    try:
        await transcript(OTHER, opened["id"])
        assert False, "cross guild"
    except TicketError:
        pass
    await close_ticket(guild_id=GUILD, ticket_id=opened["id"], actor_id=USER + 5, reason="done")
    await set_limits(guild_id=GUILD, cooldown_seconds=3600, max_open=1)
    try:
        await open_ticket(guild_id=GUILD, category_id=category["id"], opener_id=USER)
        assert False, "cooldown"
    except TicketError as exc:
        assert str(exc) == "cooldown"
    await set_limits(guild_id=GUILD, cooldown_seconds=0, max_open=1)
    second = await create_category(guild_id=GUILD, name="Billing", discord_category_id=None, staff_role_ids=[])
    again = await open_ticket(guild_id=GUILD, category_id=second["id"], opener_id=USER + 9)
    try:
        await open_ticket(guild_id=GUILD, category_id=category["id"], opener_id=USER + 9)
        assert False, "max open"
    except TicketError as exc:
        assert str(exc) == "max_open"
    await blacklist_user(guild_id=GUILD, user_id=USER + 8)
    try:
        await open_ticket(guild_id=GUILD, category_id=category["id"], opener_id=USER + 8)
        assert False, "blacklist"
    except TicketError as exc:
        assert str(exc) == "blacklisted"
    assert again["status"] == "open"
    await claim_ticket(guild_id=GUILD, ticket_id=again["id"], actor_id=USER)
    try:
        await claim_ticket(guild_id=GUILD, ticket_id=again["id"], actor_id=USER + 3)
        assert False, "second claim"
    except TicketError as exc:
        assert str(exc) == "already_claimed"
