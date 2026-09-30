from __future__ import annotations

import uuid
from dataclasses import dataclass


@dataclass(frozen=True)
class DashboardAuthContext:
    user_id: int
    session_id: uuid.UUID
    is_root: bool
