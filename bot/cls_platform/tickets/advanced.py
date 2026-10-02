"""Tickets T3. Priority, tags, notes, close requests, routing, hours, metrics, replies."""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from sqlalchemy import select

from cls_platform.database import session_scope
from cls_platform.discord_types import snowflake_to_str
from cls_platform.tickets.store import (
    Ticket,
    TicketCategory,
    TicketError,
    TicketEvent,
    TicketNote,
    TicketPanel,
    TicketPanelOption,
    TicketReply,
    TicketRoutingRule,
    TicketTag,
    TicketTagLink,
    record_event,
)

PRIORITIES = ("low", "normal", "high", "urgent")
PRIORITY_RANK = {"urgent": 0, "high": 1, "normal": 2, "low": 3}
PRIORITY_LABEL = {"low": "Low", "normal": "Normal", "high": "High", "urgent": "Urgent"}


def priority_label(value: str) -> str:
    return PRIORITY_LABEL.get(value, "Normal")


def _clock(value: str) -> tuple[int, int] | None:
    text = (value or "").strip()
    if len(text) != 5 or text[2] != ":":
        return None
    hour, minute = text[:2], text[3:]
    if not (hour.isdigit() and minute.isdigit()):
        return None
    hours, minutes = int(hour), int(minute)
    if hours > 23 or minutes > 59:
        return None
    return hours, minutes


def support_status(category: dict, now: datetime | None = None) -> dict:
    """Schedule-only. Always-open categories stay open. Invalid timezones do not block."""
    moment = now or datetime.now(timezone.utc)
    if moment.tzinfo is None:
        moment = moment.replace(tzinfo=timezone.utc)
    if (category.get("hours_mode") or "always") != "scheduled":
        return {"open": True, "notice": None, "next_open": None, "invalid_timezone": False}
    zone_name = category.get("hours_timezone") or "UTC"
    try:
        zone = ZoneInfo(zone_name)
    except ZoneInfoNotFoundError:
        return {"open": True, "notice": None, "next_open": None, "invalid_timezone": True}
    local = moment.astimezone(zone)
    start = _clock(category.get("hours_start") or "09:00")
    end = _clock(category.get("hours_end") or "17:00")
    if start is None or end is None:
        return {"open": True, "notice": None, "next_open": None, "invalid_timezone": False}
    days = int(category.get("hours_days") if category.get("hours_days") is not None else 127)
    open_now = _inside(local, days, start, end)
    nxt = None if open_now else _next_open(local, days, start)
    notice = None
    if not open_now:
        notice = "Support is currently offline."
        if nxt is not None:
            notice = f"Support is currently offline. Next opening: {nxt.strftime('%A %H:%M')} {zone_name}."
    return {"open": open_now, "notice": notice, "next_open": nxt.isoformat() if nxt else None, "invalid_timezone": False}


def _inside(local: datetime, days: int, start: tuple[int, int], end: tuple[int, int]) -> bool:
    minutes = local.hour * 60 + local.minute
    start_m = start[0] * 60 + start[1]
    end_m = end[0] * 60 + end[1]
    today = (days >> local.weekday()) & 1
    if start_m == end_m:
        return bool(today)
    if start_m < end_m:
        return bool(today) and start_m <= minutes < end_m
    yesterday = (days >> ((local.weekday() - 1) % 7)) & 1
    return (bool(today) and minutes >= start_m) or (bool(yesterday) and minutes < end_m)


def _next_open(local: datetime, days: int, start: tuple[int, int]) -> datetime | None:
    for offset in range(0, 8):
        day = local + timedelta(days=offset)
        if not ((days >> day.weekday()) & 1):
            continue
        opening = day.replace(hour=start[0], minute=start[1], second=0, microsecond=0)
        if opening > local:
            return opening
    return None


