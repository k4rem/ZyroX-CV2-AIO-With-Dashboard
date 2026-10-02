"""Read and write portable module configuration. History and secrets stay out."""

from __future__ import annotations

import aiosqlite

from cls_platform.commands.policy import policies_for, set_policy
from cls_platform.config_transfer.schema import ref, scrub_private_media, strip_secrets
from cls_platform.database import session_scope
from cls_platform.logging.store import appearance_for, event_routes, ignores_public, routes, set_appearance, set_event_route, set_ignores, set_route
from cls_platform.messages.store import create_template, delete_template, list_templates, update_template
from cls_platform.role_automation.store import create_rule, delete_rule, get_join, list_rules, save_join, update_rule
from cls_platform.role_menus.store import create_menu, delete_menu, list_menus, update_menu
from cls_platform.tickets.store import TicketPanel, TicketQuestion, create_category, create_panel, delete_panel, guild_settings, save_panel, set_limits, update_category, workspace
from sqlalchemy import select


def _name(lookup, kind: str, source_id) -> str:
    if lookup is None or not source_id:
        return ""
    return lookup(kind, str(source_id)) or ""


def _role(lookup, source_id):
    return ref("role", source_id, _name(lookup, "role", source_id))


def _channel(lookup, source_id):
    return ref("channel", source_id, _name(lookup, "channel", source_id))


def _category(lookup, source_id):
    return ref("category", source_id, _name(lookup, "category", source_id))


def _roles(lookup, values):
    return [item for item in (_role(lookup, value) for value in values or []) if item]


async def export_module(guild_id: int, module_id: str, lookup) -> dict:
    exporter = EXPORTERS[module_id]
    body = await exporter(guild_id, lookup)
    return strip_secrets(body)


async def export_welcome(guild_id: int, lookup) -> dict:
    from cls_platform.welcome.store import read_channel

    row = await read_channel(guild_id)
    return {
        "enabled": row["enabled"],
        "skip_bots": row["skip_bots"],
        "channel": _channel(lookup, row.get("channel_id")),
        "auto_delete_duration": row.get("auto_delete_duration"),
        "payload": row.get("payload") or {},
    }


async def export_dm(guild_id: int, lookup) -> dict:
    from cls_platform.welcome.store import read_dm

    row = read_dm(guild_id)
    return {"enabled": row["enabled"], "payload": row.get("payload") or {}}


async def export_goodbye(guild_id: int, lookup) -> dict:
    from cls_platform.welcome.store import read_goodbye

    row = await read_goodbye(guild_id)
    return {
        "enabled": row["enabled"],
        "skip_bots": row["skip_bots"],
        "channel": _channel(lookup, row.get("channel_id")),
        "payload": row.get("payload") or {},
    }


async def export_messages(guild_id: int, lookup) -> dict:
    templates = []
    for row in await list_templates(guild_id):
        templates.append({"name": row["name"], "payload": row["payload"]})
    return {"templates": templates}


async def export_logging(guild_id: int, lookup) -> dict:
    ignored = await ignores_public(guild_id)
    return {
        "routes": [
            {"category": row["category"], "enabled": row["enabled"], "channel": _channel(lookup, row.get("channel_id"))}
            for row in await routes(guild_id)
        ],
        "event_routes": [
            {"event_type": row["event_type"], "mode": row["mode"], "channel": _channel(lookup, row.get("channel_id"))}
            for row in await event_routes(guild_id)
        ],
        "appearance": await appearance_for(guild_id),
        "ignored_channels": _roles(lookup, []) or [_channel(lookup, item) for item in ignored.get("channels") or [] if _channel(lookup, item)],
        "ignored_roles": [item for item in (_role(lookup, value) for value in ignored.get("roles") or []) if item],
        "ignored_members": [str(item) for item in ignored.get("users") or []],
    }


