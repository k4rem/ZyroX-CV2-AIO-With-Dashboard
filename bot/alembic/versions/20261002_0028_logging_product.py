"""Per-event log appearance and exclusion scope."""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "20261002_0028"
down_revision: Union[str, None] = "20261002_0027"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "log_appearance",
        sa.Column("event_styles", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'{}'::jsonb")),
    )
    op.add_column(
        "log_appearance",
        sa.Column("ignore_scope", sa.String(length=16), nullable=False, server_default="messages"),
    )


def downgrade() -> None:
    op.drop_column("log_appearance", "ignore_scope")
    op.drop_column("log_appearance", "event_styles")
