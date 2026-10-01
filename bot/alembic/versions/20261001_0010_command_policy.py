"""Per-guild command enablement and role restrictions."""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "20261001_0010"
down_revision: Union[str, None] = "20261001_0009"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "command_policies",
        sa.Column("guild_id", sa.BigInteger(), primary_key=True),
        sa.Column("command_name", sa.String(120), primary_key=True),
        sa.Column("enabled", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("allowed_role_ids", postgresql.ARRAY(sa.BigInteger()), nullable=False, server_default="{}"),
    )
    op.create_index("ix_command_policies_guild", "command_policies", ["guild_id"])


def downgrade() -> None:
    op.drop_index("ix_command_policies_guild", table_name="command_policies")
    op.drop_table("command_policies")
