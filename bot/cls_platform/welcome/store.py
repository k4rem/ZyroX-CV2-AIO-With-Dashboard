"""Welcome storage. Existing rows stay readable; saves use the shared message payload."""

from __future__ import annotations

import json
import os

import aiosqlite

WELCOME_DB = os.environ.get("WELCOME_DB", "db/welcome.db")
JOINDM_PATH = os.environ.get("JOINDM_PATH", "jsondb/joindm_messages.json")

WELCOME_VARIABLES = (
    "user",
    "user_avatar",
    "user_name",
    "user_id",
    "user_nick",
    "user_joindate",
    "user_createdate",
    "server_name",
    "server_id",
    "server_membercount",
    "server_icon",
    "timestamp",
)
# After a member leaves, a mention is not reliable. Everything else is on the leave event.
GOODBYE_VARIABLES = tuple(item for item in WELCOME_VARIABLES if item != "user")

EMPTY_PAYLOAD = {
    "content": "",
    "embeds": [
        {
            "title": "",
            "url": None,
            "description": "",
            "color": "#9474ff",
            "author": {"name": "", "url": None, "icon": None},
            "thumbnail": None,
            "image": None,
            "fields": [],
            "footer": {"text": "", "icon": None},
            "timestamp": False,
        }
    ],
    "buttons": [],
}


def _url(value) -> dict | None:
    if not isinstance(value, str) or not value.startswith("https://"):
        return None
    return {"kind": "url", "value": value}


def legacy_to_payload(welcome_type: str | None, welcome_message: str | None, embed_data) -> dict:
    """Turn a pre-composer welcome row into the shared payload."""
    if isinstance(embed_data, str):
        try:
            embed_data = json.loads(embed_data)
        except json.JSONDecodeError:
            embed_data = None
    if isinstance(embed_data, dict) and embed_data.get("v") == 2 and isinstance(embed_data.get("payload"), dict):
        return embed_data["payload"]
    if welcome_type != "embed" or not isinstance(embed_data, dict):
        return {**EMPTY_PAYLOAD, "content": welcome_message or "", "embeds": []}
    color = embed_data.get("color") if isinstance(embed_data.get("color"), str) else ""
    if not color.startswith("#"):
        color = "#2f3136"
    return {
        "content": embed_data.get("message") or welcome_message or "",
        "embeds": [
            {
                "title": embed_data.get("title") or "",
                "url": None,
                "description": embed_data.get("description") or "",
                "color": color,
                "author": {
                    "name": embed_data.get("author_name") or "",
                    "url": None,
                    "icon": _url(embed_data.get("author_icon")),
                },
                "thumbnail": _url(embed_data.get("thumbnail")),
                "image": _url(embed_data.get("image")),
                "fields": [],
                "footer": {
                    "text": embed_data.get("footer_text") or "",
                    "icon": _url(embed_data.get("footer_icon")),
                },
                "timestamp": True,
            }
        ],
        "buttons": [],
    }


def member_values(member, guild) -> dict[str, str]:
    """Values available on the member object without another Discord fetch."""
    avatar = ""
    display_avatar = getattr(member, "display_avatar", None)
    if display_avatar is not None:
        avatar = str(display_avatar.url)
    elif getattr(member, "avatar", None) is not None:
        avatar = str(member.avatar.url)
    joined = getattr(member, "joined_at", None)
    created = getattr(member, "created_at", None)
    icon = ""
    if getattr(guild, "icon", None) is not None:
        icon = str(guild.icon.url)
    import discord

    now = discord.utils.format_dt(discord.utils.utcnow())
    return {
        "user": member.mention,
        "user_avatar": avatar,
        "user_name": str(getattr(member, "name", "") or ""),
        "user_id": str(member.id),
        "user_nick": str(getattr(member, "display_name", "") or getattr(member, "name", "") or ""),
        "user_joindate": joined.strftime("%a, %b %d, %Y") if joined else "",
        "user_createdate": created.strftime("%a, %b %d, %Y") if created else "",
        "server_name": str(getattr(guild, "name", "") or ""),
        "server_id": str(guild.id),
        "server_membercount": str(getattr(guild, "member_count", "") or ""),
        "server_icon": icon,
        "timestamp": now,
    }


def preview_values(values: dict[str, str]) -> dict[str, str]:
    """Show a mention the way Discord does, without changing the sent payload."""
    shown = dict(values)
    nick = values.get("user_nick") or values.get("user_name") or "member"
    shown["user"] = f"@{nick}"
    return shown


async def _ensure():
    os.makedirs(os.path.dirname(WELCOME_DB) or ".", exist_ok=True)
    async with aiosqlite.connect(WELCOME_DB) as db:
        await db.execute(
            """
            CREATE TABLE IF NOT EXISTS welcome (
                guild_id INTEGER PRIMARY KEY,
                welcome_type TEXT,
                welcome_message TEXT,
                channel_id INTEGER,
                embed_data TEXT,
                auto_delete_duration INTEGER
            )
            """
        )
        await db.execute(
            """
            CREATE TABLE IF NOT EXISTS goodbye (
                guild_id INTEGER PRIMARY KEY,
                enabled INTEGER NOT NULL DEFAULT 0,
                channel_id INTEGER,
                payload TEXT,
                skip_bots INTEGER NOT NULL DEFAULT 0
            )
            """
        )
        await db.commit()


