"""Postgres role menus."""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "20261002_0017"
down_revision: Union[str, None] = "20261001_0016"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "role_menus",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("guild_id", sa.BigInteger(), nullable=False),
        sa.Column("name", sa.String(80), nullable=False),
        sa.Column("channel_id", sa.BigInteger(), nullable=True),
        sa.Column("message_id", sa.BigInteger(), nullable=True),
        sa.Column("source", sa.String(16), nullable=False, server_default="created"),
        sa.Column("menu_type", sa.String(16), nullable=False, server_default="reaction"),
        sa.Column("mode", sa.String(16), nullable=False, server_default="toggle"),
        sa.Column("enabled", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("max_roles", sa.Integer(), nullable=True),
        sa.Column("payload", postgresql.JSONB(), nullable=True),
        sa.Column("publish_status", sa.String(16), nullable=False, server_default="draft"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_role_menus_guild", "role_menus", ["guild_id"])
    op.create_index("ix_role_menus_message", "role_menus", ["guild_id", "message_id"])
    op.create_table(
        "role_menu_options",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("menu_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("role_menus.id", ondelete="CASCADE"), nullable=False),
        sa.Column("role_id", sa.BigInteger(), nullable=False),
        sa.Column("emoji", sa.String(80), nullable=False, server_default=""),
        sa.Column("label", sa.String(80), nullable=False, server_default=""),
        sa.Column("description", sa.String(100), nullable=False, server_default=""),
        sa.Column("position", sa.Integer(), nullable=False, server_default="0"),
    )
    op.create_index("ix_role_menu_options_menu", "role_menu_options", ["menu_id"])


def downgrade() -> None:
    op.drop_index("ix_role_menu_options_menu", table_name="role_menu_options")
    op.drop_table("role_menu_options")
    op.drop_index("ix_role_menus_message", table_name="role_menus")
    op.drop_index("ix_role_menus_guild", table_name="role_menus")
    op.drop_table("role_menus")
