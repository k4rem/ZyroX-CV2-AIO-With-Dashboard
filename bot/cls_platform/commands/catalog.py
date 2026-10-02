"""Guild-facing command catalog.

Runtime ``walk_commands()`` decides whether a command exists.
This module decides whether a guild admin should see it, and how to describe it.
"""

from __future__ import annotations

import re

from cls_platform.commands.policy import (
    _cooldown,
    _summary,
    access_decision,
    is_dangerous,
)

AUDIENCES = ("guild_admin", "staff", "member", "root", "internal")

AUDIENCE_LABEL = {
    "guild_admin": "Guild Admin",
    "staff": "Staff / Moderator",
    "member": "Member",
    "root": "Root / Owner",
    "internal": "Internal / System",
}

# Joke and slur aliases. Removed from the live command and never shown.
RETIRED_ALIASES = frozenset({"fuckban", "stfu", "hackban", "kuttaban", "chup"})

ROOT_HEADS = frozenset({
    "np", "global", "gb", "blacklist", "reload", "sync", "leaveguild", "ownerban",
    "bdg", "badges", "emergency", "extraowner", "nightmode", "eval", "jsk", "py",
})

ROOT_COGS = frozenset({
    "owner", "badges", "emergency", "global", "noprefix", "nightmode", "extraown",
    "extraowner", "status", "staffdmcog",
})

TOY_COGS = frozenset({
    "fun", "games", "slots", "blackjack", "music", "ai", "airesponses", "nitro",
    "imagecommands", "youtube", "counting", "counting", "birthdays", "birth",
    "leveling", "mc", "filters", "minecraft",
})

# Legacy duplicates and dashboard-retired writers. Source stays; guild catalog omits them.
LEGACY_COGS = frozenset({
    "welcomer", "automod", "autorole", "autorole2", "vanityroles", "vanity",
    "invitetracker", "giveaway", "ticket", "ticketcog", "logging", "reactionroles",
    "fastgreet", "greet", "joindm",
})

MODULES: dict[str, dict] = {
    "moderation": {
        "name": "Moderation",
        "description": "Remove members, time them out, warn them, lock channels, and clear messages.",
        "audience": "staff",
        "cogs": frozenset({
            "ban", "kick", "mute", "unmute", "unban", "lock", "hide", "unhide", "unlock",
            "jail", "message", "block", "warn", "ignore", "snipe", "moderation", "topcheck",
        }),
    },
    "roles": {
        "name": "Roles",
        "description": "Give and remove roles, including timed roles and role menus.",
        "audience": "guild_admin",
        "cogs": frozenset({"customrole", "role", "invcrole", "rolemenus", "roleautomation"}),
    },
    "utilities": {
        "name": "Utilities",
        "description": "Server info, member info, and small tools members or staff run in chat.",
        "audience": "member",
        "cogs": frozenset({
            "help", "general", "extra", "afk", "stats", "calculator", "encryption", "encrypt", "qr", "timer", "steal",
        }),
    },
    "messages": {
        "name": "Messages",
        "description": "Sticky messages, embeds, and autoresponders configured for this server.",
        "audience": "guild_admin",
        "cogs": frozenset({"messages", "stickymessage", "stickymessagelistener", "autoresponder", "embed", "media"}),
    },
    "voice": {
        "name": "Voice",
        "description": "Voice channel tools and join-to-create rooms.",
        "audience": "member",
        "cogs": frozenset({"voice", "jointocreate"}),
    },
    "security": {
        "name": "Security",
        "description": "Verification commands that sit next to the Security and Verification pages.",
        "audience": "staff",
        "cogs": frozenset({"verification", "verificationv2"}),
    },
    "tickets": {
        "name": "Tickets",
        "description": "Ticket commands that match the Tickets workspace.",
        "audience": "staff",
        "cogs": frozenset({"ticketsv2"}),
    },
    "invites": {
        "name": "Invites",
        "description": "Invite tracking commands for this server.",
        "audience": "guild_admin",
        "cogs": frozenset({"growthv2"}),
    },
}

