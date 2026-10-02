"""Giveaway prize details, eligibility, and published message."""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "20261002_0022"
down_revision: Union[str, None] = "20261002_0021"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("giveaways_v2", sa.Column("description", sa.String(500), nullable=False, server_default=""))
    op.add_column("giveaways_v2", sa.Column("winner_count", sa.Integer(), nullable=False, server_default="1"))
    op.add_column("giveaways_v2", sa.Column("required_role_id", sa.BigInteger(), nullable=True))
    op.add_column("giveaways_v2", sa.Column("blocked_role_id", sa.BigInteger(), nullable=True))
    op.add_column("giveaways_v2", sa.Column("host_id", sa.BigInteger(), nullable=True))
    op.add_column("giveaways_v2", sa.Column("message_id", sa.BigInteger(), nullable=True))
    op.add_column("giveaways_v2", sa.Column("starts_at", sa.DateTime(timezone=True), nullable=True))


def downgrade() -> None:
    op.drop_column("giveaways_v2", "starts_at")
    op.drop_column("giveaways_v2", "message_id")
    op.drop_column("giveaways_v2", "host_id")
    op.drop_column("giveaways_v2", "blocked_role_id")
    op.drop_column("giveaways_v2", "required_role_id")
    op.drop_column("giveaways_v2", "winner_count")
    op.drop_column("giveaways_v2", "description")
