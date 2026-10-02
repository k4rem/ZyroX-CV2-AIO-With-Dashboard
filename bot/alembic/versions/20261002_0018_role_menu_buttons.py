"""Button interaction style for role menus. Existing rows stay single toggle."""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "20261002_0018"
down_revision: Union[str, None] = "20261002_0017"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("role_menus", sa.Column("button_style", sa.String(16), nullable=False, server_default="toggle"))


def downgrade() -> None:
    op.drop_column("role_menus", "button_style")