# High-value prefix commands to move to slash later. Not a porting sprint.
MIGRATION_QUEUE = (
    {"name": "clear", "module": "moderation", "reason": "Moderators clear messages often, and this group is still prefix-only."},
    {"name": "role", "module": "roles", "reason": "Giving a role is a core staff action and is still prefix-only."},
    {"name": "removerole", "module": "roles", "reason": "Removing a role in bulk is still prefix-only."},
    {"name": "snipe", "module": "moderation", "reason": "Staff use this to see a deleted message, and it is still prefix-only."},
    {"name": "jail", "module": "moderation", "reason": "Jailing a member is a moderation action and is still prefix-only."},
)

# Used when the command's own help text is empty. Keyed by qualified name, then by the first word.
DESCRIPTIONS: dict[str, str] = {
    "ban": "Bans a member from this server. Staff action. Accepts a member and an optional reason.",
    "unban": "Removes a ban so that person can join again. Staff action. Requires the banned user's id.",
    "kick": "Removes a member without banning them. Staff action. Accepts a member and an optional reason.",
    "mute": "Times a member out so they cannot speak. Staff action. Accepts a member, an optional duration, and a reason.",
    "unmute": "Ends a member's timeout. Staff action.",
    "warn": "Records a warning against a member. Staff action. Accepts a member and a reason.",
    "clearwarns": "Clears the warnings stored for one member. Staff action.",
    "lock": "Stops members from sending messages in a channel. Staff action.",
    "unlock": "Allows messages in a channel that was locked. Staff action.",
    "hide": "Hides a channel from everyone. Staff action.",
    "unhide": "Shows a hidden channel to everyone again. Staff action.",
    "lockall": "Locks every channel in the server. Guild admin. Use carefully.",
    "unlockall": "Unlocks every channel in the server. Guild admin.",
    "hideall": "Hides every channel from everyone. Guild admin.",
    "unhideall": "Shows every hidden channel again. Guild admin.",
    "slowmode": "Sets how often members can send messages in a channel. Staff action.",
    "unslowmode": "Turns slowmode off in a channel. Staff action.",
    "nick": "Changes a member's nickname. Staff action.",
    "purge": "Deletes recent messages in a channel. Staff action. Does not remove moderation logs.",
    "clear": "Deletes recent messages in a channel. Staff action. Does not remove moderation logs.",
    "snipe": "Shows the last deleted message in this channel. Staff action.",
    "ping": "Shows whether CLS is responding and how long the gateway round trip took. Anyone can run it.",
    "userinfo": "Shows public information about a member. Anyone can run it.",
    "serverinfo": "Shows public information about this server. Anyone can run it.",
    "roleinfo": "Shows public information about a role. Anyone can run it.",
    "channelinfo": "Shows public information about a channel. Anyone can run it.",
    "prefix": "Changes the prefix CLS listens for in this server. Guild admin.",
    "afk": "Sets an away status that CLS mentions when you are pinged. Members can run it for themselves.",
}

MEMBER_HEADS = frozenset({
    "ping", "userinfo", "serverinfo", "roleinfo", "channelinfo", "vcinfo", "banner", "afk", "help", "avatar",
})
ADMIN_HEADS = frozenset({
    "prefix", "lockall", "unlockall", "hideall", "unhideall", "unbanall", "nuke", "clone",
    "autoresponder", "stickymessage", "sticky",
})

PAGE_SIZES = (25, 50, 100)
_DASHBOARD_ONLY = re.compile(r"use the dashboard", re.I)


def cog_key(command) -> str:
    cog = getattr(command, "cog", None)
    if cog is None:
        return ""
    name = getattr(cog, "qualified_name", None) or cog.__class__.__name__
    return "".join(ch for ch in name.lower() if ch.isalnum())


def cog_label(command) -> str:
    cog = getattr(command, "cog", None)
    if cog is None:
        return "General"
    return getattr(cog, "qualified_name", None) or cog.__class__.__name__


def invocation_kind(command) -> str:
    seen = []
    current = command
    while current is not None and len(seen) < 6:
        seen.append(type(current).__name__.lower())
        current = getattr(current, "parent", None)
    blob = " ".join(seen)
    if "hybrid" in blob:
        return "hybrid"
    if "slash" in blob or "appcommand" in blob:
        return "slash"
    return "prefix"


def module_for_cog(key: str) -> str | None:
    for module_id, meta in MODULES.items():
        if key in meta["cogs"]:
            return module_id
    return None


