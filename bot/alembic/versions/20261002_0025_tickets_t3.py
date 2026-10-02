"""Tickets T3: priority, tags, notes, close requests, routing, hours, replies."""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "20261002_0025"
down_revision: Union[str, None] = "20261002_0024"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("tickets_v2", sa.Column("priority", sa.String(16), nullable=False, server_default="normal"))
    op.add_column("tickets_v2", sa.Column("close_requested_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("ticket_categories_v2", sa.Column("close_mode", sa.String(16), nullable=False, server_default="direct"))
    op.add_column("ticket_categories_v2", sa.Column("close_timeout_minutes", sa.Integer(), nullable=True))
    op.add_column("ticket_categories_v2", sa.Column("hours_mode", sa.String(16), nullable=False, server_default="always"))
    op.add_column("ticket_categories_v2", sa.Column("hours_timezone", sa.String(64), nullable=False, server_default="UTC"))
    op.add_column("ticket_categories_v2", sa.Column("hours_days", sa.Integer(), nullable=False, server_default="127"))
    op.add_column("ticket_categories_v2", sa.Column("hours_start", sa.String(5), nullable=False, server_default="09:00"))
    op.add_column("ticket_categories_v2", sa.Column("hours_end", sa.String(5), nullable=False, server_default="17:00"))
    op.add_column("ticket_categories_v2", sa.Column("hours_outside", sa.String(16), nullable=False, server_default="allow"))
    op.add_column("ticket_panels_v2", sa.Column("panel_type", sa.String(16), nullable=False, server_default="button"))
    op.create_table(
        "ticket_tags_v2",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("guild_id", sa.BigInteger(), nullable=False),
        sa.Column("name", sa.String(40), nullable=False),
        sa.Column("position", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("archived", sa.Boolean(), nullable=False, server_default=sa.text("false")),
    )
    op.create_table(
        "ticket_tag_links_v2",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("ticket_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("tickets_v2.id"), nullable=False),
        sa.Column("tag_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("ticket_tags_v2.id", ondelete="SET NULL"), nullable=True),
        sa.Column("name", sa.String(40), nullable=False),
    )
    op.create_table(
        "ticket_notes_v2",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("ticket_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("tickets_v2.id"), nullable=False),
        sa.Column("guild_id", sa.BigInteger(), nullable=False),
        sa.Column("author_id", sa.BigInteger(), nullable=False),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_table(
        "ticket_panel_options_v2",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("panel_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("ticket_panels_v2.id"), nullable=False),
        sa.Column("label", sa.String(80), nullable=False),
        sa.Column("description", sa.String(100), nullable=False, server_default=""),
        sa.Column("emoji", sa.String(80), nullable=False, server_default=""),
        sa.Column("category_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("position", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("questions", postgresql.JSONB(), nullable=False, server_default=sa.text("'[]'::jsonb")),
    )
    op.create_table(
        "ticket_routing_rules_v2",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("panel_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("ticket_panels_v2.id"), nullable=False),
        sa.Column("question_label", sa.String(80), nullable=False),
        sa.Column("operator", sa.String(16), nullable=False, server_default="equals"),
        sa.Column("value", sa.String(80), nullable=False),
        sa.Column("category_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("position", sa.Integer(), nullable=False, server_default="0"),
    )
    op.create_table(
        "ticket_replies_v2",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("guild_id", sa.BigInteger(), nullable=False),
        sa.Column("name", sa.String(80), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("position", sa.Integer(), nullable=False, server_default="0"),
    )


def downgrade() -> None:
    op.drop_table("ticket_replies_v2")
    op.drop_table("ticket_routing_rules_v2")
    op.drop_table("ticket_panel_options_v2")
    op.drop_table("ticket_notes_v2")
    op.drop_table("ticket_tag_links_v2")
    op.drop_table("ticket_tags_v2")
    op.drop_column("ticket_panels_v2", "panel_type")
    op.drop_column("ticket_categories_v2", "hours_outside")
    op.drop_column("ticket_categories_v2", "hours_end")
    op.drop_column("ticket_categories_v2", "hours_start")
    op.drop_column("ticket_categories_v2", "hours_days")
    op.drop_column("ticket_categories_v2", "hours_timezone")
    op.drop_column("ticket_categories_v2", "hours_mode")
    op.drop_column("ticket_categories_v2", "close_timeout_minutes")
    op.drop_column("ticket_categories_v2", "close_mode")
    op.drop_column("tickets_v2", "close_requested_at")
    op.drop_column("tickets_v2", "priority")
