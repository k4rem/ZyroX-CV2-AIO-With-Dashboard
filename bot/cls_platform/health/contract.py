"""Shared module-health contract.

Status is derived from real capability checks. Callers must not substitute a
placeholder string for this object.
"""

from __future__ import annotations

from typing import Any, Iterable

STATUSES = ("healthy", "warning", "error", "locked", "unavailable")
SEVERITIES = ("ok", "warning", "error", "locked", "unavailable")

# id -> (human label, fix hint)
CAPABILITIES: dict[str, tuple[str, str]] = {
    "manage_roles": ("Manage Roles", "Grant CLS the Manage Roles permission."),
    "manage_messages": ("Manage Messages", "Grant CLS the Manage Messages permission."),
    "moderate_members": ("Moderate Members", "Grant CLS the Moderate Members permission."),
    "kick_members": ("Kick Members", "Grant CLS the Kick Members permission."),
    "ban_members": ("Ban Members", "Grant CLS the Ban Members permission."),
    "manage_channels": ("Manage Channels", "Grant CLS the Manage Channels permission."),
    "view_audit_log": ("View Audit Log", "Grant CLS the View Audit Log permission."),
    "send_messages": ("Send Messages", "Allow CLS to send messages here."),
    "embed_links": ("Embed Links", "Allow CLS to embed links here."),
    "attach_files": ("Attach Files", "Allow CLS to attach files here."),
    "view_channel": ("Channel visibility", "Allow CLS to view this channel."),
    "role_managed": ("Managed role", "Choose a role that is not managed by an integration."),
    "role_hierarchy": ("Role above CLS", "Move the CLS role above this role."),
    "bot_member": ("CLS member", "CLS is not available in this server."),
}

GUILD_PERMISSIONS = (
    "manage_roles",
    "manage_messages",
    "moderate_members",
    "kick_members",
    "ban_members",
    "manage_channels",
    "view_audit_log",
    "send_messages",
    "embed_links",
    "attach_files",
    "view_channel",
)

CHANNEL_CAPABILITIES = (
    "view_channel",
    "send_messages",
    "embed_links",
    "attach_files",
    "manage_channels",
)

CHANNEL_FAIL_LABELS = {
    "view_channel": "Cannot view",
    "send_messages": "Cannot send",
    "embed_links": "Cannot embed",
    "attach_files": "Cannot attach files",
    "manage_channels": "Cannot manage channel",
}

def check(
    *,
    id: str,
    ok: bool,
    severity: str,
    scope: str,
    label: str | None = None,
    fix_hint: str | None = None,
) -> dict[str, Any]:
    if severity not in SEVERITIES:
        raise ValueError(f"unknown severity {severity}")
    known = CAPABILITIES.get(id)
    resolved_label = label or (known[0] if known else id)
    resolved_hint = fix_hint if fix_hint is not None else (known[1] if known else None)
    passed = bool(ok)
    return {
        "id": id,
        "label": resolved_label,
        "ok": passed,
        "severity": "ok" if passed else severity,
        "fix_hint": None if passed else resolved_hint,
        "scope": scope,
    }


def rollup(checks: Iterable[dict[str, Any]]) -> str:
    rows = list(checks)
    if not rows:
        return "unavailable"
    failing = [row for row in rows if not row.get("ok")]
    if not failing:
        return "healthy"
    severities = {row.get("severity") for row in failing}
    if "error" in severities:
        return "error"
    if "unavailable" in severities:
        return "unavailable"
    if "warning" in severities:
        return "warning"
    if "locked" in severities:
        return "locked"
    return "unavailable"


def module_health(checks: Iterable[dict[str, Any]]) -> dict[str, Any]:
    rows = list(checks)
    return {"status": rollup(rows), "checks": rows}


def role_is_below_bot(position: int, role_id: int | str, bot_position: int, bot_role_id: int | str) -> bool:
    """Discord lets a bot manage roles strictly below its highest role."""
    if int(position) < int(bot_position):
        return True
    if int(position) > int(bot_position):
        return False
    return int(role_id) < int(bot_role_id)


