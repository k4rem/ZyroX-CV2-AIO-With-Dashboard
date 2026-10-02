"""Resource matching. Cross-guild imports never reuse a source Snowflake."""

from __future__ import annotations

from cls_platform.config_transfer.schema import EMOJI, MODULES, module_label, snowflake

KINDS = {"role", "channel", "category", "emoji"}


def normalize(name: str) -> str:
    return " ".join((name or "").strip().lower().split())


def collect_refs(value, found: list[dict] | None = None) -> list[dict]:
    rows = found if found is not None else []
    if isinstance(value, dict) and value.get("type") in KINDS and str(value.get("source_id") or "").isdigit():
        rows.append({"type": value["type"], "source_id": str(value["source_id"]), "name": value.get("name") or ""})
        return rows
    if isinstance(value, dict):
        for item in value.values():
            collect_refs(item, rows)
    elif isinstance(value, list):
        for item in value:
            collect_refs(item, rows)
    elif isinstance(value, str):
        for match in EMOJI.finditer(value):
            rows.append({"type": "emoji", "source_id": match.group(2), "name": match.group(1)})
    return rows


def unique_refs(modules: dict, selected: list[str]) -> list[dict]:
    seen = {}
    for module_id in selected:
        for ref in collect_refs(modules.get(module_id) or {}):
            key = f"{ref['type']}:{ref['source_id']}"
            current = seen.get(key)
            if current is None or (not current["name"] and ref["name"]):
                seen[key] = ref
    return list(seen.values())


def _named(catalog: dict, kind: str) -> list[dict]:
    if kind == "category":
        return [item for item in catalog.get("channels") or [] if item.get("kind") == "category"]
    if kind == "channel":
        return [item for item in catalog.get("channels") or [] if item.get("kind") != "category"]
    return list(catalog.get(f"{kind}s") or catalog.get(kind) or [])


def decide(ref: dict, *, same_guild: bool, catalog: dict, choice: dict | None) -> dict:
    """Return one mapping row. A choice of map/skip/unicode overrides auto-match."""
    key = f"{ref['type']}:{ref['source_id']}"
    if choice and choice.get("action") == "skip":
        return {**ref, "key": key, "status": "skip", "target_id": None, "detail": "Skipped"}
    if choice and choice.get("action") == "unicode" and ref["type"] == "emoji":
        emoji = str(choice.get("emoji") or "")
        if not emoji or emoji.startswith("<"):
            return {**ref, "key": key, "status": "needs_mapping", "target_id": None, "detail": "Choose a Unicode emoji"}
        return {**ref, "key": key, "status": "resolved", "target_id": emoji, "detail": "Replaced with a Unicode emoji"}
    if choice and choice.get("action") == "map" and str(choice.get("target_id") or "").isdigit():
        target = str(choice["target_id"])
        if not _catalog_has(catalog, ref["type"], target):
            return {**ref, "key": key, "status": "missing", "target_id": None, "detail": "That target is not on this server"}
        return {**ref, "key": key, "status": "resolved", "target_id": target, "detail": "Mapped"}
    if same_guild and _catalog_has(catalog, ref["type"], ref["source_id"]):
        return {**ref, "key": key, "status": "resolved", "target_id": ref["source_id"], "detail": "Still on this server"}
    matches = [item for item in _named(catalog, ref["type"]) if normalize(item.get("name") or "") == normalize(ref.get("name") or "") and normalize(ref.get("name") or "")]
    if len(matches) == 1:
        return {**ref, "key": key, "status": "resolved", "target_id": str(matches[0]["id"]), "detail": "Matched by name"}
    if len(matches) > 1:
        return {**ref, "key": key, "status": "needs_mapping", "target_id": None, "detail": "More than one match. Choose one."}
    return {**ref, "key": key, "status": "missing", "target_id": None, "detail": "Missing on this server"}


def _catalog_has(catalog: dict, kind: str, source_id: str) -> bool:
    if kind == "emoji" and not str(source_id).isdigit():
        return True
    return any(str(item.get("id")) == str(source_id) for item in _named(catalog, kind))


def mapping_rows(modules: dict, selected: list[str], *, same_guild: bool, catalog: dict, choices: dict | None) -> list[dict]:
    rows = []
    for ref in unique_refs(modules, selected):
        row = decide(ref, same_guild=same_guild, catalog=catalog, choice=(choices or {}).get(f"{ref['type']}:{ref['source_id']}"))
        row["affects"] = consequences(modules, selected, ref)
        rows.append(row)
    return rows