def audience_for(name: str, module_id: str | None) -> str:
    head = name.split()[0].lower()
    if head in ROOT_HEADS:
        return "root"
    if head in MEMBER_HEADS:
        return "member"
    if head in ADMIN_HEADS:
        return "guild_admin"
    if module_id and module_id in MODULES:
        return MODULES[module_id]["audience"]
    return "guild_admin"


def description_for(command) -> str:
    name = (getattr(command, "qualified_name", None) or getattr(command, "name", "") or "").strip()
    head = name.split()[0].lower() if name else ""
    runtime = _summary(command)
    if _DASHBOARD_ONLY.search(runtime or ""):
        return ""
    exact = DESCRIPTIONS.get(name.lower())
    if exact:
        return exact
    if runtime:
        return runtime
    return DESCRIPTIONS.get(head) or ""


def visibility(command) -> str | None:
    """Return a hide reason, or None when the command belongs in the guild catalog."""
    name = (getattr(command, "qualified_name", None) or "").strip()
    if not name or (name.startswith("__") and name.endswith("__")):
        return "internal"
    head = name.split()[0].lower()
    key = cog_key(command)
    raw = cog_label(command)
    if head in ROOT_HEADS or key in ROOT_COGS:
        return "root"
    if key in TOY_COGS:
        return "toy"
    if key in LEGACY_COGS or raw.startswith("_"):
        return "legacy"
    if module_for_cog(key) is None:
        return "uncatalogued"
    if not description_for(command):
        return "missing_description"
    text = _summary(command)
    if _DASHBOARD_ONLY.search(text or ""):
        return "legacy"
    return None


def is_guild_visible(command) -> bool:
    return visibility(command) is None


def module_id_for_command(command) -> str | None:
    if not is_guild_visible(command):
        return None
    return module_for_cog(cog_key(command))


def _permission_names(command) -> list[str]:
    permissions = getattr(command, "default_member_permissions", None)
    if permissions is None:
        return []
    try:
        return [str(label).replace("_", " ") for label, allowed in permissions if allowed]
    except (TypeError, ValueError):
        return []


def _aliases(command) -> list[str]:
    values = []
    for item in getattr(command, "aliases", None) or []:
        text = str(item).strip()
        if text and text.lower() not in RETIRED_ALIASES:
            values.append(text)
    return values


def command_row(command, saved: dict, module_enabled: dict[str, bool]) -> dict | None:
    if not is_guild_visible(command):
        return None
    name = command.qualified_name
    module_id = module_for_cog(cog_key(command))
    meta = MODULES[module_id]
    policy = saved.get(name)
    parent = name.rsplit(" ", 1)[0] if " " in name else None
    parent_policy = saved.get(parent) if parent else None
    own = policy is not None
    enabled = True if policy is None else bool(policy.get("enabled", True))
    allowed_roles = (policy or {}).get("allowed_role_ids") or []
    blocked_roles = (policy or {}).get("blocked_role_ids") or []
    allowed_channels = (policy or {}).get("allowed_channel_ids") or []
    blocked_channels = (policy or {}).get("blocked_channel_ids") or []
    restricted = bool(allowed_roles or blocked_roles or allowed_channels or blocked_channels or parent_policy)
    kind = invocation_kind(command)
    cooldown = _cooldown(command)
    return {
        "id": name,
        "name": name,
        "display_name": name.replace(" ", " / "),
        "module": meta["name"],
        "module_id": module_id,
        "group": name.split()[0],
        "description": description_for(command),
        "usage": f"{name} {getattr(command, 'signature', '') or ''}".strip(),
        "examples": [],
        "aliases": _aliases(command),
        "command_type": kind,
        "audience": audience_for(name, module_id),
        "audience_label": AUDIENCE_LABEL[audience_for(name, module_id)],
        "permissions": _permission_names(command),
        "default_enabled": True,
        "cooldown": cooldown,
        "cooldown_configurable": False,
        "visibility_supported": False,
        "autodelete_supported": False,
        "dangerous": is_dangerous(name, cog_label(command)),
        "protected": False,
        "enabled": enabled,
        "module_enabled": module_enabled.get(module_id, True),
        "allowed_role_ids": list(allowed_roles),
        "blocked_role_ids": list(blocked_roles),
        "allowed_channel_ids": list(allowed_channels),
        "blocked_channel_ids": list(blocked_channels),
        "restricted": restricted,
        "policy_scope": "own" if own else "inherited",
        "runtime_status": "loaded",
        "source": cog_label(command),
        "category": meta["name"],
    }


