"""Pure Automod V2 decisions. No Discord calls and no database."""

from __future__ import annotations

import re
from typing import Any

RULE_IDS = (
    "flood",
    "duplicate",
    "caps",
    "mentions",
    "emoji",
    "links",
    "invites",
    "bad_words",
    "attachments",
    "keyword",
)

RULE_NAMES = {
    "flood": "Message flood",
    "duplicate": "Duplicate messages",
    "caps": "Caps",
    "mentions": "Mentions",
    "emoji": "Emoji spam",
    "links": "Links",
    "invites": "Discord invites",
    "bad_words": "Bad words",
    "attachments": "Attachments",
    "keyword": "Custom keyword",
}

LOG_EVENTS = {
    "flood": "automod.spam",
    "duplicate": "automod.duplicate",
    "caps": "automod.caps",
    "mentions": "automod.mentions",
    "emoji": "automod.emoji",
    "links": "automod.links",
    "invites": "automod.invites",
    "bad_words": "automod.bad_words",
    "attachments": "automod.attachments",
    "keyword": "automod.keyword",
}

LOG_TITLES = {
    "flood": "Spam detected",
    "duplicate": "Duplicate message detected",
    "caps": "Caps detected",
    "mentions": "Mention spam detected",
    "emoji": "Emoji spam detected",
    "links": "Link detected",
    "invites": "Invite detected",
    "bad_words": "Blocked language detected",
    "attachments": "Attachment policy detected",
    "keyword": "Keyword detected",
}

TIMEOUT_MIN = 60
TIMEOUT_MAX = 28 * 24 * 60 * 60
MESSAGE_ACTIONS = {"keep", "delete"}
MEMBER_ACTIONS = {"none", "warn", "timeout", "kick", "ban"}
NOTIFY_ACTIONS = {"none", "dm", "channel", "both"}
MODES = {"observe", "enforce"}
ENGINES = {"cls"}
PRESETS = {"relaxed", "balanced", "strict", "custom"}
ESCALATION_ACTIONS = {"timeout", "kick", "ban"}
_SEVERITY = {"ban": 3, "kick": 2, "timeout": 1}

_LEET = str.maketrans({"0": "o", "1": "i", "3": "e", "4": "a", "5": "s", "7": "t", "@": "a", "$": "s"})
_CONFUSABLE = str.maketrans(
    {
        "а": "a",
        "е": "e",
        "о": "o",
        "р": "p",
        "с": "c",
        "у": "y",
        "х": "x",
        "і": "i",
        "Α": "a",
        "Ε": "e",
        "Ο": "o",
    }
)
_INVITE = re.compile(r"(?:discord\.gg|discord(?:app)?\.com/invite)/([A-Za-z0-9-]+)", re.I)
_URL = re.compile(r"https?://[^\s<>]+", re.I)
_CUSTOM_EMOJI = re.compile(r"<a?:\w+:\d+>")
_UNICODE_EMOJI = re.compile(r"[\U0001F300-\U0001FAFF\u2600-\u27BF]")
_USER_MENTION = re.compile(r"<@!?\d+>")
_ROLE_MENTION = re.compile(r"<@&\d+>")
_ZW = re.compile(r"[\u200b-\u200d\ufeff]")


def logging_sentence(rule_id: str, summary: str, member_name: str, channel_name: str) -> str:
    title = LOG_TITLES.get(rule_id, "Automod")
    who = member_name.strip() or "member"
    where = channel_name.strip() or "channel"
    return f"{title} — @{who} {summary} in #{where}"


def id_set(values: Any) -> set[int]:
    found: set[int] = set()
    for item in values or []:
        text = str(item).strip()
        if text.isdigit():
            found.add(int(text))
    return found


def empty_scope() -> dict[str, list[str]]:
    return {
        "include_channels": [],
        "exclude_channels": [],
        "include_categories": [],
        "exclude_categories": [],
        "exclude_roles": [],
    }


def empty_exclusions() -> dict[str, list[str]]:
    return {"channels": [], "categories": [], "roles": [], "members": [], "staff_roles": []}


