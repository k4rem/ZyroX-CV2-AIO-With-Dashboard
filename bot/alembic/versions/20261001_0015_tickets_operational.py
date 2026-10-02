"""Tickets V2 operational columns: teams, publish state, messages, HTML transcripts."""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "20261001_0015"
down_revision: Union[str, None] = "20261001_0014"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("ticket_categories_v2", sa.Column("ping_staff", sa.Boolean(), nullable=False, server_default=sa.text("true")))
    op.add_column("ticket_panels_v2", sa.Column("payload", postgresql.JSONB(), nullable=True))
    op.add_column(
        "ticket_panels_v2",
        sa.Column("required_role_ids", postgresql.ARRAY(sa.BigInteger()), nullable=False, server_default="{}"),
    )
    op.add_column(
        "ticket_panels_v2",
        sa.Column("blocked_role_ids", postgresql.ARRAY(sa.BigInteger()), nullable=False, server_default="{}"),
    )
    op.add_column("ticket_panels_v2", sa.Column("published_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column(
        "ticket_panels_v2",
        sa.Column("publish_status", sa.String(16), nullable=False, server_default="draft"),
    )
    op.add_column("ticket_questions_v2", sa.Column("placeholder", sa.Text(), nullable=False, server_default=""))
    op.add_column("ticket_questions_v2", sa.Column("min_length", sa.Integer(), nullable=False, server_default="0"))
    op.add_column("ticket_questions_v2", sa.Column("max_length", sa.Integer(), nullable=False, server_default="1000"))
    op.add_column("ticket_settings_v2", sa.Column("auto_close_hours", sa.Integer(), nullable=True))
    op.add_column("ticket_settings_v2", sa.Column("grace_minutes", sa.Integer(), nullable=False, server_default="60"))
    op.add_column("ticket_settings_v2", sa.Column("transcript_channel_id", sa.BigInteger(), nullable=True))
    op.add_column("tickets_v2", sa.Column("closed_by", sa.BigInteger(), nullable=True))
    op.add_column("tickets_v2", sa.Column("control_message_id", sa.BigInteger(), nullable=True))
    op.add_column("tickets_v2", sa.Column("panel_id", postgresql.UUID(as_uuid=True), nullable=True))
    op.add_column("tickets_v2", sa.Column("last_activity_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("tickets_v2", sa.Column("activity_generation", sa.Integer(), nullable=False, server_default="0"))
    op.add_column("tickets_v2", sa.Column("degraded", sa.Boolean(), nullable=False, server_default=sa.text("false")))
    op.create_table(
        "ticket_participants_v2",
        sa.Column("ticket_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("tickets_v2.id"), nullable=False),
        sa.Column("user_id", sa.BigInteger(), nullable=False),
        sa.Column("added_by", sa.BigInteger(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("ticket_id", "user_id"),
    )
    op.create_table(
        "ticket_messages_v2",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("ticket_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("tickets_v2.id"), nullable=False),
        sa.Column("guild_id", sa.BigInteger(), nullable=False),
        sa.Column("message_id", sa.BigInteger(), nullable=False),
        sa.Column("author_id", sa.BigInteger(), nullable=False),
        sa.Column("author_name", sa.Text(), nullable=False, server_default=""),
        sa.Column("display_name", sa.Text(), nullable=False, server_default=""),
        sa.Column("avatar", sa.Text(), nullable=False, server_default=""),
        sa.Column("content", sa.Text(), nullable=False, server_default=""),
        sa.Column("attachments", postgresql.JSONB(), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("embeds", postgresql.JSONB(), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("reference_id", sa.BigInteger(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.UniqueConstraint("guild_id", "message_id", name="uq_ticket_messages_v2_message"),
    )
    op.create_table(
        "ticket_html_v2",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("ticket_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("tickets_v2.id"), nullable=False),
        sa.Column("guild_id", sa.BigInteger(), nullable=False),
        sa.Column("html", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("ticket_html_v2")
    op.drop_table("ticket_messages_v2")
    op.drop_table("ticket_participants_v2")
    op.drop_column("tickets_v2", "degraded")
    op.drop_column("tickets_v2", "activity_generation")
    op.drop_column("tickets_v2", "last_activity_at")
    op.drop_column("tickets_v2", "panel_id")
    op.drop_column("tickets_v2", "control_message_id")
    op.drop_column("tickets_v2", "closed_by")
    op.drop_column("ticket_settings_v2", "transcript_channel_id")
    op.drop_column("ticket_settings_v2", "grace_minutes")
    op.drop_column("ticket_settings_v2", "auto_close_hours")
    op.drop_column("ticket_questions_v2", "max_length")
    op.drop_column("ticket_questions_v2", "min_length")
    op.drop_column("ticket_questions_v2", "placeholder")
    op.drop_column("ticket_panels_v2", "publish_status")
    op.drop_column("ticket_panels_v2", "published_at")
    op.drop_column("ticket_panels_v2", "blocked_role_ids")
    op.drop_column("ticket_panels_v2", "required_role_ids")
    op.drop_column("ticket_panels_v2", "payload")
    op.drop_column("ticket_categories_v2", "ping_staff")
