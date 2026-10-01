"""Response types only. No Discord mutation implementation exists in this pass."""

from __future__ import annotations

from typing import Protocol

from cls_platform.security.constants import ENFORCE_OPERATIONALLY_AVAILABLE


class EnforceUnavailable(RuntimeError):
    """ENFORCE and Discord containment are not operational before step 2A.6."""


class DiscordContainment(Protocol):
    """Future containment port. There is no implementation in Phase 2A.1–2A.4."""

    async def quarantine_member(self, guild_id: int, user_id: int, action_id: str) -> None: ...


def execute_discord_containment(*_args: object, **_kwargs: object) -> None:
    """Refuse every containment call. This function never talks to Discord."""
    if ENFORCE_OPERATIONALLY_AVAILABLE:
        raise EnforceUnavailable("ENFORCE flag is set without a containment implementation")
    raise EnforceUnavailable(
        "Discord containment is not implemented. OBSERVE may record would_contain only."
    )