def default_escalations() -> list[dict[str, Any]]:
    return [
        {"points": 10, "window_seconds": 7 * 86400, "action": "kick", "duration_seconds": None},
        {"points": 6, "window_seconds": 86400, "action": "timeout", "duration_seconds": 3600},
        {"points": 3, "window_seconds": 1800, "action": "timeout", "duration_seconds": 600},
    ]


def _rule(
    rule_id: str,
    *,
    enabled: bool,
    trigger: dict[str, Any],
    message_action: str = "delete",
    member_action: str = "none",
    timeout_seconds: int = 600,
    points: int = 1,
) -> dict[str, Any]:
    return {
        "id": rule_id,
        "name": RULE_NAMES[rule_id],
        "enabled": enabled,
        "engine": "cls",
        "mode": "enforce",
        "trigger": trigger,
        "scope": empty_scope(),
        "message_action": message_action,
        "member_action": member_action,
        "timeout_seconds": timeout_seconds,
        "notify_action": "none",
        "points": points,
    }


def preset_rules(preset: str) -> list[dict[str, Any]]:
    """Concrete rule values. The name never hides the numbers."""
    name = preset if preset in {"relaxed", "balanced", "strict"} else "balanced"
    if name == "relaxed":
        return [
            _rule("flood", enabled=True, trigger={"count": 8, "window_seconds": 8, "per_channel": False}, member_action="timeout", timeout_seconds=300),
            _rule("duplicate", enabled=True, trigger={"count": 5, "window_seconds": 60, "normalized": True}),
            _rule("caps", enabled=True, trigger={"percent": 85, "min_length": 12}),
            _rule("mentions", enabled=True, trigger={"count": 8, "everyone": True}),
            _rule("emoji", enabled=True, trigger={"count": 12}),
            _rule("links", enabled=False, trigger={"mode": "block", "allow": [], "deny": []}, message_action="keep"),
            _rule("invites", enabled=True, trigger={"block_external": True, "allow_own": True, "allow_guilds": [], "allow_codes": []}),
            _rule("bad_words", enabled=False, trigger={"terms": [], "mode": "whole", "exceptions": []}, message_action="keep"),
            _rule("attachments", enabled=False, trigger={"policy": "allow"}, message_action="keep"),
            _rule("keyword", enabled=False, trigger={"phrases": [], "mode": "contains"}, message_action="keep"),
        ]
    if name == "strict":
        return [
            _rule("flood", enabled=True, trigger={"count": 4, "window_seconds": 4, "per_channel": True}, member_action="timeout", timeout_seconds=3600, points=2),
            _rule("duplicate", enabled=True, trigger={"count": 2, "window_seconds": 20, "normalized": True}, member_action="timeout", timeout_seconds=600),
            _rule("caps", enabled=True, trigger={"percent": 60, "min_length": 6}),
            _rule("mentions", enabled=True, trigger={"count": 4, "everyone": True}, member_action="timeout", timeout_seconds=600),
            _rule("emoji", enabled=True, trigger={"count": 6}),
            _rule("links", enabled=True, trigger={"mode": "block", "allow": [], "deny": []}),
            _rule("invites", enabled=True, trigger={"block_external": True, "allow_own": True, "allow_guilds": [], "allow_codes": []}, member_action="timeout", timeout_seconds=600),
            _rule("bad_words", enabled=False, trigger={"terms": [], "mode": "whole", "exceptions": []}),
            _rule("attachments", enabled=False, trigger={"policy": "allow"}, message_action="keep"),
            _rule("keyword", enabled=False, trigger={"phrases": [], "mode": "contains"}, message_action="keep"),
        ]
    return [
        _rule("flood", enabled=True, trigger={"count": 5, "window_seconds": 5, "per_channel": False}, member_action="timeout", timeout_seconds=600),
        _rule("duplicate", enabled=True, trigger={"count": 3, "window_seconds": 30, "normalized": True}),
        _rule("caps", enabled=True, trigger={"percent": 70, "min_length": 8}),
        _rule("mentions", enabled=True, trigger={"count": 5, "everyone": True}),
        _rule("emoji", enabled=True, trigger={"count": 8}),
        _rule("links", enabled=True, trigger={"mode": "block", "allow": [], "deny": []}),
        _rule("invites", enabled=True, trigger={"block_external": True, "allow_own": True, "allow_guilds": [], "allow_codes": []}),
        _rule("bad_words", enabled=False, trigger={"terms": [], "mode": "whole", "exceptions": []}),
        _rule("attachments", enabled=False, trigger={"policy": "allow"}, message_action="keep"),
        _rule("keyword", enabled=False, trigger={"phrases": [], "mode": "contains"}, message_action="keep"),
    ]


