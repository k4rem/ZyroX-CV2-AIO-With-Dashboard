"""Guild command module switches. Per-command policies stay untouched."""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "20261002_0029"
down_revision: Union[str, None] = "20261002_0028"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "command_module_states",
        sa.Column("guild_id", sa.BigInteger(), nullable=False),
        sa.Column("module_id", sa.String(length=40), nullable=False),
        sa.Column("enabled", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.PrimaryKeyConstraint("guild_id", "module_id"),
    )


def downgrade() -> None:
    op.drop_table("command_module_states")
