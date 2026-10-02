"""Dashboard fields for ticket panels, teams, blacklist, and opener snapshots."""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "20261001_0016"
down_revision: Union[str, None] = "20261001_0015"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("ticket_categories_v2", sa.Column("required_role_ids", postgresql.ARRAY(sa.BigInteger()), nullable=False, server_default="{}"))
    op.add_column("ticket_categories_v2", sa.Column("blocked_role_ids", postgresql.ARRAY(sa.BigInteger()), nullable=False, server_default="{}"))
    op.add_column("ticket_panels_v2", sa.Column("button_emoji", sa.String(80), nullable=False, server_default=""))
    op.add_column("ticket_panels_v2", sa.Column("button_style", sa.String(16), nullable=False, server_default="primary"))
    op.add_column("ticket_panels_v2", sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("tickets_v2", sa.Column("opener_name", sa.Text(), nullable=False, server_default=""))
    op.add_column("tickets_v2", sa.Column("opener_avatar", sa.Text(), nullable=False, server_default=""))
    op.add_column("ticket_settings_v2", sa.Column("name_format", sa.String(80), nullable=False, server_default="ticket-{number}-{username}"))
    op.add_column("ticket_blacklist_v2", sa.Column("reason", sa.Text(), nullable=False, server_default=""))
    op.add_column("ticket_blacklist_v2", sa.Column("actor_id", sa.BigInteger(), nullable=True))


def downgrade() -> None:
    op.drop_column("ticket_blacklist_v2", "actor_id")
    op.drop_column("ticket_blacklist_v2", "reason")
    op.drop_column("ticket_settings_v2", "name_format")
    op.drop_column("tickets_v2", "opener_avatar")
    op.drop_column("tickets_v2", "opener_name")
    op.drop_column("ticket_panels_v2", "updated_at")
    op.drop_column("ticket_panels_v2", "button_style")
    op.drop_column("ticket_panels_v2", "button_emoji")
    op.drop_column("ticket_categories_v2", "blocked_role_ids")
    op.drop_column("ticket_categories_v2", "required_role_ids")