async def export_tickets(guild_id: int, lookup) -> dict:
    home = await workspace(guild_id)
    settings = await guild_settings(guild_id)
    panels = []
    async with session_scope() as session:
        rows = (await session.execute(select(TicketPanel).where(TicketPanel.guild_id == guild_id))).scalars().all()
        for row in rows:
            questions = (await session.execute(select(TicketQuestion).where(TicketQuestion.panel_id == row.id).order_by(TicketQuestion.position))).scalars().all()
            panels.append({
                "title": row.title,
                "message": row.message,
                "button_label": row.button_label,
                "button_emoji": row.button_emoji or "",
                "button_style": row.button_style or "primary",
                "category_name": next((item["name"] for item in home["categories"] if item["id"] == str(row.category_id)), ""),
                "channel": _channel(lookup, row.channel_id),
                "publication": {"channel": _channel(lookup, row.channel_id), "message_id": str(row.published_message_id) if row.published_message_id else None, "status": row.publish_status},
                "required_roles": _roles(lookup, row.required_role_ids),
                "blocked_roles": _roles(lookup, row.blocked_role_ids),
                "payload": row.payload,
                "questions": [{"label": item.label, "kind": item.kind, "required": item.required, "placeholder": item.placeholder or "", "min_length": item.min_length or 0, "max_length": item.max_length or 1000} for item in questions],
            })
    return {
        "settings": {
            "cooldown_seconds": home["cooldown_seconds"],
            "max_open": home["max_open"],
            "auto_close_hours": settings["auto_close_hours"],
            "grace_minutes": settings["grace_minutes"],
            "transcript_channel": _channel(lookup, settings.get("transcript_channel_id")),
            "name_format": settings["name_format"],
        },
        "categories": [
            {
                "name": row["name"],
                "discord_category": _category(lookup, row.get("discord_category_id")),
                "staff_roles": _roles(lookup, row.get("staff_role_ids")),
                "required_roles": _roles(lookup, row.get("required_role_ids")),
                "blocked_roles": _roles(lookup, row.get("blocked_role_ids")),
                "name_format": row.get("name_format"),
                "ping_staff": row.get("ping_staff", True),
            }
            for row in home["categories"]
        ],
        "panels": panels,
    }


async def export_menus(guild_id: int, lookup) -> dict:
    menus = []
    for row in await list_menus(guild_id):
        menus.append({
            "name": row["name"],
            "source": row["source"],
            "type": row["type"],
            "mode": row["mode"],
            "button_style": row["button_style"],
            "enabled": row["enabled"],
            "max_roles": row["max_roles"],
            "channel": _channel(lookup, row.get("channel_id")),
            "payload": row.get("payload"),
            "publication": {"message_id": row.get("message_id"), "status": row.get("publish_status")},
            "options": [
                {"role": _role(lookup, option["role_id"]), "emoji": option["emoji"], "label": option["label"], "description": option["description"]}
                for option in row.get("options") or []
            ],
        })
    return {"menus": menus}


async def export_join(guild_id: int, lookup) -> dict:
    row = await get_join(guild_id)
    return {
        "member_roles": _roles(lookup, row["member_role_ids"]),
        "bot_roles": _roles(lookup, row["bot_role_ids"]),
        "delay_seconds": row["delay_seconds"],
        "screening": row["screening"],
    }


async def export_rules(guild_id: int, lookup) -> dict:
    rules = []
    for row in await list_rules(guild_id):
        conditions = []
        for condition in row["conditions"] or []:
            item = dict(condition)
            if item.get("kind") in {"has_role", "lacks_role"}:
                item["role"] = _role(lookup, item.pop("role_id", None))
            conditions.append(item)
        rules.append({
            "name": row["name"],
            "trigger": row["trigger"],
            "trigger_role": _role(lookup, row.get("trigger_role_id")),
            "conditions": conditions,
            "action": row["action"],
            "action_role": _role(lookup, row["action_role_id"]),
            "delay_seconds": row["delay_seconds"],
            "enabled": row["enabled"],
        })
    return {"rules": rules}


async def export_commands(guild_id: int, lookup) -> dict:
    policies = await policies_for(guild_id)
    return {
        "policies": [
            {
                "command": name,
                "enabled": row["enabled"],
                "allowed_roles": _roles(lookup, row.get("allowed_role_ids")),
                "blocked_roles": _roles(lookup, row.get("blocked_role_ids")),
                "allowed_channels": [_channel(lookup, item) for item in (row.get("allowed_channel_ids") or [])],
                "blocked_channels": [_channel(lookup, item) for item in (row.get("blocked_channel_ids") or [])],
            }
            for name, row in policies.items()
        ]
    }