def fresh_config(preset: str = "balanced") -> dict[str, Any]:
    chosen = preset if preset in PRESETS and preset != "custom" else "balanced"
    return {
        "enabled": False,
        "preset": "custom" if preset == "custom" else chosen,
        "exclusions": empty_exclusions(),
        "escalations": default_escalations(),
        "strike_ttl_seconds": 7 * 86400,
        "rules": preset_rules(chosen),
    }


def normalize_text(value: str) -> str:
    text = _ZW.sub("", value or "")
    text = text.lower().translate(_CONFUSABLE).translate(_LEET)
    text = re.sub(r"(.)\1{2,}", r"\1", text)
    return text


def normalize_duplicate(value: str) -> str:
    text = _ZW.sub("", (value or "").lower())
    return re.sub(r"\s+", " ", text).strip()


def _clip(value: str, limit: int = 80) -> str:
    text = re.sub(r"\s+", " ", value or "").strip()
    if len(text) <= limit:
        return text
    return text[: limit - 1] + "…"


def scope_reason(exclusions: dict, rule: dict, ctx: dict) -> str | None:
    """Explicit exclusion wins over an include list. Staff immunity is its own reason."""
    member_id = int(ctx.get("member_id") or 0)
    channel_id = int(ctx.get("channel_id") or 0)
    category_id = int(ctx.get("category_id") or 0)
    role_ids = id_set(ctx.get("role_ids"))
    scope = rule.get("scope") or {}
    staff = id_set((exclusions or {}).get("staff_roles"))
    if role_ids & staff:
        return "Staff immunity"
    if member_id and member_id in id_set((exclusions or {}).get("members")):
        return "Member exclusion"
    if channel_id and (
        channel_id in id_set((exclusions or {}).get("channels"))
        or channel_id in id_set(scope.get("exclude_channels"))
    ):
        return "Channel exclusion"
    if category_id and (
        category_id in id_set((exclusions or {}).get("categories"))
        or category_id in id_set(scope.get("exclude_categories"))
    ):
        return "Category exclusion"
    if role_ids & (id_set((exclusions or {}).get("roles")) | id_set(scope.get("exclude_roles"))):
        return "Role exclusion"
    include_channels = id_set(scope.get("include_channels"))
    include_categories = id_set(scope.get("include_categories"))
    if include_channels or include_categories:
        in_channel = channel_id in include_channels if include_channels else False
        in_category = category_id in include_categories if include_categories else False
        if not in_channel and not in_category:
            return "Outside rule scope"
    return None


def _wildcard(pattern: str) -> re.Pattern[str] | None:
    if not pattern or len(pattern) > 80 or pattern.count("*") > 3:
        return None
    if not re.fullmatch(r"[A-Za-z0-9 *]+", pattern):
        return None
    body = ".*".join(re.escape(part) for part in pattern.lower().split("*"))
    return re.compile(body)


def _term_hit(text: str, term: str, mode: str) -> bool:
    if mode == "wildcard":
        compiled = _wildcard(term)
        return bool(compiled and compiled.search(text))
    if mode == "whole":
        return re.search(rf"(?<!\w){re.escape(term)}(?!\w)", text) is not None
    return term in text


