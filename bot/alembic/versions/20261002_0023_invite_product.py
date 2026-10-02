"""Invite leave state and the log channel."""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "20261002_0023"
down_revision: Union[str, None] = "20261002_0022"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("invite_joins_v2", sa.Column("left_at", sa.DateTime(timezone=True), nullable=True))
    op.create_table(
        "invite_settings_v2",
        sa.Column("guild_id", sa.BigInteger(), primary_key=True),
        sa.Column("log_channel_id", sa.BigInteger(), nullable=True),
    )


def downgrade() -> None:
    op.drop_table("invite_settings_v2")
    op.drop_column("invite_joins_v2", "left_at")