async def export_automod(guild_id: int, lookup) -> dict:
    from cls_platform.automod.store import get_config

    config = await get_config(guild_id)
    if config.get("schema_version") == 2 and (config.get("migrated") or config.get("enabled") or any(rule.get("enabled") for rule in config.get("rules") or [])):
        return {
            "schema_version": 2,
            "enabled": config["enabled"],
            "preset": config["preset"],
            "exclusions": config["exclusions"],
            "escalations": config["escalations"],
            "strike_ttl_seconds": config["strike_ttl_seconds"],
            "rules": config["rules"],
        }
    try:
        async with aiosqlite.connect("db/automod.db") as db:
            enabled = await (await db.execute("SELECT enabled FROM automod WHERE guild_id = ?", (guild_id,))).fetchone()
            punishments = await (await db.execute("SELECT event, punishment FROM automod_punishments WHERE guild_id = ?", (guild_id,))).fetchall()
            ignored = await (await db.execute("SELECT type, id FROM automod_ignored WHERE guild_id = ?", (guild_id,))).fetchall()
            log_row = await (await db.execute("SELECT log_channel FROM automod_logging WHERE guild_id = ?", (guild_id,))).fetchone()
    except Exception:
        return {"enabled": False, "punishments": [], "ignored_roles": [], "ignored_channels": [], "log_channel": None}
    return {
        "enabled": bool(enabled[0]) if enabled else False,
        "punishments": [{"event": row[0], "punishment": row[1]} for row in punishments],
        "ignored_roles": [item for item in (_role(lookup, row[1]) for row in ignored if row[0] == "role") if item],
        "ignored_channels": [item for item in (_channel(lookup, row[1]) for row in ignored if row[0] == "channel") if item],
        "log_channel": _channel(lookup, log_row[0] if log_row else None),
    }


async def export_j2c(guild_id: int, lookup) -> dict:
    try:
        async with aiosqlite.connect("j2c_data.db") as db:
            row = await (await db.execute("SELECT join_channel_id, control_channel_id, category_id, COALESCE(enabled, 1) FROM guild_setup WHERE guild_id = ?", (guild_id,))).fetchone()
    except Exception:
        return {"enabled": False, "join_channel": None, "control_channel": None, "category": None}
    if row is None:
        return {"enabled": False, "join_channel": None, "control_channel": None, "category": None}
    return {
        "enabled": bool(row[3]),
        "join_channel": _channel(lookup, row[0]),
        "control_channel": _channel(lookup, row[1]),
        "category": _category(lookup, row[2]),
    }


async def export_autoreact(guild_id: int, lookup) -> dict:
    try:
        async with aiosqlite.connect("db/autoreact.db") as db:
            rows = await (await db.execute("SELECT trigger, emojis FROM autoreact WHERE guild_id = ?", (guild_id,))).fetchall()
    except Exception:
        return {"triggers": []}
    return {"triggers": [{"trigger": row[0], "emojis": row[1]} for row in rows]}


def _id(value) -> int | None:
    text = str(value or "")
    return int(text) if text.isdigit() else None


def _id_list(values) -> list[int]:
    return [int(item) for item in values or [] if str(item).isdigit()]


def _ref_ids(values) -> list[str]:
    found = []
    for item in values or []:
        text = str(item.get("id") if isinstance(item, dict) else item)
        if text.isdigit():
            found.append(text)
    return found


