"""Readable HTML transcripts. User content is escaped."""

from __future__ import annotations

import html
from datetime import datetime


def _when(value) -> str:
    if isinstance(value, datetime):
        return value.strftime("%Y-%m-%d %H:%M UTC")
    return html.escape(str(value or ""))


def render_html(*, number: int, guild_name: str, category: str, opener: str, assignee: str, reason: str, opened, closed, messages: list[dict]) -> str:
    rows = []
    for message in messages:
        content = html.escape(message.get("content") or "")
        name = html.escape(message.get("display_name") or message.get("author_name") or "Member")
        avatar = html.escape(message.get("avatar") or "", quote=True)
        attachments = message.get("attachments") or []
        files = "".join(
            f'<li><a href="{html.escape(item.get("url") or "", quote=True)}">{html.escape(item.get("filename") or "attachment")}</a></li>'
            for item in attachments
            if isinstance(item, dict)
        )
        embeds = "".join(
            f'<blockquote><strong>{html.escape(item.get("title") or "")}</strong><br>{html.escape(item.get("description") or "")}</blockquote>'
            for item in (message.get("embeds") or [])
            if isinstance(item, dict)
        )
        reply = ""
        if message.get("reference_id"):
            reply = f'<p class="reply">Reply to message {html.escape(str(message["reference_id"]))}</p>'
        rows.append(
            "<article>"
            f'<img alt="" src="{avatar}">'
            f"<header><strong>{name}</strong> <time>{_when(message.get('created_at'))}</time></header>"
            f"{reply}<p>{content}</p>"
            f"{('<ul>' + files + '</ul>') if files else ''}"
            f"{embeds}</article>"
        )
    body = "\n".join(rows) or "<p>No messages were stored.</p>"
    return f"""<!DOCTYPE html>
<html><head><meta charset="utf-8"><title>Ticket {number}</title>
<style>
body {{ font-family: sans-serif; background:#1e1f22; color:#f2f3f5; }}
article {{ display:grid; grid-template-columns:40px 1fr; gap:8px; margin:12px 0; }}
img {{ width:40px; height:40px; border-radius:50%; background:#2b2d31; }}
time {{ color:#949ba4; font-size:12px; }}
a {{ color:#c4b5fd; }}
blockquote {{ margin:6px 0; padding:8px; background:#2b2d31; }}
</style></head><body>
<h1>Ticket {number}</h1>
<p>{html.escape(guild_name)} · {html.escape(category)}</p>
<p>Opened by {html.escape(opener)} · Staff {html.escape(assignee or "Unassigned")}</p>
<p>Opened {_when(opened)} · Closed {_when(closed)}</p>
<p>Reason: {html.escape(reason or "—")}</p>
{body}
</body></html>"""
