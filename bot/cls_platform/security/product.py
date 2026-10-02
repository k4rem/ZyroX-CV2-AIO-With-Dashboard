"""Human Security Center language. Raw engine ids stay out of primary labels."""

from __future__ import annotations

from datetime import datetime, timezone

LABELS: dict[str, tuple[str, str]] = {
    "channel.delete": ("Channel deletion", "Channels removed inside the time window."),
    "role.delete": ("Role deletion", "Roles removed inside the time window."),
    "member.prune": ("Member prune", "A prune removed members in one action."),
    "aggregate.destructive": ("Destructive burst", "Several destructive actions landed inside one window."),
    "role.permission_escalation": ("Permission escalation", "A role gained dangerous permissions."),
    "member.privileged_role_grant": ("Privileged role grant", "A member received a role with dangerous permissions."),
    "channel.overwrite_escalation": ("Channel permission escalation", "A channel overwrite granted dangerous access."),
    "single.everyone_critical_control": ("Everyone gained a critical permission", "A critical permission was granted to everyone."),
    "single.critical_control_grant": ("Critical permission grant", "A critical permission was granted."),
    "sequence.self_escalation": ("Self escalation", "An actor increased their own access."),
    "member.ban": ("Member ban", "Members were banned inside the time window."),
    "member.kick": ("Member kick", "Members were kicked inside the time window."),
    "member.ban_or_kick": ("Moderation burst", "Bans or kicks landed inside the time window."),
    "bot.add": ("Bot added", "A bot was added to the server."),
    "bot.privilege_change": ("Bot privilege change", "A bot gained dangerous permissions."),
    "webhook.create": ("Webhook created", "Webhooks were created inside the time window."),
    "webhook.delete": ("Webhook deleted", "A webhook was deleted."),
    "webhook.update": ("Webhook edited", "A webhook was edited."),
    "cls.impairment": ("CLS impairment", "An action reduced what CLS can do."),
    "sequence.cls_impairment": ("CLS impairment sequence", "A sequence reduced what CLS can do."),
    "phishing": ("Phishing message", "A message matched the phishing patterns CLS watches."),
    "human_honeypot": ("Human honeypot", "Someone posted in the visible honeypot channel."),
    "bot_trap": ("Bot trap", "An untrusted bot posted in the bot trap channel."),
    "webhook_activity": ("Webhook in the bot trap", "A webhook posted in the bot trap channel."),
}

GROUPS: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("Destructive actions", ("channel.delete", "role.delete", "member.prune", "aggregate.destructive")),
    ("Permission escalation", ("role.permission_escalation", "member.privileged_role_grant", "channel.overwrite_escalation", "single.everyone_critical_control", "single.critical_control_grant", "sequence.self_escalation")),
    ("Role and admin changes", ("member.privileged_role_grant", "role.permission_escalation")),
    ("Channel destruction", ("channel.delete",)),
    ("Bot additions", ("bot.add", "bot.privilege_change")),
    ("Webhook abuse", ("webhook.create", "webhook.delete", "webhook.update")),
    ("CLS impairment", ("cls.impairment", "sequence.cls_impairment")),
    ("Moderation bursts", ("member.ban_or_kick", "member.ban", "member.kick")),
)

SCOPE_GROUPS: dict[str, tuple[str, ...]] = {
    "Role changes": ("role.permission_escalation", "member.privileged_role_grant", "role.delete"),
    "Channel destruction": ("channel.delete",),
    "Moderation bursts": ("member.ban", "member.kick"),
    "Bot additions": ("bot.add", "bot.privilege_change"),
    "Webhook abuse": ("webhook.create", "webhook.delete", "webhook.update"),
    "CLS impairment": ("cls.impairment",),
}

CONFIDENCE_LABELS = {
    "CONFIRMED": "Confirmed",
    "PROBABLE": "Probable",
    "AMBIGUOUS": "Ambiguous",
    "UNATTRIBUTED": "Unknown",
    "SELF": "Self",
    "CLS_PROXIED": "CLS",
}

SEVERITY_LABELS = {"C": "Critical", "H": "High", "M": "Medium", "L": "Low"}
MESSAGE_KINDS = {"phishing", "human_honeypot", "bot_trap", "webhook_activity"}


def detector_title(action_class: str) -> str:
    found = LABELS.get(action_class)
    return found[0] if found else "Security signal"


def detector_description(action_class: str) -> str:
    found = LABELS.get(action_class)
    return found[1] if found else "CLS is watching this signal."


def confidence_label(state: str | None) -> str:
    if not state:
        return "Unknown"
    return CONFIDENCE_LABELS.get(state, "Unknown")


def severity_label(code: str | None) -> str:
    if not code:
        return "Unspecified"
    return SEVERITY_LABELS.get(code, "Unspecified")


def provisional(threshold_status: str | None) -> bool:
    return threshold_status == "DEVELOPMENT_PROPOSAL"