def summary_of(module_id: str, body: dict) -> str:
    if module_id == "automod":
        rules = [row for row in body.get("rules") or [] if row.get("enabled")]
        if rules:
            return f"{len(rules)} rules"
        return "Configured" if body.get("enabled") or body.get("punishments") else "Not configured"
    if module_id in {"welcome", "welcome_dm", "goodbye", "j2c"}:
        return "Configured" if body.get("enabled") or body.get("channel") or body.get("payload", {}).get("content") or body.get("punishments") or body.get("join_channel") else "Not configured"
    if module_id == "messages":
        count = len(body.get("templates") or [])
        return f"{count} templates" if count else "No templates"
    if module_id == "logging":
        enabled = len([row for row in body.get("routes") or [] if row.get("enabled")])
        return f"{enabled} routes" if enabled else "Not configured"
    if module_id == "tickets":
        return f"{len(body.get('panels') or [])} panels · {len(body.get('categories') or [])} teams"
    if module_id == "role_menus":
        count = len(body.get("menus") or [])
        return f"{count} menus" if count else "No menus"
    if module_id == "role_automation":
        count = len(body.get("rules") or [])
        return f"{count} rules" if count else "No rules"
    if module_id == "join_roles":
        count = len(body.get("member_roles") or []) + len(body.get("bot_roles") or [])
        return f"{count} roles" if count else "Not configured"
    if module_id == "commands":
        count = len(body.get("policies") or [])
        return f"{count} commands" if count else "Default"
    if module_id == "autoreact":
        count = len(body.get("triggers") or [])
        return f"{count} triggers" if count else "Not configured"
    return "Configured"


async def apply_module(guild_id: int, module_id: str, body: dict, *, same_guild: bool, known_messages: set[str], strategy: str) -> None:
    notes: list[str] = []
    cleaned = scrub_private_media(body, cross_guild=not same_guild, notes=notes)
    await APPLIERS[module_id](guild_id, cleaned, same_guild=same_guild, known_messages=known_messages, strategy=strategy)


async def apply_welcome(guild_id, body, **_):
    from cls_platform.welcome.store import write_channel

    channel = _id(body.get("channel"))
    await write_channel(guild_id, enabled=bool(body.get("enabled")) and channel is not None, skip_bots=bool(body.get("skip_bots")), channel_id=channel, auto_delete_duration=body.get("auto_delete_duration"), payload=body.get("payload") or {})


async def apply_dm(guild_id, body, **_):
    from cls_platform.welcome.store import write_dm

    write_dm(guild_id, enabled=bool(body.get("enabled")), payload=body.get("payload") or {})


async def apply_goodbye(guild_id, body, **_):
    from cls_platform.welcome.store import write_goodbye

    channel = _id(body.get("channel"))
    await write_goodbye(guild_id, enabled=bool(body.get("enabled")) and channel is not None, skip_bots=bool(body.get("skip_bots")), channel_id=channel, payload=body.get("payload") or {})


async def apply_messages(guild_id, body, *, strategy: str, **_):
    current = {row["name"]: row for row in await list_templates(guild_id)}
    incoming = body.get("templates") or []
    names = {item["name"] for item in incoming}
    for item in incoming:
        existing = current.get(item["name"])
        if existing:
            await update_template(guild_id=guild_id, template_id=existing["id"], name=item["name"], payload=item.get("payload") or {})
        else:
            await create_template(guild_id=guild_id, name=item["name"], payload=item.get("payload") or {"content": "", "embeds": [], "buttons": []}, created_by=None)
    if strategy == "replace":
        for name, row in current.items():
            if name not in names:
                await delete_template(guild_id, row["id"])


async def apply_logging(guild_id, body, *, same_guild: bool, **_):
    for row in body.get("routes") or []:
        channel = _id(row.get("channel"))
        enabled = bool(row.get("enabled")) and (channel is not None or not row.get("enabled"))
        if row.get("enabled") and channel is None:
            enabled = False
        await set_route(guild_id=guild_id, category=row["category"], enabled=enabled, channel_id=channel)
    for row in body.get("event_routes") or []:
        mode = row.get("mode") or "inherit"
        channel = _id(row.get("channel"))
        if mode == "custom" and channel is None:
            mode = "inherit"
            channel = None
        await set_event_route(guild_id=guild_id, event_type=row["event_type"], mode=mode, channel_id=channel)
    if isinstance(body.get("appearance"), dict):
        await set_appearance(guild_id, body["appearance"])
    members = [int(item) for item in body.get("ignored_members") or [] if str(item).isdigit()] if same_guild else []
    await set_ignores(guild_id=guild_id, channels=_id_list(body.get("ignored_channels")), roles=_id_list(body.get("ignored_roles")), users=members)


