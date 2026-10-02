"""Auto react rules."""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "20261002_0024"
down_revision: Union[str, None] = "20261002_0023"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "autoreact_rules_v2",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("guild_id", sa.BigInteger(), nullable=False),
        sa.Column("name", sa.String(80), nullable=False),
        sa.Column("enabled", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("scope", sa.String(16), nullable=False, server_default="all"),
        sa.Column("channel_ids", postgresql.ARRAY(sa.BigInteger()), nullable=False, server_default="{}"),
        sa.Column("mode", sa.String(16), nullable=False, server_default="contains"),
        sa.Column("pattern", sa.String(200), nullable=False, server_default=""),
        sa.Column("emojis", postgresql.ARRAY(sa.String(80)), nullable=False, server_default="{}"),
    )
    op.create_index("ix_autoreact_rules_v2_guild", "autoreact_rules_v2", ["guild_id"])


def downgrade() -> None:
    op.drop_index("ix_autoreact_rules_v2_guild", table_name="autoreact_rules_v2")
    op.drop_table("autoreact_rules_v2")