def behavior(*, enforce_locked: bool, honeypot_configured: bool) -> dict:
    will = [
        "Detect suspicious actions",
        "Record evidence",
        "Create incidents",
        "Send alerts where a destination is configured",
        "Delete phishing messages",
    ]
    if honeypot_configured:
        will.append("Delete messages posted in the human honeypot")
    will_not = []
    if enforce_locked:
        will_not = [
            "Ban members",
            "Kick members",
            "Strip roles",
            "Quarantine members automatically",
        ]
    return {
        "mode_label": "Detect, record, and alert" if enforce_locked else "Detect and contain",
        "enforce_label": "Locked" if enforce_locked else "Available",
        "will": will,
        "will_not": will_not,
    }


def posture(*, open_high: int, join_elevated: bool) -> str:
    if open_high > 0 or join_elevated:
        return "Elevated"
    return "Normal"


def incident_heading(kind: str | None, detail: str | None) -> tuple[str, str]:
    title = detector_title(kind or "")
    subtitle = (detail or "").strip() or detector_description(kind or "")
    return title, subtitle


def status_label(status: str, closure: str | None) -> str:
    if status == "ACTIVE":
        return "Open"
    if closure == "FALSE_POSITIVE":
        return "False positive"
    if closure == "RESOLVED":
        return "Resolved"
    if closure == "EXPIRED_INACTIVE":
        return "Closed, inactive"
    if closure == "EXPIRED_LIFETIME":
        return "Closed, expired"
    return "Closed"


def delete_failure_detail(exc: BaseException) -> str:
    name = type(exc).__name__.lower()
    text = str(exc).lower()
    if "forbidden" in name or "50013" in text or "missing permission" in text or "manage messages" in text:
        return "Missing Manage Messages"
    return "Delete failed"


def channel_in_guild(known_ids: set[int], channel_id: int) -> bool:
    return int(channel_id) in known_ids


def honeypot_exempt(*, author_is_bot: bool, webhook: bool, staff: bool, trusted: bool) -> bool:
    return author_is_bot or webhook or staff or trusted


def join_signal(rows: list[dict], *, now: datetime | None = None) -> dict:
    moment = now or datetime.now(timezone.utc)
    if moment.tzinfo is None:
        moment = moment.replace(tzinfo=timezone.utc)
    window = 600
    young_limit = 7 * 24 * 3600
    recent = 0
    young = 0
    for row in rows:
        joined = row.get("joined_at")
        if joined is None:
            continue
        if joined.tzinfo is None:
            joined = joined.replace(tzinfo=timezone.utc)
        ago = (moment - joined).total_seconds()
        if ago < 0 or ago > window:
            continue
        recent += 1
        created = row.get("created_at")
        if created is None:
            continue
        if created.tzinfo is None:
            created = created.replace(tzinfo=timezone.utc)
        if (moment - created).total_seconds() < young_limit:
            young += 1
    elevated = recent >= 8 and young >= 5
    return {
        "recent_joins": recent,
        "young_accounts": young,
        "window_minutes": 10,
        "elevated": elevated,
        "explanation": f"{recent} joins in 10 minutes. {young} of those accounts are younger than 7 days.",
    }


def scope_options() -> list[dict]:
    rows = [{"id": "*", "title": "All protected actions", "scopes": ["*"]}]
    for title, scopes in SCOPE_GROUPS.items():
        rows.append({"id": title, "title": title, "scopes": list(scopes)})
    return rows


def group_detectors(policies: list[dict], counts: dict[str, int], last_at: dict[str, str | None]) -> list[dict]:
    grouped: dict[str, list] = {name: [] for name, _ids in GROUPS}
    seen: set[str] = set()
    by_class = {row["action_class"]: row for row in policies}
    for name, ids in GROUPS:
        for action_class in ids:
            if action_class in seen or action_class not in by_class:
                continue
            seen.add(action_class)
            row = by_class[action_class]
            grouped[name].append(_detector_card(row, counts, last_at))
    other = []
    for row in policies:
        if row["action_class"] in seen:
            continue
        other.append(_detector_card(row, counts, last_at))
    payload = [{"name": name, "detectors": rows} for name, rows in grouped.items() if rows]
    if other:
        payload.append({"name": "Other signals", "detectors": other})
    return payload


def _detector_card(row: dict, counts: dict[str, int], last_at: dict[str, str | None]) -> dict:
    tuning = provisional(row.get("threshold_status"))
    return {
        "id": row["action_class"],
        "title": detector_title(row["action_class"]),
        "description": detector_description(row["action_class"]),
        "threshold": row.get("threshold"),
        "window_s": row.get("window_s"),
        "enabled": row.get("enabled", True),
        "mode": "Detect and record",
        "response": "Record and alert. Containment stays locked.",
        "last_triggered_at": last_at.get(row["action_class"]),
        "triggers_30d": int(counts.get(row["action_class"], 0)),
        "provisional": tuning,
        "provisional_label": "Threshold tuning: Provisional" if tuning else None,
        "provisional_detail": "This threshold is a development proposal. It is not production validated." if tuning else None,
    }


def scope_title(scopes: list[str] | None) -> str:
    values = list(scopes or [])
    if values == ["*"]:
        return "All protected actions"
    for title, group in SCOPE_GROUPS.items():
        if set(values) == set(group):
            return title
    if not values:
        return "No scope"
    return ", ".join(detector_title(item) for item in values)
