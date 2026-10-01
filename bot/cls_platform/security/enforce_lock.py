"""Production ENFORCE stays locked unless a disposable-test unlock is set."""

from __future__ import annotations

import os

from sqlalchemy import text

UNLOCK_ENV = "CLS_SECURITY_ENFORCE_UNLOCK"


def enforce_unlocked() -> bool:
    return os.getenv(UNLOCK_ENV) == "1"


async def arm_enforce_session(session) -> None:
    """Allow this transaction to persist ENFORCE rows. Local to the transaction."""
    if not enforce_unlocked():
        from cls_platform.security.response_protocol import EnforceUnavailable

        raise EnforceUnavailable(
            "ENFORCE is locked. Production stays OBSERVE until the owner sets the test unlock."
        )
    await session.execute(text("SELECT set_config('app.allow_enforce', 'on', true)"))