def route_category(*, rules: list[dict], answers: dict, default_category_id: str, known_category_ids: set[str]) -> tuple[str, str]:
    """Return (category_id, matched|fallback|default). Missing targets fall back to the panel category."""
    folded = {str(key).strip().lower(): str(value) for key, value in (answers or {}).items()}
    for rule in rules:
        label = str(rule.get("question_label") or "").strip().lower()
        answer = folded.get(label, "")
        expected = str(rule.get("value") or "")
        operator = rule.get("operator") or "equals"
        hit = expected.strip().lower() == answer.strip().lower() if operator != "contains" else expected.strip().lower() in answer.lower()
        if not hit or not expected.strip():
            continue
        target = str(rule.get("category_id") or "")
        if target and target in known_category_ids:
            return target, "matched"
        return default_category_id, "fallback"
    return default_category_id, "default"


def close_request_expired(requested_at: datetime | None, timeout_minutes: int | None, now: datetime) -> bool:
    if requested_at is None or not timeout_minutes or timeout_minutes <= 0:
        return False
    moment = requested_at if requested_at.tzinfo else requested_at.replace(tzinfo=timezone.utc)
    return now >= moment + timedelta(minutes=int(timeout_minutes))


def render_reply(content: str, *, number: int, opener: str) -> str:
    return (content or "").replace("{number}", str(number)).replace("{opener}", opener or "member")[:1800]


def claim_minutes(opened_at: datetime | None, claimed_at: datetime | None) -> float | None:
    if opened_at is None or claimed_at is None:
        return None
    return max(0.0, (claimed_at - opened_at).total_seconds() / 60)


def _median(values: list[float]) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    mid = len(ordered) // 2
    if len(ordered) % 2:
        return round(ordered[mid], 1)
    return round((ordered[mid - 1] + ordered[mid]) / 2, 1)


def _average(values: list[float]) -> float | None:
    if not values:
        return None
    return round(sum(values) / len(values), 1)


def summarize_metrics(tickets: list[dict], claims: list[tuple[datetime, datetime]], now: datetime, days: int) -> dict:
    """Open and unassigned are current. Today and averages use the requested window. Claim time is first claim, not first reply."""
    start = now - timedelta(days=days)
    today = now.date()

    def stamp(value):
        if value is None:
            return None
        if isinstance(value, str):
            value = datetime.fromisoformat(value)
        return value if value.tzinfo else value.replace(tzinfo=timezone.utc)

    open_rows = [row for row in tickets if row.get("raw_status") == "open" or (row.get("status") in {"open", "claimed"} and row.get("raw_status") in {None, "open"})]
    opened_window = []
    closed_window = []
    resolutions = []
    by_category: dict[str, int] = {}
    by_tag: dict[str, int] = {}
    for row in tickets:
        opened = stamp(row.get("opened_at"))
        closed = stamp(row.get("closed_at"))
        if opened and opened >= start:
            opened_window.append(row)
        if closed and closed >= start and row.get("raw_status") == "closed":
            closed_window.append(row)
            if opened:
                resolutions.append((closed - opened).total_seconds() / 60)
        if row.get("raw_status") == "open" or row.get("status") in {"open", "claimed"}:
            name = row.get("category_name") or "Uncategorized"
            by_category[name] = by_category.get(name, 0) + 1
            for tag in row.get("tags") or []:
                label = tag.get("name") or "Tag"
                by_tag[label] = by_tag.get(label, 0) + 1
    claim_values = []
    for opened_at, claimed_at in claims:
        opened = stamp(opened_at)
        claimed = stamp(claimed_at)
        if opened and claimed and claimed >= start:
            minutes = claim_minutes(opened, claimed)
            if minutes is not None:
                claim_values.append(minutes)
    return {
        "range_days": days,
        "open": len([row for row in open_rows if (row.get("raw_status") or "open") == "open"]),
        "unassigned": len([row for row in open_rows if not row.get("assignee_id") and (row.get("raw_status") or "open") == "open"]),
        "opened_today": len([row for row in tickets if stamp(row.get("opened_at")) and stamp(row.get("opened_at")).date() == today]),
        "closed_today": len([row for row in tickets if stamp(row.get("closed_at")) and stamp(row.get("closed_at")).date() == today and row.get("raw_status") == "closed"]),
        "opened_in_range": len(opened_window),
        "closed_in_range": len(closed_window),
        "median_first_claim_minutes": _median(claim_values),
        "average_first_claim_minutes": _average(claim_values),
        "average_resolution_minutes": _average(resolutions),
        "by_category": [{"name": name, "open": count} for name, count in sorted(by_category.items())],
        "by_tag": [{"name": name, "open": count} for name, count in sorted(by_tag.items())],
    }