def iter_commands(bot):
    walker = getattr(bot, "walk_commands", None)
    if walker is None:
        return
    seen = set()
    for command in walker():
        name = getattr(command, "qualified_name", None) or getattr(command, "name", None)
        if not name or name in seen:
            continue
        seen.add(name)
        yield command


def guild_rows(bot, saved: dict, module_enabled: dict[str, bool]) -> list[dict]:
    rows = []
    for command in iter_commands(bot):
        row = command_row(command, saved, module_enabled)
        if row is not None:
            rows.append(row)
    rows.sort(key=lambda item: (item["module"].lower(), item["name"].lower()))
    return rows


def _search_blob(row: dict) -> str:
    alias = " ".join(row.get("aliases") or [])
    return f"{row['name']} {row['display_name']} {row['description']} {alias} {row['module']}".lower()


def normalize_query(query: str) -> str:
    text = (query or "").strip().lower()
    if text.startswith("/"):
        text = text[1:]
    return " ".join(text.split())


def filter_rows(
    rows: list[dict],
    *,
    query: str = "",
    module_id: str = "",
    audience: str = "",
    kind: str = "",
    enabled: str = "",
    restricted: str = "",
) -> list[dict]:
    needle = normalize_query(query)
    picked = []
    for row in rows:
        if module_id and row["module_id"] != module_id:
            continue
        if audience and row["audience"] != audience:
            continue
        if kind and row["command_type"] != kind:
            continue
        if enabled == "on" and not (row["enabled"] and row["module_enabled"]):
            continue
        if enabled == "off" and row["enabled"] and row["module_enabled"]:
            continue
        if restricted == "yes" and not row["restricted"]:
            continue
        if restricted == "no" and row["restricted"]:
            continue
        if needle and needle not in _search_blob(row) and needle not in row["name"].lower():
            continue
        if row["audience"] in {"root", "internal"}:
            continue
        picked.append(row)
    return picked