def bad_word_hit(content: str, trigger: dict) -> str | None:
    mode = str(trigger.get("mode") or "whole")
    if mode not in {"whole", "contains", "wildcard"}:
        mode = "whole"
    normalized = normalize_text(content)
    for exception in trigger.get("exceptions") or []:
        cleaned = normalize_text(str(exception))
        if cleaned:
            normalized = normalized.replace(cleaned, " ")
    for term in trigger.get("terms") or []:
        cleaned = normalize_text(str(term)) if mode != "wildcard" else str(term).strip().lower()
        if cleaned and _term_hit(normalized if mode != "wildcard" else normalize_text(content), cleaned, mode):
            return cleaned
    return None


def _host(url: str) -> str:
    host = re.sub(r"^https?://", "", url, flags=re.I).split("/")[0].split("?")[0].split(":")[0]
    return host.lower().removeprefix("www.")


def link_hit(content: str, trigger: dict) -> str | None:
    hosts = [_host(match) for match in _URL.findall(content or "")]
    hosts = [host for host in hosts if host]
    if not hosts:
        return None
    allow = {str(item).lower().removeprefix("www.") for item in trigger.get("allow") or []}
    deny = {str(item).lower().removeprefix("www.") for item in trigger.get("deny") or []}
    mode = str(trigger.get("mode") or "block")
    for host in hosts:
        if host in deny or any(host.endswith("." + item) for item in deny):
            return host
        if mode == "block" and host not in allow and not any(host.endswith("." + item) for item in allow):
            return host
    return None


def invite_hit(content: str, trigger: dict, *, own_codes: set[str] | None = None) -> str | None:
    if not trigger.get("block_external", True):
        return None
    allow_codes = {str(item).lower() for item in trigger.get("allow_codes") or []}
    own = {str(item).lower() for item in (own_codes or set())}
    for code in _INVITE.findall(content or ""):
        token = code.lower()
        if token in allow_codes:
            continue
        if trigger.get("allow_own", True) and token in own:
            continue
        return token
    return None


def caps_hit(content: str, trigger: dict) -> dict | None:
    min_length = int(trigger.get("min_length") or 8)
    if len(content or "") < min_length:
        return None
    letters = [char for char in content if char.isalpha()]
    if not letters:
        return None
    percent = int(trigger.get("percent") or 70)
    actual = round(100 * sum(char.isupper() for char in letters) / len(letters))
    if actual >= percent:
        return {"percent": actual, "minimum": percent, "min_length": min_length}
    return None


def emoji_count(content: str) -> int:
    return len(_CUSTOM_EMOJI.findall(content or "")) + len(_UNICODE_EMOJI.findall(content or ""))


def mention_hit(content: str, trigger: dict) -> dict | None:
    users = len(_USER_MENTION.findall(content or ""))
    roles = len(_ROLE_MENTION.findall(content or ""))
    everyone = "@everyone" in (content or "") or "@here" in (content or "")
    threshold = int(trigger.get("count") or 5)
    if trigger.get("everyone", True) and everyone:
        return {"mentions": users + roles, "everyone": True, "threshold": threshold}
    if users + roles >= threshold:
        return {"mentions": users + roles, "everyone": False, "threshold": threshold}
    return None


def attachment_hit(names: list[str], content_types: list[str], trigger: dict, *, has_text: bool) -> str | None:
    policy = str(trigger.get("policy") or "allow")
    files = list(names or [])
    if policy in {"allow", ""}:
        return None
    images = []
    others = []
    for index, name in enumerate(files):
        kind = (content_types[index] if index < len(content_types) else "") or ""
        lower = name.lower()
        image = kind.startswith("image/") or lower.endswith((".png", ".jpg", ".jpeg", ".gif", ".webp"))
        (images if image else others).append(name)
    if policy == "block" and files:
        return "attachments are blocked"
    if policy == "images_only" and others:
        return "only images are allowed"
    if policy == "attachments_only" and has_text and not files:
        return "this channel allows attachments only"
    if policy == "image_channel" and (others or not images):
        return "this channel allows images only"
    return None


def flood_span(stamps: list[float], now: float, count: int, window: float) -> float | None:
    recent = [stamp for stamp in stamps if now - stamp <= window]
    recent.append(now)
    if len(recent) < count:
        return None
    return max(0.0, now - recent[-count])


