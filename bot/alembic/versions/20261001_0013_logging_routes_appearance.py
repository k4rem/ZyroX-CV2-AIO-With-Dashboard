"""Per-event logging routes and appearance settings."""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "20261001_0013"
down_revision: Union[str, None] = "20261001_0012"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "log_event_routes",
        sa.Column("guild_id", sa.BigInteger(), primary_key=True),
        sa.Column("event_type", sa.String(64), primary_key=True),
        sa.Column("mode", sa.String(16), nullable=False),
        sa.Column("channel_id", sa.BigInteger(), nullable=True),
    )
    op.create_table(
        "log_appearance",
        sa.Column("guild_id", sa.BigInteger(), primary_key=True),
        sa.Column("style", sa.String(16), nullable=False, server_default="balanced"),
        sa.Column("show_avatars", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("show_moderator", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("show_jump", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("show_timestamp", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("show_ids", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("footer_mode", sa.String(16), nullable=False, server_default="cls"),
        sa.Column("footer_text", sa.String(80), nullable=True),
        sa.Column("colors", postgresql.JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
    )


def downgrade() -> None:
    op.drop_table("log_appearance")
    op.drop_table("log_event_routes")
