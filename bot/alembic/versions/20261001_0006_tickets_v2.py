"""Tickets V2 tables. Legacy ticket.db is not written."""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "20261001_0006"
down_revision: Union[str, None] = "20261001_0005"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "ticket_categories_v2",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("guild_id", sa.BigInteger(), nullable=False),
        sa.Column("name", sa.String(80), nullable=False),
        sa.Column("discord_category_id", sa.BigInteger(), nullable=True),
        sa.Column("staff_role_ids", postgresql.ARRAY(sa.BigInteger()), nullable=False, server_default="{}"),
        sa.Column("name_format", sa.String(80), nullable=False, server_default="ticket-{number}"),
    )
    op.create_index("ix_ticket_categories_v2_guild", "ticket_categories_v2", ["guild_id"])
    op.create_table(
        "ticket_panels_v2",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("guild_id", sa.BigInteger(), nullable=False),
        sa.Column("category_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("ticket_categories_v2.id"), nullable=False),
        sa.Column("channel_id", sa.BigInteger(), nullable=True),
        sa.Column("title", sa.String(120), nullable=False),
        sa.Column("message", sa.Text(), nullable=False, server_default=""),
        sa.Column("button_label", sa.String(40), nullable=False, server_default="Open ticket"),
        sa.Column("published_message_id", sa.BigInteger(), nullable=True),
    )
    op.create_table(
        "ticket_questions_v2",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("panel_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("ticket_panels_v2.id"), nullable=False),
        sa.Column("label", sa.String(120), nullable=False),
        sa.Column("kind", sa.String(16), nullable=False),
        sa.Column("required", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("position", sa.Integer(), nullable=False, server_default="0"),
    )
    op.create_table(
        "tickets_v2",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("guild_id", sa.BigInteger(), nullable=False),
        sa.Column("category_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("ticket_categories_v2.id"), nullable=False),
        sa.Column("number", sa.Integer(), nullable=False),
        sa.Column("opener_id", sa.BigInteger(), nullable=False),
        sa.Column("channel_id", sa.BigInteger(), nullable=True),
        sa.Column("status", sa.String(16), nullable=False),
        sa.Column("assignee_id", sa.BigInteger(), nullable=True),
        sa.Column("close_reason", sa.Text(), nullable=True),
        sa.Column("opened_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("closed_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index(
        "uq_tickets_v2_open_opener",
        "tickets_v2",
        ["guild_id", "category_id", "opener_id"],
        unique=True,
        postgresql_where=sa.text("status = 'open'"),
    )
    op.create_table(
        "ticket_events_v2",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("ticket_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("tickets_v2.id"), nullable=False),
        sa.Column("guild_id", sa.BigInteger(), nullable=False),
        sa.Column("kind", sa.String(32), nullable=False),
        sa.Column("actor_id", sa.BigInteger(), nullable=True),
        sa.Column("payload", postgresql.JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_table(
        "ticket_transcript_v2",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("ticket_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("tickets_v2.id"), nullable=False),
        sa.Column("author_id", sa.BigInteger(), nullable=False),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("ticket_transcript_v2")
    op.drop_table("ticket_events_v2")
    op.drop_index("uq_tickets_v2_open_opener", table_name="tickets_v2")
    op.drop_table("tickets_v2")
    op.drop_table("ticket_questions_v2")
    op.drop_table("ticket_panels_v2")
    op.drop_index("ix_ticket_categories_v2_guild", table_name="ticket_categories_v2")
    op.drop_table("ticket_categories_v2")
