"""Invite V2 history and persistent giveaways."""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "20261001_0011"
down_revision: Union[str, None] = "20261001_0010"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "invite_codes_v2",
        sa.Column("guild_id", sa.BigInteger(), primary_key=True),
        sa.Column("code", sa.String(32), primary_key=True),
        sa.Column("inviter_id", sa.BigInteger(), nullable=True),
        sa.Column("uses", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("vanity", sa.Boolean(), nullable=False, server_default=sa.text("false")),
    )
    op.create_table(
        "invite_joins_v2",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("guild_id", sa.BigInteger(), nullable=False),
        sa.Column("user_id", sa.BigInteger(), nullable=False),
        sa.Column("code", sa.String(32), nullable=True),
        sa.Column("status", sa.String(16), nullable=False),
        sa.Column("joined_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_invite_joins_v2_guild_time", "invite_joins_v2", ["guild_id", "joined_at"])
    op.create_table(
        "giveaways_v2",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("guild_id", sa.BigInteger(), nullable=False),
        sa.Column("channel_id", sa.BigInteger(), nullable=True),
        sa.Column("prize", sa.String(200), nullable=False),
        sa.Column("ends_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("status", sa.String(16), nullable=False),
        sa.Column("winner_ids", postgresql.ARRAY(sa.BigInteger()), nullable=False, server_default="{}"),
    )
    op.create_index("ix_giveaways_v2_due", "giveaways_v2", ["status", "ends_at"])
    op.create_table(
        "giveaway_entries_v2",
        sa.Column("giveaway_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("giveaways_v2.id"), primary_key=True),
        sa.Column("user_id", sa.BigInteger(), primary_key=True),
    )


def downgrade() -> None:
    op.drop_table("giveaway_entries_v2")
    op.drop_index("ix_giveaways_v2_due", table_name="giveaways_v2")
    op.drop_table("giveaways_v2")
    op.drop_index("ix_invite_joins_v2_guild_time", table_name="invite_joins_v2")
    op.drop_table("invite_joins_v2")
    op.drop_table("invite_codes_v2")