def paginate(rows: list[dict], page: int, page_size: int) -> dict:
    size = page_size if page_size in PAGE_SIZES else 25
    current = page if page > 0 else 1
    total = len(rows)
    pages = max(1, (total + size - 1) // size)
    if current > pages:
        current = pages
    start = (current - 1) * size
    return {
        "commands": rows[start : start + size],
        "page": current,
        "page_size": size,
        "total": total,
        "pages": pages,
    }


def module_summaries(rows: list[dict], module_enabled: dict[str, bool], bot) -> list[dict]:
    health = getattr(bot, "module_health", None)
    failed = {name for name, _reason in (*(getattr(health, "required_failed", None) or []), *(getattr(health, "optional_failed", None) or []))}
    summaries = []
    for module_id, meta in MODULES.items():
        owned = [row for row in rows if row["module_id"] == module_id]
        if not owned:
            continue
        enabled_commands = sum(1 for row in owned if row["enabled"])
        disabled_commands = len(owned) - enabled_commands
        restricted_commands = sum(1 for row in owned if row["restricted"])
        cog_failed = any(_cog_failed(name, failed) for name in meta["cogs"])
        if cog_failed:
            status = "warning"
            label = "Some commands unavailable"
        else:
            status = "healthy"
            label = "Healthy"
        summaries.append({
            "id": module_id,
            "name": meta["name"],
            "description": meta["description"],
            "enabled": module_enabled.get(module_id, True),
            "enabled_commands": enabled_commands,
            "disabled_commands": disabled_commands,
            "restricted_commands": restricted_commands,
            "command_count": len(owned),
            "health": {
                "status": status,
                "checks": [{
                    "id": f"{module_id}-load",
                    "label": label,
                    "ok": status == "healthy",
                    "severity": "ok" if status == "healthy" else "warning",
                    "fix_hint": None,
                    "scope": "module",
                }],
            },
        })
    return summaries


def _cog_failed(key: str, failed: set[str]) -> bool:
    for name in failed:
        if "".join(ch for ch in name.lower() if ch.isalnum()) == key:
            return True
    return False


def overview(rows: list[dict], modules: list[dict]) -> dict:
    active = sum(1 for item in modules if item["enabled"])
    enabled = sum(1 for row in rows if row["enabled"] and row["module_enabled"])
    disabled = len(rows) - enabled
    kinds = {"prefix": 0, "slash": 0, "hybrid": 0}
    for row in rows:
        kinds[row["command_type"]] = kinds.get(row["command_type"], 0) + 1
    return {
        "active_modules": active,
        "module_count": len(modules),
        "enabled_commands": enabled,
        "disabled_commands": disabled,
        "restricted_commands": sum(1 for row in rows if row["restricted"]),
        "prefix_commands": kinds.get("prefix", 0),
        "slash_commands": kinds.get("slash", 0),
        "hybrid_commands": kinds.get("hybrid", 0),
        "catalog_status": "loaded",
        "layers": (
            "CLS command policy controls whether a command is available and where or for whom it can run. "
            "Discord's own Integrations permissions are a separate layer."
        ),
    }


def build_tree(rows: list[dict]) -> list[dict]:
    parents: dict[str, dict] = {}
    order: list[str] = []
    for row in rows:
        group = row["group"]
        if group not in parents:
            parents[group] = {"name": group, "module_id": row["module_id"], "children": []}
            order.append(group)
        if row["name"] == group:
            parents[group]["command"] = row
        else:
            parents[group]["children"].append(row)
    return [parents[key] for key in order]


def drift_report(bot) -> dict:
    """Developer diagnostic. Not returned to guild admins."""
    missing_meta = []
    missing_description = []
    invalid = []
    alias_owner: dict[str, str] = {}
    duplicate_aliases = []
    catalog_without_runtime = []
    seen = set()
    for command in iter_commands(bot):
        name = command.qualified_name
        seen.add(name.lower())
        reason = visibility(command)
        key = cog_key(command)
        if reason == "missing_description":
            missing_description.append(name)
        elif reason == "uncatalogued" and key and key not in ROOT_COGS and key not in TOY_COGS and key not in LEGACY_COGS:
            missing_meta.append(name)
        audience = audience_for(name, module_for_cog(key))
        module_id = module_for_cog(key)
        if reason is None and audience not in AUDIENCES:
            invalid.append(name)
        if reason is None and module_id not in MODULES:
            invalid.append(name)
        for alias in _aliases(command):
            token = alias.lower()
            if token in alias_owner:
                duplicate_aliases.append(token)
            else:
                alias_owner[token] = name
    for name in DESCRIPTIONS:
        if name not in seen and " " not in name:
            # Curated copy may describe a head that is loaded under that name only.
            pass
        head_loaded = any(item == name or item.startswith(name + " ") for item in seen)
        if not head_loaded:
            catalog_without_runtime.append(name)
    return {
        "runtime_without_metadata": missing_meta,
        "missing_description": missing_description,
        "catalog_without_runtime": catalog_without_runtime,
        "duplicate_aliases": duplicate_aliases,
        "invalid": invalid,
    }


def retire_unprofessional_aliases(bot) -> None:
    walker = getattr(bot, "walk_commands", None)
    if walker is None:
        return
    for command in list(walker()):
        aliases = [str(item) for item in (getattr(command, "aliases", None) or [])]
        for alias in aliases:
            if alias.lower() not in RETIRED_ALIASES:
                continue
            parent = getattr(command, "parent", None) or bot
            remove = getattr(parent, "remove_command", None)
            if remove is not None:
                remove(alias)


async def explain_access(
    *,
    guild_id: int,
    command,
    role_ids: set[int],
    channel_id: int | None,
    discord_permissions: set[str] | None,
) -> dict:
    module_id = module_id_for_command(command) if command is not None else None
    name = getattr(command, "qualified_name", None) or ""
    result = await access_decision(guild_id, name, role_ids, channel_id, module_id=module_id)
    required = set(_permission_names(command)) if command is not None else set()
    if result["allowed"] and required and discord_permissions is not None:
        missing = sorted(perm for perm in required if perm not in discord_permissions)
        result["steps"].append({
            "ok": not missing,
            "label": "Discord permission " + (", ".join(missing) if missing else "present"),
        })
        if missing:
            result["allowed"] = False
            result["code"] = "discord_permission"
            result["message"] = "Missing Discord permission: " + ", ".join(missing)
    elif result["allowed"]:
        result["steps"].append({
            "ok": True,
            "label": "Discord Integrations are a separate layer and were not changed",
        })
    result["command"] = name
    return result