def duplicate_count(history: list[tuple[float, str]], now: float, text: str, window: float, *, normalized: bool) -> int:
    token = normalize_duplicate(text) if normalized else (text or "")
    if not token:
        return 0
    hits = [item for item in history if now - item[0] <= window and item[1] == token]
    return len(hits) + 1


def plan_actions(rule: dict) -> list[dict[str, Any]]:
    planned: list[dict[str, Any]] = []
    if rule.get("message_action") == "delete":
        planned.append({"kind": "delete", "label": "Delete message", "duration_seconds": None})
    member = str(rule.get("member_action") or "none")
    if member == "warn":
        planned.append({"kind": "warn", "label": "Warn", "duration_seconds": None})
    elif member == "timeout":
        seconds = int(rule.get("timeout_seconds") or 600)
        planned.append({"kind": "timeout", "label": f"Timeout {_duration_label(seconds)}", "duration_seconds": seconds})
    elif member == "kick":
        planned.append({"kind": "kick", "label": "Kick", "duration_seconds": None})
    elif member == "ban":
        planned.append({"kind": "ban", "label": "Ban", "duration_seconds": None})
    notify = str(rule.get("notify_action") or "none")
    if notify in {"dm", "both"}:
        planned.append({"kind": "dm", "label": "DM", "duration_seconds": None})
    if notify in {"channel", "both"}:
        planned.append({"kind": "notice", "label": "Channel notice", "duration_seconds": None})
    return planned


def _duration_label(seconds: int) -> str:
    if seconds % 86400 == 0:
        days = seconds // 86400
        return f"{days}d"
    if seconds % 3600 == 0:
        return f"{seconds // 3600}h"
    if seconds % 60 == 0:
        return f"{seconds // 60}m"
    return f"{seconds}s"


def result(kind: str, label: str, outcome: str, reason: str, *, discord_error: str | None = None) -> dict[str, Any]:
    return {
        "kind": kind,
        "label": label,
        "outcome": outcome,
        "reason": reason,
        "discord_error": discord_error,
        "context": label,
    }


def gate_action(action: dict, *, perms: dict, is_owner: bool, is_admin: bool, hierarchy_ok: bool) -> dict | None:
    kind = action["kind"]
    if kind in {"warn", "timeout", "kick", "ban"} and is_owner:
        return result(kind, action["label"], "skipped", "CLS cannot punish the server owner.")
    if kind in {"timeout", "kick", "ban"} and is_admin:
        return result(kind, action["label"], "failed", "CLS cannot punish an administrator.")
    if kind in {"timeout", "kick", "ban"} and not hierarchy_ok:
        return result(kind, action["label"], "failed", "CLS role is below the member's highest role")
    needed = {
        "delete": "manage_messages",
        "timeout": "moderate_members",
        "kick": "kick_members",
        "ban": "ban_members",
        "notice": "send_messages",
    }.get(kind)
    labels = {
        "manage_messages": "Manage Messages",
        "moderate_members": "Moderate Members",
        "kick_members": "Kick Members",
        "ban_members": "Ban Members",
        "send_messages": "Send Messages",
    }
    if needed and not perms.get(needed, False):
        return result(kind, action["label"], "failed", f"CLS needs the {labels[needed]} permission.")
    if kind == "timeout":
        seconds = int(action.get("duration_seconds") or 0)
        if seconds < TIMEOUT_MIN or seconds > TIMEOUT_MAX:
            return result(kind, action["label"], "failed", "Timeout must be between 60 seconds and 28 days.")
    return None


def highest_escalation(strikes: list[dict], thresholds: list[dict], now: float) -> dict | None:
    """One action: the highest matching threshold. No cascade."""
    ordered = sorted(
        thresholds or [],
        key=lambda row: (
            int(row.get("points") or 0),
            _SEVERITY.get(str(row.get("action")), 0),
            int(row.get("duration_seconds") or 0),
        ),
        reverse=True,
    )
    active = [row for row in strikes if float(row.get("expires_at") or now) >= now]
    for threshold in ordered:
        window = float(threshold.get("window_seconds") or 0)
        points = int(threshold.get("points") or 0)
        if points <= 0 or window <= 0:
            continue
        total = sum(int(row.get("points") or 0) for row in active if now - float(row["created_at"]) <= window)
        if total >= points:
            return threshold
    return None