async def tags_for(guild_id: int, ticket_ids: list[uuid.UUID]) -> dict[uuid.UUID, list[dict]]:
    if not ticket_ids:
        return {}
    async with session_scope() as session:
        rows = (
            await session.execute(select(TicketTagLink).where(TicketTagLink.ticket_id.in_(ticket_ids)))
        ).scalars().all()
        grouped: dict[uuid.UUID, list[dict]] = {}
        for row in rows:
            grouped.setdefault(row.ticket_id, []).append({"id": str(row.tag_id) if row.tag_id else None, "name": row.name})
        return grouped


async def set_priority(*, guild_id: int, ticket_id: str, priority: str, actor_id: int) -> dict:
    chosen = priority if priority in PRIORITIES else ""
    if not chosen:
        raise TicketError("priority")
    async with session_scope() as session:
        ticket = await session.get(Ticket, uuid.UUID(ticket_id))
        if ticket is None or ticket.guild_id != guild_id:
            raise TicketError("missing")
        previous = ticket.priority or "normal"
        ticket.priority = chosen
        number = ticket.number
    if previous != chosen:
        await record_event(
            guild_id=guild_id,
            ticket_id=ticket_id,
            kind="priority_changed",
            actor_id=actor_id,
            payload={"from": previous, "to": chosen, "label": f"{priority_label(previous)} → {priority_label(chosen)}"},
        )
    return {"priority": chosen, "number": number, "changed": previous != chosen, "from": previous, "to": chosen}


async def list_tags(guild_id: int) -> list[dict]:
    async with session_scope() as session:
        rows = (
            await session.execute(
                select(TicketTag).where(TicketTag.guild_id == guild_id, TicketTag.archived.is_(False)).order_by(TicketTag.position, TicketTag.name)
            )
        ).scalars().all()
        return [{"id": str(row.id), "name": row.name, "position": row.position} for row in rows]


async def save_tag(*, guild_id: int, tag_id: str | None, name: str, position: int | None = None) -> dict:
    cleaned = (name or "").strip()[:40]
    if not cleaned:
        raise TicketError("tag_name")
    async with session_scope() as session:
        if tag_id:
            row = await session.get(TicketTag, uuid.UUID(tag_id))
            if row is None or row.guild_id != guild_id:
                raise TicketError("missing")
        else:
            row = TicketTag(guild_id=guild_id, name=cleaned, position=position or 0)
            session.add(row)
        row.name = cleaned
        if position is not None:
            row.position = position
        await session.flush()
        links = (await session.execute(select(TicketTagLink).where(TicketTagLink.tag_id == row.id))).scalars().all()
        for link in links:
            link.name = cleaned
        return {"id": str(row.id), "name": row.name, "position": row.position}


async def archive_tag(*, guild_id: int, tag_id: str) -> dict:
    async with session_scope() as session:
        row = await session.get(TicketTag, uuid.UUID(tag_id))
        if row is None or row.guild_id != guild_id:
            raise TicketError("missing")
        row.archived = True
        links = (await session.execute(select(TicketTagLink).where(TicketTagLink.tag_id == row.id))).scalars().all()
        for link in links:
            link.tag_id = None
        return {"id": str(row.id), "name": row.name}