def role_checks(
    *,
    managed: bool,
    position: int | None,
    role_id: int | str | None,
    bot_position: int | None,
    bot_role_id: int | str | None,
    manage_roles: bool | None,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    if manage_roles is not None:
        rows.append(
            check(
                id="manage_roles",
                ok=bool(manage_roles),
                severity="error",
                scope="guild",
            )
        )
    rows.append(
        check(
            id="role_managed",
            ok=not managed,
            severity="warning",
            scope="role",
        )
    )
    if position is not None and role_id is not None and bot_position is not None and bot_role_id is not None:
        rows.append(
            check(
                id="role_hierarchy",
                ok=role_is_below_bot(position, role_id, bot_position, bot_role_id),
                severity="warning",
                scope="role",
            )
        )
    return rows


def channel_checks(capabilities: dict[str, bool], required: Iterable[str]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for key in required:
        if key not in CHANNEL_CAPABILITIES:
            raise ValueError(f"unknown channel capability {key}")
        severity = "warning" if key in {"embed_links", "attach_files"} else "error"
        rows.append(
            check(
                id=key,
                ok=bool(capabilities.get(key)),
                severity=severity,
                scope="channel",
                label=CHANNEL_FAIL_LABELS[key],
            )
        )
    return rows


def guild_permission_checks(permissions: dict[str, bool]) -> list[dict[str, Any]]:
    rows = []
    for key in GUILD_PERMISSIONS:
        severity = "warning" if key == "view_audit_log" else "error"
        rows.append(
            check(
                id=key,
                ok=bool(permissions.get(key)),
                severity=severity,
                scope="guild",
            )
        )
    return rows


def _perm(obj: Any, name: str) -> bool:
    if obj is None:
        return False
    if isinstance(obj, dict):
        return bool(obj.get(name))
    return bool(getattr(obj, name, False))


def _channel_caps(channel: Any, member: Any) -> dict[str, bool] | None:
    permissions_for = getattr(channel, "permissions_for", None)
    if not callable(permissions_for):
        return None
    try:
        overwrite = permissions_for(member)
    except Exception:
        return None
    return {key: _perm(overwrite, key) for key in CHANNEL_CAPABILITIES}


def runtime_snapshot(guild: Any) -> dict[str, Any]:
    """One pass over the cached guild. No per-role or per-channel HTTP."""
    if guild is None or getattr(guild, "me", None) is None:
        health = module_health(
            [
                check(
                    id="bot_member",
                    ok=False,
                    severity="unavailable",
                    scope="guild",
                )
            ]
        )
        return {**health, "bot": None, "roles": {}, "channels": {}}

    me = guild.me
    guild_permissions = getattr(me, "guild_permissions", None)
    perm_map = {key: _perm(guild_permissions, key) for key in GUILD_PERMISSIONS}
    checks = guild_permission_checks(perm_map)
    top = getattr(me, "top_role", None)
    bot = None
    if top is not None:
        bot = {
            "top_role_id": str(top.id),
            "top_role_position": int(getattr(top, "position", 0) or 0),
            "manage_roles": perm_map["manage_roles"],
        }
    roles: dict[str, Any] = {}
    for role in getattr(guild, "roles", []) or []:
        role_id = getattr(role, "id", None)
        if role_id is None:
            continue
        position = getattr(role, "position", None)
        managed = bool(getattr(role, "managed", False))
        role_rows = role_checks(
            managed=managed,
            position=int(position) if position is not None else None,
            role_id=role_id,
            bot_position=bot["top_role_position"] if bot else None,
            bot_role_id=bot["top_role_id"] if bot else None,
            manage_roles=perm_map["manage_roles"],
        )
        roles[str(role_id)] = {
            "position": int(position) if position is not None else None,
            "managed": managed,
            "status": rollup(role_rows),
            "checks": role_rows,
        }
    channels: dict[str, Any] = {}
    for channel in getattr(guild, "channels", []) or []:
        channel_id = getattr(channel, "id", None)
        if channel_id is None:
            continue
        caps = _channel_caps(channel, me)
        if caps is None:
            continue
        channels[str(channel_id)] = caps
    health = module_health(checks)
    return {**health, "bot": bot, "roles": roles, "channels": channels}