def consequences(modules: dict, selected: list[str], ref: dict) -> list[str]:
    notes = []
    key = (ref["type"], ref["source_id"])
    for module_id in selected:
        count = _count(modules.get(module_id) or {}, key)
        if count:
            label = module_label(module_id)
            notes.append(f"{label} uses this {count} time" if count == 1 else f"{label} uses this {count} times")
    return notes


def _count(value, key: tuple[str, str], total: int = 0) -> int:
    if isinstance(value, dict) and value.get("type") == key[0] and str(value.get("source_id") or "") == key[1]:
        return total + 1
    if isinstance(value, dict):
        return sum(_count(item, key) for item in value.values()) + total
    if isinstance(value, list):
        return sum(_count(item, key) for item in value) + total
    if isinstance(value, str):
        return total + sum(1 for match in EMOJI.finditer(value) if match.group(2) == key[1] and key[0] == "emoji")
    return total


def apply_map(value, resolved: dict[str, dict]):
    """Replace resource refs with target ids. Skipped refs become None."""
    if isinstance(value, dict) and value.get("type") in KINDS and str(value.get("source_id") or "").isdigit():
        row = resolved.get(f"{value['type']}:{value['source_id']}")
        if row is None or row.get("status") == "skip":
            return None
        return row.get("target_id")
    if isinstance(value, dict):
        return {key: apply_map(item, resolved) for key, item in value.items()}
    if isinstance(value, list):
        return [apply_map(item, resolved) for item in value]
    if isinstance(value, str):
        def replacer(match):
            row = resolved.get(f"emoji:{match.group(2)}")
            if row is None or row.get("status") == "skip":
                return ""
            return str(row.get("target_id") or "")
        return EMOJI.sub(replacer, value)
    return value


def unresolved(rows: list[dict]) -> list[dict]:
    return [row for row in rows if row["status"] in {"needs_mapping", "missing"}]


def impact_for(module_id: str, current, incoming, resolved: dict[str, dict], blocked: str | None = None) -> dict:
    label = module_label(module_id)
    if incoming is None:
        return {"module": module_id, "label": label, "action": "skip", "detail": "Not in this backup"}
    mapped = apply_map(incoming, resolved)
    if blocked:
        return {"module": module_id, "label": label, "action": "blocked", "detail": blocked}
    if current in (None, {}, []) and _empty(mapped):
        return {"module": module_id, "label": label, "action": "unchanged", "detail": "Nothing to import"}
    if _same(current, mapped):
        return {"module": module_id, "label": label, "action": "unchanged", "detail": "Already matches"}
    action = "update" if not _empty(current) else "create"
    return {"module": module_id, "label": label, "action": action, "detail": _detail(module_id, mapped, action)}


def _empty(value) -> bool:
    if value in (None, {}, []):
        return True
    if isinstance(value, dict):
        return not any(value.get(key) for key in ("enabled", "templates", "rules", "menus", "panels", "categories", "triggers", "policies"))
    return False


def _same(current, mapped) -> bool:
    return _plain(current) == _plain(mapped)


def _plain(value):
    if isinstance(value, dict) and "source_id" in value and "type" in value:
        return snowflake(value)
    if isinstance(value, dict):
        return {key: _plain(item) for key, item in value.items() if key not in {"id", "exported_at"}}
    if isinstance(value, list):
        return [_plain(item) for item in value]
    return value


def blocked_detail(module_id: str, rows: list[dict]) -> str | None:
    label = module_label(module_id)
    for row in rows:
        if row["status"] not in {"needs_mapping", "missing"} or row["type"] != "emoji":
            continue
        if any(note.startswith(label) for note in row.get("affects") or []):
            return "Missing custom emoji"
    return None


def _detail(module_id: str, mapped, action: str) -> str:
    verb = "Create" if action == "create" else "Update"
    if module_id == "tickets":
        return f"{verb} {len(mapped.get('panels') or [])} panels"
    if module_id == "role_menus":
        return f"{verb} {len(mapped.get('menus') or [])} menus"
    if module_id == "role_automation":
        return f"{verb} {len(mapped.get('rules') or [])} rules"
    if module_id == "messages":
        return f"{verb} {len(mapped.get('templates') or [])} templates"
    return verb


def group_preview(summaries: dict[str, str]) -> list[dict]:
    built = []
    order = []
    for item in MODULES:
        if item["group"] not in order:
            order.append(item["group"])
    labels = {"messaging": "Messaging", "moderation": "Moderation", "support": "Support", "roles": "Roles", "engagement": "Engagement", "system": "System"}
    for group_id in order:
        built.append({
            "id": group_id,
            "label": labels[group_id],
            "modules": [
                {"id": item["id"], "label": item["label"], "summary": summaries.get(item["id"]) or "Not configured"}
                for item in MODULES
                if item["group"] == group_id
            ],
        })
    return built