async def set_ticket_tags(*, guild_id: int, ticket_id: str, tag_ids: list[str], actor_id: int) -> list[dict]:
    async with session_scope() as session:
        ticket = await session.get(Ticket, uuid.UUID(ticket_id))
        if ticket is None or ticket.guild_id != guild_id:
            raise TicketError("missing")
        tags = (
            await session.execute(select(TicketTag).where(TicketTag.guild_id == guild_id, TicketTag.archived.is_(False)))
        ).scalars().all()
        by_id = {str(tag.id): tag for tag in tags}
        chosen = []
        for tag_id in tag_ids:
            tag = by_id.get(str(tag_id))
            if tag is None:
                raise TicketError("tag_missing")
            chosen.append(tag)
        existing = (await session.execute(select(TicketTagLink).where(TicketTagLink.ticket_id == ticket.id))).scalars().all()
        for row in existing:
            await session.delete(row)
        for tag in chosen[:8]:
            session.add(TicketTagLink(ticket_id=ticket.id, tag_id=tag.id, name=tag.name))
        await session.flush()
        names = [tag.name for tag in chosen[:8]]
    await record_event(guild_id=guild_id, ticket_id=ticket_id, kind="tags_changed", actor_id=actor_id, payload={"tags": names})
    return [{"id": str(tag.id), "name": tag.name} for tag in chosen[:8]]


async def list_notes(guild_id: int, ticket_id: str) -> list[dict]:
    async with session_scope() as session:
        ticket = await session.get(Ticket, uuid.UUID(ticket_id))
        if ticket is None or ticket.guild_id != guild_id:
            raise TicketError("missing")
        rows = (
            await session.execute(select(TicketNote).where(TicketNote.ticket_id == ticket.id, TicketNote.guild_id == guild_id).order_by(TicketNote.created_at))
        ).scalars().all()
        return [
            {"id": str(row.id), "author_id": snowflake_to_str(row.author_id), "body": row.body, "created_at": row.created_at.isoformat() if row.created_at else None}
            for row in rows
        ]


async def add_note(*, guild_id: int, ticket_id: str, author_id: int, body: str) -> dict:
    text = (body or "").strip()
    if not text:
        raise TicketError("note_empty")
    async with session_scope() as session:
        ticket = await session.get(Ticket, uuid.UUID(ticket_id))
        if ticket is None or ticket.guild_id != guild_id:
            raise TicketError("missing")
        row = TicketNote(ticket_id=ticket.id, guild_id=guild_id, author_id=author_id, body=text[:2000])
        session.add(row)
        await session.flush()
        return {"id": str(row.id), "author_id": snowflake_to_str(author_id), "body": row.body}


async def delete_note(*, guild_id: int, ticket_id: str, note_id: str, actor_id: int, allow_any: bool) -> None:
    async with session_scope() as session:
        note = await session.get(TicketNote, uuid.UUID(note_id))
        if note is None or note.guild_id != guild_id or str(note.ticket_id) != ticket_id:
            raise TicketError("missing")
        if note.author_id != actor_id and not allow_any:
            raise TicketError("note_forbidden")
        await session.delete(note)


async def mark_close_request(*, guild_id: int, ticket_id: str, actor_id: int, message: str) -> dict:
    async with session_scope() as session:
        ticket = await session.get(Ticket, uuid.UUID(ticket_id))
        if ticket is None or ticket.guild_id != guild_id or ticket.status != "open":
            raise TicketError("missing")
        category = await session.get(TicketCategory, ticket.category_id)
        ticket.close_requested_at = datetime.now(timezone.utc)
        timeout = category.close_timeout_minutes if category else None
        number = ticket.number
    await record_event(
        guild_id=guild_id,
        ticket_id=ticket_id,
        kind="close_requested",
        actor_id=actor_id,
        payload={"message": (message or "")[:300]},
    )
    return {"number": number, "timeout_minutes": timeout}


async def reject_close_request(*, guild_id: int, ticket_id: str, actor_id: int) -> None:
    async with session_scope() as session:
        ticket = await session.get(Ticket, uuid.UUID(ticket_id))
        if ticket is None or ticket.guild_id != guild_id:
            raise TicketError("missing")
        ticket.close_requested_at = None
    await record_event(guild_id=guild_id, ticket_id=ticket_id, kind="close_request_rejected", actor_id=actor_id, payload={})


async def clear_close_request(guild_id: int, ticket_id: str) -> None:
    async with session_scope() as session:
        ticket = await session.get(Ticket, uuid.UUID(ticket_id))
        if ticket is not None and ticket.guild_id == guild_id:
            ticket.close_requested_at = None


