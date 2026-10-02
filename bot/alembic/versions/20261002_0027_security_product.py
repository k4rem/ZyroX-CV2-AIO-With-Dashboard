"""Human honeypot channel and trust reason."""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "20261002_0027"
down_revision: Union[str, None] = "20261002_0026"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("security_center_settings", sa.Column("honeypot_channel_id", sa.BigInteger(), nullable=True))
    op.add_column("security_trusted_actors", sa.Column("reason", sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column("security_trusted_actors", "reason")
    op.drop_column("security_center_settings", "honeypot_channel_id")
