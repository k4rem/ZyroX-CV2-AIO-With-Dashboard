"""Verification V2 tables. Disabled until a guild is explicitly enabled."""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "20261001_0005"
down_revision: Union[str, None] = "20261001_0004"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "verification_configs",
        sa.Column("guild_id", sa.BigInteger(), primary_key=True),
        sa.Column("enabled", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("unverified_role_id", sa.BigInteger(), nullable=True),
        sa.Column("verified_role_id", sa.BigInteger(), nullable=True),
        sa.Column("channel_id", sa.BigInteger(), nullable=True),
        sa.Column("method", sa.String(16), nullable=False, server_default="button"),
        sa.Column("grace_seconds", sa.Integer(), nullable=False, server_default="604800"),
        sa.Column("message", sa.Text(), nullable=False, server_default=""),
        sa.Column("protected_category_ids", postgresql.ARRAY(sa.BigInteger()), nullable=False, server_default="{}"),
        sa.Column("enabled_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
    )
    op.create_table(
        "verification_members",
        sa.Column("guild_id", sa.BigInteger(), nullable=False),
        sa.Column("user_id", sa.BigInteger(), nullable=False),
        sa.Column("state", sa.String(16), nullable=False),
        sa.Column("grace_until", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("guild_id", "user_id"),
    )
    op.create_table(
        "verification_overwrite_backups",
        sa.Column("guild_id", sa.BigInteger(), nullable=False),
        sa.Column("category_id", sa.BigInteger(), nullable=False),
        sa.Column("role_id", sa.BigInteger(), nullable=False),
        sa.Column("had_overwrite", sa.Boolean(), nullable=False),
        sa.Column("allow_bits", sa.Text(), nullable=False, server_default="0"),
        sa.Column("deny_bits", sa.Text(), nullable=False, server_default="0"),
        sa.PrimaryKeyConstraint("guild_id", "category_id"),
    )


def downgrade() -> None:
    op.drop_table("verification_overwrite_backups")
    op.drop_table("verification_members")
    op.drop_table("verification_configs")