def detect_content(rule: dict, content: str, *, attachments: list[dict] | None = None, own_codes: set[str] | None = None) -> dict | None:
    rule_id = rule.get("id")
    trigger = rule.get("trigger") or {}
    files = attachments or []
    names = [str(item.get("filename") or "") for item in files]
    types = [str(item.get("content_type") or "") for item in files]
    if rule_id == "caps":
        hit = caps_hit(content, trigger)
        if not hit:
            return None
        return {"summary": f"used {hit['percent']}% caps", "excerpt": _clip(content), "threshold": hit}
    if rule_id == "mentions":
        hit = mention_hit(content, trigger)
        if not hit:
            return None
        why = "@everyone/@here" if hit["everyone"] else f"{hit['mentions']} mentions"
        return {"summary": f"sent {why}", "excerpt": _clip(content), "threshold": hit}
    if rule_id == "emoji":
        count = emoji_count(content)
        need = int(trigger.get("count") or 8)
        if count < need:
            return None
        return {"summary": f"sent {count} emoji", "excerpt": _clip(content), "threshold": {"count": count, "minimum": need}}
    if rule_id == "links":
        host = link_hit(content, trigger)
        if not host:
            return None
        return {"summary": f"posted {host}", "excerpt": host, "threshold": {"mode": trigger.get("mode") or "block", "host": host}}
    if rule_id == "invites":
        code = invite_hit(content, trigger, own_codes=own_codes)
        if not code:
            return None
        return {"summary": f"posted an invite ({code})", "excerpt": "discord.gg/" + code, "threshold": {"code": code}}
    if rule_id == "bad_words":
        term = bad_word_hit(content, trigger)
        if not term:
            return None
        return {"summary": "used a blocked word", "excerpt": "•••", "threshold": {"mode": trigger.get("mode") or "whole"}}
    if rule_id == "keyword":
        term = bad_word_hit(content, {"terms": trigger.get("phrases") or [], "mode": trigger.get("mode") or "contains", "exceptions": []})
        if not term:
            return None
        return {"summary": "matched a keyword", "excerpt": _clip(term, 40), "threshold": {"mode": trigger.get("mode") or "contains"}}
    if rule_id == "attachments":
        reason = attachment_hit(names, types, trigger, has_text=bool((content or "").strip()))
        if not reason:
            return None
        return {"summary": reason, "excerpt": ", ".join(names)[:80], "threshold": {"policy": trigger.get("policy")}}
    return None


def evaluate_message(
    config: dict,
    *,
    content: str,
    ctx: dict,
    flood_stamps: list[float] | None = None,
    duplicate_history: list[tuple[float, str]] | None = None,
    now: float = 0,
    attachments: list[dict] | None = None,
    own_codes: set[str] | None = None,
) -> list[dict]:
    """Matches only. Does not punish. Each hit includes the actions that would run."""
    if not config.get("enabled"):
        return []
    found = []
    for rule in config.get("rules") or []:
        if not rule.get("enabled") or rule.get("engine") not in ENGINES:
            continue
        reason = scope_reason(config.get("exclusions") or {}, rule, ctx)
        if reason:
            continue
        rule_id = rule.get("id")
        trigger = rule.get("trigger") or {}
        match = None
        if rule_id == "flood":
            span = flood_span(
                list(flood_stamps or []),
                now,
                int(trigger.get("count") or 5),
                float(trigger.get("window_seconds") or 5),
            )
            if span is not None:
                match = {
                    "summary": f"sent {int(trigger.get('count') or 5)} messages in {span:.1f}s",
                    "excerpt": _clip(content),
                    "threshold": {"count": int(trigger.get("count") or 5), "window_seconds": trigger.get("window_seconds"), "span": round(span, 1)},
                }
        elif rule_id == "duplicate":
            count = duplicate_count(
                list(duplicate_history or []),
                now,
                content,
                float(trigger.get("window_seconds") or 30),
                normalized=bool(trigger.get("normalized", True)),
            )
            need = int(trigger.get("count") or 3)
            if count >= need:
                match = {
                    "summary": f"repeated a message {count} times",
                    "excerpt": _clip(content),
                    "threshold": {"count": count, "minimum": need, "normalized": bool(trigger.get("normalized", True))},
                }
        else:
            match = detect_content(rule, content, attachments=attachments, own_codes=own_codes)
        if match is None:
            continue
        actions = plan_actions(rule)
        if rule.get("mode") == "observe":
            actions = [
                result(item["kind"], item["label"], "skipped", "Observe mode records the match and does not punish.")
                for item in actions
            ]
        found.append(
            {
                "rule_id": rule_id,
                "name": rule.get("name") or RULE_NAMES.get(rule_id, rule_id),
                "mode": rule.get("mode") or "enforce",
                "engine": "cls",
                "summary": match["summary"],
                "excerpt": match["excerpt"],
                "threshold": match["threshold"],
                "scope": rule.get("scope") or empty_scope(),
                "actions": actions,
                "points": int(rule.get("points") or 0),
            }
        )
    return found