def _channel_record(row) -> dict:
    if row is None:
        return {
            "enabled": False,
            "skip_bots": False,
            "channel_id": None,
            "auto_delete_duration": None,
            "payload": json.loads(json.dumps(EMPTY_PAYLOAD)),
        }
    welcome_type, welcome_message, channel_id, embed_data, auto_delete = row
    parsed = None
    if embed_data:
        try:
            parsed = json.loads(embed_data)
        except json.JSONDecodeError:
            parsed = None
    if isinstance(parsed, dict) and parsed.get("v") == 2:
        return {
            "enabled": bool(parsed.get("enabled")),
            "skip_bots": bool(parsed.get("skip_bots")),
            "channel_id": str(channel_id) if channel_id else None,
            "auto_delete_duration": auto_delete,
            "payload": parsed.get("payload") or json.loads(json.dumps(EMPTY_PAYLOAD)),
        }
    return {
        "enabled": bool(channel_id),
        "skip_bots": False,
        "channel_id": str(channel_id) if channel_id else None,
        "auto_delete_duration": auto_delete,
        "payload": legacy_to_payload(welcome_type, welcome_message, parsed),
    }


async def read_channel(guild_id: int) -> dict:
    await _ensure()
    async with aiosqlite.connect(WELCOME_DB) as db:
        async with db.execute(
            "SELECT welcome_type, welcome_message, channel_id, embed_data, auto_delete_duration FROM welcome WHERE guild_id = ?",
            (guild_id,),
        ) as cursor:
            row = await cursor.fetchone()
    return _channel_record(row)


async def write_channel(guild_id: int, *, enabled: bool, skip_bots: bool, channel_id: int | None, auto_delete_duration: int | None, payload: dict) -> dict:
    await _ensure()
    wrapper = json.dumps({"v": 2, "enabled": enabled, "skip_bots": skip_bots, "payload": payload})
    content = payload.get("content") or ""
    async with aiosqlite.connect(WELCOME_DB) as db:
        await db.execute(
            """
            INSERT INTO welcome (guild_id, welcome_type, welcome_message, channel_id, embed_data, auto_delete_duration)
            VALUES (?, 'composer', ?, ?, ?, ?)
            ON CONFLICT(guild_id) DO UPDATE SET
                welcome_type = 'composer',
                welcome_message = excluded.welcome_message,
                channel_id = excluded.channel_id,
                embed_data = excluded.embed_data,
                auto_delete_duration = excluded.auto_delete_duration
            """,
            (guild_id, content, channel_id, wrapper, auto_delete_duration),
        )
        await db.commit()
    return await read_channel(guild_id)


def _read_joindm_file() -> dict:
    if not os.path.exists(JOINDM_PATH):
        return {}
    try:
        with open(JOINDM_PATH, "r", encoding="utf-8") as handle:
            data = json.load(handle)
    except (OSError, json.JSONDecodeError):
        return {}
    return data if isinstance(data, dict) else {}


def _write_joindm_file(data: dict) -> None:
    folder = os.path.dirname(JOINDM_PATH)
    if folder:
        os.makedirs(folder, exist_ok=True)
    with open(JOINDM_PATH, "w", encoding="utf-8") as handle:
        json.dump(data, handle, indent=2)


def normalize_dm(raw) -> dict:
    if isinstance(raw, str):
        return {"enabled": bool(raw.strip()), "payload": {**EMPTY_PAYLOAD, "content": raw, "embeds": []}}
    if isinstance(raw, dict) and isinstance(raw.get("payload"), dict):
        return {"enabled": bool(raw.get("enabled")), "payload": raw["payload"]}
    return {"enabled": False, "payload": json.loads(json.dumps(EMPTY_PAYLOAD))}


def read_dm(guild_id: int) -> dict:
    return normalize_dm(_read_joindm_file().get(str(guild_id)))


def write_dm(guild_id: int, *, enabled: bool, payload: dict) -> dict:
    data = _read_joindm_file()
    data[str(guild_id)] = {"enabled": enabled, "payload": payload}
    _write_joindm_file(data)
    return read_dm(guild_id)


async def read_goodbye(guild_id: int) -> dict:
    await _ensure()
    async with aiosqlite.connect(WELCOME_DB) as db:
        async with db.execute("SELECT enabled, channel_id, payload, skip_bots FROM goodbye WHERE guild_id = ?", (guild_id,)) as cursor:
            row = await cursor.fetchone()
    if row is None:
        return {
            "enabled": False,
            "skip_bots": False,
            "channel_id": None,
            "payload": json.loads(json.dumps(EMPTY_PAYLOAD)),
        }
    try:
        payload = json.loads(row[2]) if row[2] else json.loads(json.dumps(EMPTY_PAYLOAD))
    except json.JSONDecodeError:
        payload = json.loads(json.dumps(EMPTY_PAYLOAD))
    return {
        "enabled": bool(row[0]),
        "channel_id": str(row[1]) if row[1] else None,
        "payload": payload,
        "skip_bots": bool(row[3]),
    }


async def write_goodbye(guild_id: int, *, enabled: bool, skip_bots: bool, channel_id: int | None, payload: dict) -> dict:
    await _ensure()
    async with aiosqlite.connect(WELCOME_DB) as db:
        await db.execute(
            """
            INSERT INTO goodbye (guild_id, enabled, channel_id, payload, skip_bots)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(guild_id) DO UPDATE SET
                enabled = excluded.enabled,
                channel_id = excluded.channel_id,
                payload = excluded.payload,
                skip_bots = excluded.skip_bots
            """,
            (guild_id, int(enabled), channel_id, json.dumps(payload), int(skip_bots)),
        )
        await db.commit()
    return await read_goodbye(guild_id)