async def apply_tickets(guild_id, body, *, same_guild: bool, known_messages: set[str], strategy: str, **_):
    home = await workspace(guild_id)
    by_name = {row["name"]: row for row in home["categories"]}
    for row in body.get("categories") or []:
        staff = _id_list(row.get("staff_roles"))
        required = _id_list(row.get("required_roles"))
        blocked = _id_list(row.get("blocked_roles"))
        category = _id(row.get("discord_category"))
        existing = by_name.get(row["name"])
        if existing:
            await update_category(guild_id=guild_id, category_id=existing["id"], name=row["name"], discord_category_id=category, staff_role_ids=staff, name_format=row.get("name_format"), ping_staff=bool(row.get("ping_staff", True)), required_role_ids=required, blocked_role_ids=blocked, discord_category_set=True)
        else:
            created = await create_category(guild_id=guild_id, name=row["name"], discord_category_id=category, staff_role_ids=staff, name_format=row.get("name_format"), ping_staff=bool(row.get("ping_staff", True)), required_role_ids=required, blocked_role_ids=blocked)
            by_name[row["name"]] = created
    settings = body.get("settings") or {}
    await set_limits(guild_id=guild_id, cooldown_seconds=int(settings.get("cooldown_seconds") or 60), max_open=int(settings.get("max_open") or 1), auto_close_hours=settings.get("auto_close_hours"), grace_minutes=settings.get("grace_minutes"), transcript_channel_id=_id(settings.get("transcript_channel")), name_format=settings.get("name_format"))
    current_panels = {row["title"]: row for row in home["panels"]}
    seen = set()
    for row in body.get("panels") or []:
        seen.add(row["title"])
        team = by_name.get(row.get("category_name") or "")
        if team is None:
            continue
        channel = _id(row.get("channel"))
        publication = row.get("publication") or {}
        message_id = publication.get("message_id") if same_guild and str(publication.get("message_id") or "") in known_messages else None
        existing = current_panels.get(row["title"])
        if existing:
            await save_panel(guild_id=guild_id, panel_id=existing["id"], category_id=team["id"], channel_id=channel, title=row["title"], message=row.get("message"), button_label=row.get("button_label"), button_emoji=row.get("button_emoji"), button_style=row.get("button_style"), questions=row.get("questions") or [], required_role_ids=_id_list(row.get("required_roles")), blocked_role_ids=_id_list(row.get("blocked_roles")), payload=row.get("payload"), channel_set=True)
        else:
            created = await create_panel(guild_id=guild_id, category_id=team["id"], channel_id=channel, title=row["title"], message=row.get("message") or "", button_label=row.get("button_label") or "Open ticket", questions=row.get("questions") or [], required_role_ids=_id_list(row.get("required_roles")), blocked_role_ids=_id_list(row.get("blocked_roles")), payload=row.get("payload"), button_emoji=row.get("button_emoji") or "", button_style=row.get("button_style") or "primary")
            existing = {"id": created["id"]}
        from cls_platform.tickets.store import set_publish
        if message_id:
            await set_publish(guild_id=guild_id, panel_id=existing["id"], channel_id=channel, message_id=int(message_id), status=publication.get("status") or "published")
        else:
            await set_publish(guild_id=guild_id, panel_id=existing["id"], channel_id=channel, message_id=None, status="draft")
    if strategy == "replace":
        for title, row in current_panels.items():
            if title not in seen:
                await delete_panel(guild_id=guild_id, panel_id=row["id"])


