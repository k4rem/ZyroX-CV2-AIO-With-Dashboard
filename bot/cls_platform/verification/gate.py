"""Deny view on protected categories for the unverified role, and restore the previous overwrite."""

from __future__ import annotations


def _bits(overwrite) -> tuple[str, str]:
    allow, deny = overwrite.pair()
    return str(allow.value), str(deny.value)


async def apply_category_denies(categories: list, role, *, reason: str) -> list[dict]:
    backups = []
    for category in categories:
        if category is None:
            raise LookupError("category_missing")
        previous = category.overwrites.get(role)
        if previous is None:
            allow_bits, deny_bits, had = "0", "0", False
        else:
            allow_bits, deny_bits = _bits(previous)
            had = True
        backups.append(
            {
                "category_id": int(category.id),
                "role_id": int(role.id),
                "had_overwrite": had,
                "allow_bits": allow_bits,
                "deny_bits": deny_bits,
            }
        )
        kwargs = {}
        if previous is not None:
            for name, value in previous:
                if value is not None:
                    kwargs[name] = value
        kwargs["view_channel"] = False
        await category.set_permissions(role, reason=reason, **kwargs)
    return backups


async def restore_category_denies(categories_by_id: dict, backups: list[dict], role, *, reason: str) -> None:
    for item in backups:
        category = categories_by_id.get(int(item["category_id"]))
        if category is None:
            continue
        if not item["had_overwrite"]:
            await category.set_permissions(role, overwrite=None, reason=reason)
            continue
        await category.set_permissions(
            role,
            overwrite=("restore", item["allow_bits"], item["deny_bits"]),
            reason=reason,
        )
