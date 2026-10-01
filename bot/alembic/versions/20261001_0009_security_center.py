"""Security Center settings. Does not change Phase 2A enforcement tables."""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "20261001_0009"
down_revision: Union[str, None] = "20261001_0008"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "security_center_settings",
        sa.Column("guild_id", sa.BigInteger(), primary_key=True),
        sa.Column("dashboard_locked", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("phishing_action", sa.String(32), nullable=False, server_default="delete_timeout"),
        sa.Column("trap_channel_ids", postgresql.ARRAY(sa.BigInteger()), nullable=False, server_default="{}"),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("security_center_settings")