async def apply_menus(guild_id, body, *, same_guild: bool, known_messages: set[str], strategy: str, **_):
    current = {row["name"]: row for row in await list_menus(guild_id)}
    seen = set()
    for row in body.get("menus") or []:
        seen.add(row["name"])
        options = []
        missing_role = False
        for option in row.get("options") or []:
            role_id = option.get("role")
            if not str(role_id or "").isdigit():
                missing_role = True
                continue
            options.append({"role_id": str(role_id), "emoji": option.get("emoji") or "", "label": option.get("label") or "", "description": option.get("description") or ""})
        channel = _id(row.get("channel"))
        publication = row.get("publication") or {}
        keep_message = same_guild and str(publication.get("message_id") or "") in known_messages and channel is not None and not missing_role
        source = row.get("source") if same_guild and keep_message else "created"
        if source == "existing" and not keep_message:
            source = "created"
        payload = row.get("payload") if source == "created" else None
        existing = current.get(row["name"])
        if existing:
            saved = await update_menu(guild_id=guild_id, menu_id=existing["id"], name=row["name"], mode=row.get("mode"), menu_type=row.get("type"), enabled=bool(row.get("enabled")) and not missing_role, max_roles=row.get("max_roles"), max_roles_set=True, channel_id=channel, channel_set=True, payload=payload, options=options, button_style=row.get("button_style"))
        else:
            saved = await create_menu(guild_id=guild_id, name=row["name"], source=source if source in {"created", "existing"} else "created", menu_type=row.get("type") or "button", mode=row.get("mode") or "toggle", channel_id=channel, max_roles=row.get("max_roles"), payload=payload, options=options, button_style=row.get("button_style"))
            if missing_role:
                saved = await update_menu(guild_id=guild_id, menu_id=saved["id"], enabled=False)
        if keep_message:
            from cls_platform.role_menus.store import set_published
            await set_published(guild_id=guild_id, menu_id=saved["id"], channel_id=channel, message_id=int(publication["message_id"]), status=publication.get("status") or "published")
    if strategy == "replace":
        for name, row in current.items():
            if name not in seen:
                await delete_menu(guild_id=guild_id, menu_id=row["id"])


async def apply_join(guild_id, body, **_):
    await save_join(guild_id=guild_id, member_role_ids=_id_list(body.get("member_roles")), bot_role_ids=_id_list(body.get("bot_roles")), delay_seconds_value=int(body.get("delay_seconds") or 0), screening=body.get("screening") or "immediate")


async def apply_rules(guild_id, body, *, strategy: str, **_):
    current = {row["name"]: row for row in await list_rules(guild_id)}
    seen = set()
    for row in body.get("rules") or []:
        seen.add(row["name"])
        conditions = []
        unresolved = not str(row.get("action_role") or "").isdigit()
        if row.get("trigger") in {"role_add", "role_remove"} and not str(row.get("trigger_role") or "").isdigit():
            unresolved = True
        for condition in row.get("conditions") or []:
            item = {key: value for key, value in condition.items() if key != "role"}
            if condition.get("kind") in {"has_role", "lacks_role"}:
                if not str(condition.get("role") or "").isdigit():
                    unresolved = True
                    continue
                item["role_id"] = str(condition["role"])
            conditions.append(item)
        fields = {
            "name": row["name"],
            "trigger": row["trigger"],
            "trigger_role_id": str(row.get("trigger_role") or "") or None,
            "conditions": conditions,
            "action": row["action"],
            "action_role_id": str(row.get("action_role") or "0"),
            "delay_seconds": int(row.get("delay_seconds") or 0),
            "enabled": bool(row.get("enabled")) and not unresolved,
        }
        existing = current.get(row["name"])
        if unresolved and not str(fields["action_role_id"]).isdigit():
            continue
        if existing:
            await update_rule(guild_id=guild_id, rule_id=existing["id"], **fields)
        elif str(fields["action_role_id"]).isdigit():
            await create_rule(guild_id=guild_id, name=fields["name"], trigger=fields["trigger"], trigger_role_id=fields["trigger_role_id"], conditions=fields["conditions"], action=fields["action"], action_role_id=fields["action_role_id"], delay_seconds_value=fields["delay_seconds"], enabled=fields["enabled"])
    if strategy == "replace":
        for name, row in current.items():
            if name not in seen:
                await delete_rule(guild_id=guild_id, rule_id=row["id"])


async def apply_commands(guild_id, body, *, strategy: str, **_):
    from cls_platform.commands.policy import CommandPolicy
    from sqlalchemy import delete

    incoming = body.get("policies") or []
    names = {row["command"] for row in incoming}
    for row in incoming:
        await set_policy(
            guild_id=guild_id,
            command_name=row["command"],
            enabled=bool(row.get("enabled", True)),
            allowed_role_ids=_id_list(row.get("allowed_roles")),
            blocked_role_ids=_id_list(row.get("blocked_roles")),
            allowed_channel_ids=_id_list(row.get("allowed_channels")),
            blocked_channel_ids=_id_list(row.get("blocked_channels")),
            actor_id=None,
        )
    if strategy == "replace":
        async with session_scope() as session:
            await session.execute(delete(CommandPolicy).where(CommandPolicy.guild_id == guild_id, CommandPolicy.command_name.notin_(names or {"__none__"})))


