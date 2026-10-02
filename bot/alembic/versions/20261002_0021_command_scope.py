"""Command policy channel and blocked-role scope."""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "20261002_0021"
down_revision: Union[str, None] = "20261002_0020"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("command_policies", sa.Column("blocked_role_ids", postgresql.ARRAY(sa.BigInteger()), nullable=False, server_default="{}"))
    op.add_column("command_policies", sa.Column("allowed_channel_ids", postgresql.ARRAY(sa.BigInteger()), nullable=False, server_default="{}"))
    op.add_column("command_policies", sa.Column("blocked_channel_ids", postgresql.ARRAY(sa.BigInteger()), nullable=False, server_default="{}"))


def downgrade() -> None:
    op.drop_column("command_policies", "blocked_channel_ids")
    op.drop_column("command_policies", "allowed_channel_ids")
    op.drop_column("command_policies", "blocked_role_ids")