async def due_close_requests(now: datetime) -> list[dict]:
    async with session_scope() as session:
        rows = (
            await session.execute(select(Ticket, TicketCategory).join(TicketCategory, Ticket.category_id == TicketCategory.id).where(Ticket.status == "open", Ticket.close_requested_at.is_not(None)))
        ).all()
        due = []
        for ticket, category in rows:
            if close_request_expired(ticket.close_requested_at, category.close_timeout_minutes, now):
                due.append({"guild_id": ticket.guild_id, "ticket_id": str(ticket.id), "number": ticket.number})
        return due


async def save_panel_advanced(*, guild_id: int, panel_id: str, panel_type: str | None, options: list[dict] | None, rules: list[dict] | None) -> None:
    async with session_scope() as session:
        panel = await session.get(TicketPanel, uuid.UUID(panel_id))
        if panel is None or panel.guild_id != guild_id:
            raise TicketError("missing")
        if panel_type in {"button", "select"}:
            panel.panel_type = panel_type
        if options is not None:
            existing = (await session.execute(select(TicketPanelOption).where(TicketPanelOption.panel_id == panel.id))).scalars().all()
            for row in existing:
                await session.delete(row)
            for index, option in enumerate(options[:25]):
                label = str(option.get("label") or "").strip()[:80]
                if not label:
                    continue
                category_id = option.get("category_id") or None
                questions = option.get("questions") or []
                session.add(
                    TicketPanelOption(
                        panel_id=panel.id,
                        label=label,
                        description=str(option.get("description") or "")[:100],
                        emoji=str(option.get("emoji") or "")[:80],
                        category_id=uuid.UUID(str(category_id)) if category_id else None,
                        position=index,
                        questions=_option_questions(questions),
                    )
                )
        if rules is not None:
            existing_rules = (await session.execute(select(TicketRoutingRule).where(TicketRoutingRule.panel_id == panel.id))).scalars().all()
            for row in existing_rules:
                await session.delete(row)
            for index, rule in enumerate(rules[:12]):
                label = str(rule.get("question_label") or "").strip()[:80]
                value = str(rule.get("value") or "").strip()[:80]
                if not label or not value:
                    continue
                category_id = rule.get("category_id") or None
                session.add(
                    TicketRoutingRule(
                        panel_id=panel.id,
                        question_label=label,
                        operator="contains" if rule.get("operator") == "contains" else "equals",
                        value=value,
                        category_id=uuid.UUID(str(category_id)) if category_id else None,
                        position=index,
                    )
                )


def _option_questions(questions: list) -> list[dict]:
    rows = []
    for question in (questions or [])[:5]:
        kind = "paragraph" if question.get("kind") in {"long", "paragraph"} else "short"
        rows.append({"label": str(question.get("label") or "Question")[:45], "kind": kind, "required": bool(question.get("required", True)), "placeholder": str(question.get("placeholder") or "")[:100]})
    return rows


async def panel_advanced(panel_id: str) -> dict:
    async with session_scope() as session:
        panel = await session.get(TicketPanel, uuid.UUID(panel_id))
        if panel is None:
            return {"panel_type": "button", "options": [], "rules": []}
        options = (
            await session.execute(select(TicketPanelOption).where(TicketPanelOption.panel_id == panel.id).order_by(TicketPanelOption.position))
        ).scalars().all()
        rules = (
            await session.execute(select(TicketRoutingRule).where(TicketRoutingRule.panel_id == panel.id).order_by(TicketRoutingRule.position))
        ).scalars().all()
        return {
            "panel_type": panel.panel_type or "button",
            "options": [
                {
                    "id": str(row.id),
                    "label": row.label,
                    "description": row.description,
                    "emoji": row.emoji,
                    "category_id": str(row.category_id) if row.category_id else None,
                    "questions": row.questions or [],
                }
                for row in options
            ],
            "rules": [
                {
                    "id": str(row.id),
                    "question_label": row.question_label,
                    "operator": row.operator,
                    "value": row.value,
                    "category_id": str(row.category_id) if row.category_id else None,
                }
                for row in rules
            ],
        }