async def apply_automod(guild_id, body, **_):
    """Write Automod V2. The legacy sqlite file is left unchanged."""
    from cls_platform.automod.engine import fresh_config
    from cls_platform.automod.migrate import _LEGACY, _MINUTES
    from cls_platform.automod.store import save_config

    if int(body.get("schema_version") or 0) == 2 and body.get("rules"):
        await save_config(guild_id, body, notes=["Imported Automod V2."], migrated=True)
        return
    config = fresh_config("custom")
    config["preset"] = "custom"
    config["enabled"] = bool(body.get("enabled"))
    by_id = {rule["id"]: rule for rule in config["rules"]}
    for rule in config["rules"]:
        rule["enabled"] = False
        rule["member_action"] = "none"
        rule["message_action"] = "keep"
    notes = ["Imported a legacy Automod bundle into V2. The old database was not modified."]
    for row in body.get("punishments") or []:
        rule_id = _LEGACY.get(str(row.get("event") or "").strip().lower())
        action = str(row.get("punishment") or "").strip().lower()
        if rule_id is None or rule_id not in by_id:
            notes.append(f"Left '{row.get('event')}' unmigrated.")
            continue
        if action == "warn":
            notes.append(f"{rule_id} had Warn stored. It was not copied as a member action.")
            continue
        rule = by_id[rule_id]
        if action == "delete":
            rule["message_action"] = "delete"
            rule["enabled"] = True
        elif action in {"mute", "timeout"}:
            rule["message_action"] = "delete"
            rule["member_action"] = "timeout"
            rule["timeout_seconds"] = _MINUTES.get(rule_id, 10) * 60
            rule["enabled"] = True
        elif action in {"kick", "ban"}:
            rule["message_action"] = "delete"
            rule["member_action"] = action
            rule["enabled"] = True
    config["exclusions"]["roles"] = _ref_ids(body.get("ignored_roles"))
    config["exclusions"]["channels"] = _ref_ids(body.get("ignored_channels"))
    await save_config(guild_id, config, notes=notes, migrated=True)


async def apply_j2c(guild_id, body, **_):
    async with aiosqlite.connect("j2c_data.db") as db:
        await db.execute(
            """
            INSERT INTO guild_setup (guild_id, join_channel_id, control_channel_id, category_id, enabled)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(guild_id) DO UPDATE SET
                join_channel_id = excluded.join_channel_id,
                control_channel_id = excluded.control_channel_id,
                category_id = excluded.category_id,
                enabled = excluded.enabled
            """,
            (guild_id, _id(body.get("join_channel")), _id(body.get("control_channel")), _id(body.get("category")), 1 if body.get("enabled") else 0),
        )
        await db.commit()


async def apply_autoreact(guild_id, body, **_):
    async with aiosqlite.connect("db/autoreact.db") as db:
        await db.execute("DELETE FROM autoreact WHERE guild_id = ?", (guild_id,))
        for row in body.get("triggers") or []:
            await db.execute("INSERT INTO autoreact (guild_id, trigger, emojis) VALUES (?, ?, ?)", (guild_id, row.get("trigger"), row.get("emojis") or ""))
        await db.commit()


EXPORTERS = {
    "welcome": export_welcome,
    "welcome_dm": export_dm,
    "goodbye": export_goodbye,
    "messages": export_messages,
    "logging": export_logging,
    "tickets": export_tickets,
    "role_menus": export_menus,
    "join_roles": export_join,
    "role_automation": export_rules,
    "commands": export_commands,
    "automod": export_automod,
    "j2c": export_j2c,
    "autoreact": export_autoreact,
}

APPLIERS = {
    "welcome": apply_welcome,
    "welcome_dm": apply_dm,
    "goodbye": apply_goodbye,
    "messages": apply_messages,
    "logging": apply_logging,
    "tickets": apply_tickets,
    "role_menus": apply_menus,
    "join_roles": apply_join,
    "role_automation": apply_rules,
    "commands": apply_commands,
    "automod": apply_automod,
    "j2c": apply_j2c,
    "autoreact": apply_autoreact,
}


def dumps(bundle: dict) -> str:
    return json.dumps(bundle, indent=2)