def validate_config(body: dict) -> dict[str, Any]:
    """Return a normalized config or raise ValueError with a human message."""
    preset = str(body.get("preset") or "custom")
    if preset not in PRESETS:
        raise ValueError("Preset must be Relaxed, Balanced, Strict, or Custom.")
    rules_in = {str(item.get("id")): item for item in body.get("rules") or []}
    base = {rule["id"]: rule for rule in fresh_config("balanced")["rules"]}
    normalized_rules = []
    for rule_id in RULE_IDS:
        incoming = rules_in.get(rule_id) or base[rule_id]
        trigger = dict(base[rule_id]["trigger"])
        trigger.update(dict(incoming.get("trigger") or {}))
        member = str(incoming.get("member_action") or "none")
        message = str(incoming.get("message_action") or "keep")
        notify = str(incoming.get("notify_action") or "none")
        mode = str(incoming.get("mode") or "enforce")
        if member not in MEMBER_ACTIONS or message not in MESSAGE_ACTIONS or notify not in NOTIFY_ACTIONS or mode not in MODES:
            raise ValueError(f"{RULE_NAMES[rule_id]} has an unknown action.")
        timeout = int(incoming.get("timeout_seconds") or 600)
        if member == "timeout" and (timeout < TIMEOUT_MIN or timeout > TIMEOUT_MAX):
            raise ValueError("Timeout must be between 60 seconds and 28 days.")
        points = int(incoming.get("points") or 0)
        if points < 0 or points > 100:
            raise ValueError("Strike points must be between 0 and 100.")
        scope = empty_scope()
        for key in scope:
            scope[key] = [str(item) for item in id_set((incoming.get("scope") or {}).get(key))]
        normalized_rules.append(
            {
                **base[rule_id],
                "enabled": bool(incoming.get("enabled")),
                "engine": "cls",
                "mode": mode,
                "trigger": _clean_trigger(rule_id, trigger),
                "scope": scope,
                "message_action": message,
                "member_action": member,
                "timeout_seconds": timeout,
                "notify_action": notify,
                "points": points,
            }
        )
    exclusions = empty_exclusions()
    raw_exclusions = body.get("exclusions") or {}
    for key in exclusions:
        exclusions[key] = [str(item) for item in id_set(raw_exclusions.get(key))]
    escalations = []
    for row in body.get("escalations") or []:
        action = str(row.get("action") or "")
        if action not in ESCALATION_ACTIONS:
            raise ValueError("Escalation actions are timeout, kick, or ban.")
        points = int(row.get("points") or 0)
        window = int(row.get("window_seconds") or 0)
        if points <= 0 or window <= 0:
            raise ValueError("Each escalation needs points and a time window.")
        duration = row.get("duration_seconds")
        duration_value = int(duration) if duration else None
        if action == "timeout" and (duration_value is None or duration_value < TIMEOUT_MIN or duration_value > TIMEOUT_MAX):
            raise ValueError("Escalation timeout must be between 60 seconds and 28 days.")
        escalations.append(
            {"points": points, "window_seconds": window, "action": action, "duration_seconds": duration_value}
        )
    ttl = int(body.get("strike_ttl_seconds") or 7 * 86400)
    if ttl < 60:
        raise ValueError("Strike expiry must be at least 60 seconds.")
    return {
        "enabled": bool(body.get("enabled")),
        "preset": preset,
        "exclusions": exclusions,
        "escalations": escalations,
        "strike_ttl_seconds": ttl,
        "rules": normalized_rules,
    }


