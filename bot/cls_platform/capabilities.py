"""Dashboard capability bundles (Phase 1 RBAC)."""

from __future__ import annotations

from typing import FrozenSet

# Root-only capabilities (never assignable via Dashboard roles)
ROOT_ONLY: FrozenSet[str] = frozenset({"rbac.manage"})

ALL_CAPABILITIES: tuple[str, ...] = (
    "guild.view",
    "tickets.config",
    "tickets.transcripts.view",
    "tickets.analytics.view",
    "moderation.config",
    "logging.view",
    "logging.config",
    "welcome.config",
    "j2c.config",
    "autorole.config",
    "reactionroles.config",
    "security.view",
    "security.config",
    "security.incidents.view",
    "audit.view",
    "giveaways.manage",
    "invites.manage",
    "bot.settings",
)

ADMIN_CAPS: list[str] = [c for c in ALL_CAPABILITIES if c not in ROOT_ONLY]
MODERATOR_CAPS: list[str] = [
    "guild.view",
    "moderation.config",
    "logging.view",
    "security.view",
    "security.incidents.view",
    "tickets.config",
    "tickets.transcripts.view",
    "audit.view",
]
SUPPORT_CAPS: list[str] = [
    "guild.view",
    "logging.view",
    "tickets.config",
    "tickets.transcripts.view",
    "tickets.analytics.view",
]

SYSTEM_ROLE_TEMPLATES: dict[str, list[str]] = {
    "admin": ADMIN_CAPS,
    "moderator": MODERATOR_CAPS,
    "support": SUPPORT_CAPS,
}
