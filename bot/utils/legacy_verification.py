"""Phase 0 containment for unsafe legacy verification mutations."""

from __future__ import annotations

from .env_parse import parse_env_bool

LEGACY_VERIFICATION_ENABLED: bool = parse_env_bool(
    "LEGACY_VERIFICATION_ENABLED", "false"
)

LEGACY_VERIFICATION_DISABLED_USER_MESSAGE = (
    "Legacy verification changes are disabled (LEGACY_VERIFICATION_ENABLED=false) "
    "pending Verification V2. Read-only commands like status and logs still work."
)


def legacy_verification_mutations_allowed() -> bool:
    return LEGACY_VERIFICATION_ENABLED


def legacy_verification_block_reason() -> str | None:
    if LEGACY_VERIFICATION_ENABLED:
        return None
    return LEGACY_VERIFICATION_DISABLED_USER_MESSAGE