def _clean_trigger(rule_id: str, trigger: dict) -> dict:
    if rule_id == "flood":
        return {
            "count": max(2, int(trigger.get("count") or 5)),
            "window_seconds": max(1, int(trigger.get("window_seconds") or 5)),
            "per_channel": bool(trigger.get("per_channel")),
        }
    if rule_id == "duplicate":
        return {
            "count": max(2, int(trigger.get("count") or 3)),
            "window_seconds": max(1, int(trigger.get("window_seconds") or 30)),
            "normalized": bool(trigger.get("normalized", True)),
        }
    if rule_id == "caps":
        return {"percent": min(100, max(1, int(trigger.get("percent") or 70))), "min_length": max(1, int(trigger.get("min_length") or 8))}
    if rule_id == "mentions":
        return {"count": max(1, int(trigger.get("count") or 5)), "everyone": bool(trigger.get("everyone", True))}
    if rule_id == "emoji":
        return {"count": max(1, int(trigger.get("count") or 8))}
    if rule_id == "links":
        mode = str(trigger.get("mode") or "block")
        return {
            "mode": mode if mode in {"block", "allow"} else "block",
            "allow": _domains(trigger.get("allow")),
            "deny": _domains(trigger.get("deny")),
        }
    if rule_id == "invites":
        return {
            "block_external": bool(trigger.get("block_external", True)),
            "allow_own": bool(trigger.get("allow_own", True)),
            "allow_guilds": [str(item) for item in id_set(trigger.get("allow_guilds"))],
            "allow_codes": [str(item).strip().lower() for item in trigger.get("allow_codes") or [] if str(item).strip()],
        }
    if rule_id in {"bad_words", "keyword"}:
        mode = str(trigger.get("mode") or ("whole" if rule_id == "bad_words" else "contains"))
        allowed = {"whole", "contains", "wildcard"}
        key = "terms" if rule_id == "bad_words" else "phrases"
        values = [str(item).strip() for item in trigger.get(key) or [] if str(item).strip()]
        cleaned = {
            "mode": mode if mode in allowed else "contains",
            key: values[:200],
        }
        if rule_id == "bad_words":
            cleaned["exceptions"] = [str(item).strip() for item in trigger.get("exceptions") or [] if str(item).strip()][:200]
        return cleaned
    policy = str(trigger.get("policy") or "allow")
    if policy not in {"allow", "block", "images_only", "attachments_only", "image_channel"}:
        policy = "allow"
    return {"policy": policy}


def _domains(values: Any) -> list[str]:
    found = []
    for item in values or []:
        host = str(item).strip().lower().removeprefix("www.")
        if host and re.fullmatch(r"[a-z0-9.-]{1,253}", host):
            found.append(host)
    return found[:100]


def followups_for(rule_id: str) -> list[dict[str, str]]:
    options = {
        "channel_exclusion": "Add a channel exclusion",
        "role_exclusion": "Add a role exclusion",
        "keyword_exception": "Add a keyword exception",
        "domain_allowlist": "Add a domain allowlist",
    }
    keys = ["channel_exclusion", "role_exclusion"]
    if rule_id in {"bad_words", "keyword"}:
        keys.append("keyword_exception")
    if rule_id == "links":
        keys.append("domain_allowlist")
    return [{"kind": key, "label": options[key]} for key in keys]


def exclusion_count(rule: dict, exclusions: dict) -> int:
    scope = rule.get("scope") or {}
    return sum(len(scope.get(key) or []) for key in scope) + sum(len(exclusions.get(key) or []) for key in ("channels", "categories", "roles", "members", "staff_roles"))