async def load_option(option_id: str) -> dict | None:
    async with session_scope() as session:
        row = await session.get(TicketPanelOption, uuid.UUID(option_id))
        if row is None:
            return None
        return {
            "id": str(row.id),
            "panel_id": str(row.panel_id),
            "label": row.label,
            "category_id": str(row.category_id) if row.category_id else None,
            "questions": row.questions or [],
        }


async def known_categories(guild_id: int) -> set[str]:
    async with session_scope() as session:
        rows = (await session.execute(select(TicketCategory.id).where(TicketCategory.guild_id == guild_id))).scalars().all()
        return {str(row) for row in rows}


async def category_public(guild_id: int, category_id: str) -> dict | None:
    async with session_scope() as session:
        row = await session.get(TicketCategory, uuid.UUID(category_id))
        if row is None or row.guild_id != guild_id:
            return None
        return {
            "id": str(row.id),
            "name": row.name,
            "hours_mode": row.hours_mode,
            "hours_timezone": row.hours_timezone,
            "hours_days": row.hours_days,
            "hours_start": row.hours_start,
            "hours_end": row.hours_end,
            "hours_outside": row.hours_outside,
            "close_mode": row.close_mode,
            "close_timeout_minutes": row.close_timeout_minutes,
            "discord_category_id": row.discord_category_id,
            "staff_role_ids": list(row.staff_role_ids or []),
        }


async def metrics(guild_id: int, now: datetime, days: int) -> dict:
    async with session_scope() as session:
        tickets = (await session.execute(select(Ticket).where(Ticket.guild_id == guild_id))).scalars().all()
        categories = {row.id: row.name for row in (await session.execute(select(TicketCategory).where(TicketCategory.guild_id == guild_id))).scalars().all()}
        events = (
            await session.execute(select(TicketEvent).where(TicketEvent.guild_id == guild_id, TicketEvent.kind == "claimed"))
        ).scalars().all()
        links = (await session.execute(select(TicketTagLink).where(TicketTagLink.ticket_id.in_([row.id for row in tickets] or [uuid.uuid4()])))).scalars().all()
    by_ticket: dict[uuid.UUID, list[dict]] = {}
    for link in links:
        by_ticket.setdefault(link.ticket_id, []).append({"name": link.name})
    opened = {row.id: row.opened_at for row in tickets}
    claims = [(opened.get(event.ticket_id), event.created_at) for event in events if event.ticket_id in opened]
    rows = [
        {
            "raw_status": row.status,
            "status": "claimed" if row.status == "open" and row.assignee_id else row.status,
            "assignee_id": row.assignee_id,
            "opened_at": row.opened_at,
            "closed_at": row.closed_at,
            "category_name": categories.get(row.category_id) or "",
            "tags": by_ticket.get(row.id, []),
        }
        for row in tickets
    ]
    return summarize_metrics(rows, claims, now, days)


async def list_replies(guild_id: int) -> list[dict]:
    async with session_scope() as session:
        rows = (await session.execute(select(TicketReply).where(TicketReply.guild_id == guild_id).order_by(TicketReply.position, TicketReply.name))).scalars().all()
        return [{"id": str(row.id), "name": row.name, "content": row.content} for row in rows]


async def save_reply(*, guild_id: int, reply_id: str | None, name: str, content: str) -> dict:
    cleaned = (name or "").strip()[:80]
    body = (content or "").strip()
    if not cleaned or not body:
        raise TicketError("reply")
    async with session_scope() as session:
        if reply_id:
            row = await session.get(TicketReply, uuid.UUID(reply_id))
            if row is None or row.guild_id != guild_id:
                raise TicketError("missing")
        else:
            row = TicketReply(guild_id=guild_id, name=cleaned, content=body[:1800])
            session.add(row)
        row.name = cleaned
        row.content = body[:1800]
        await session.flush()
        return {"id": str(row.id), "name": row.name, "content": row.content}


async def delete_reply(*, guild_id: int, reply_id: str) -> None:
    async with session_scope() as session:
        row = await session.get(TicketReply, uuid.UUID(reply_id))
        if row is None or row.guild_id != guild_id:
            raise TicketError("missing")
        await session.delete(row)
