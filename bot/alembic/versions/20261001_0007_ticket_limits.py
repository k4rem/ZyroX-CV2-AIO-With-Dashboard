"""Ticket creation cooldown and blacklist."""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "20261001_0007"
down_revision: Union[str, None] = "20261001_0006"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "ticket_settings_v2",
        sa.Column("guild_id", sa.BigInteger(), primary_key=True),
        sa.Column("cooldown_seconds", sa.Integer(), nullable=False, server_default="60"),
        sa.Column("max_open", sa.Integer(), nullable=False, server_default="1"),
    )
    op.create_table(
        "ticket_blacklist_v2",
        sa.Column("guild_id", sa.BigInteger(), primary_key=True),
        sa.Column("user_id", sa.BigInteger(), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_ticket_blacklist_v2_guild", "ticket_blacklist_v2", ["guild_id"])


def downgrade() -> None:
    op.drop_index("ix_ticket_blacklist_v2_guild", table_name="ticket_blacklist_v2")
    op.drop_table("ticket_blacklist_v2")
    op.drop_table("ticket_settings_v2")
