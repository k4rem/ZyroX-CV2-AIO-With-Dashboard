"""Audit-log attribution. Never pick an actor from a tie."""

from __future__ import annotations


def classify_matches(matches: list[tuple[object, str | None]]) -> tuple[object | None, str, str | None, str | None]:
    """Return user, confidence, reason, note.

    One matching entry is certain.
    Several entries for the same user are probable.
    Several different users stay unknown and are marked ambiguous.
    """
    usable = [(user, reason) for user, reason in matches if getattr(user, "id", None)]
    if not usable:
        return None, "unknown", None, None
    if len(usable) == 1:
        return usable[0][0], "certain", usable[0][1], None
    ids = {user.id for user, _reason in usable}
    if len(ids) == 1:
        return usable[0][0], "probable", usable[0][1], None
    return None, "unknown", None, "ambiguous"
