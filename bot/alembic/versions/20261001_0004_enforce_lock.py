"""Allow ENFORCE rows only when the transaction sets app.allow_enforce.

Revision ID: 20261001_0004
Revises: 20261001_0003

Production never sets that GUC. Tests set it only after CLS_SECURITY_ENFORCE_UNLOCK=1.
"""

from __future__ import annotations

from typing import Sequence, Union

from alembic import op

revision: str = "20261001_0004"
down_revision: Union[str, None] = "20261001_0003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        """
        CREATE OR REPLACE FUNCTION security_reject_operational_enforce()
        RETURNS trigger
        LANGUAGE plpgsql
        AS $$
        BEGIN
          IF (NEW.human_mode = 'ENFORCE' OR NEW.bot_mode = 'ENFORCE')
             AND current_setting('app.allow_enforce', true) IS DISTINCT FROM 'on' THEN
            RAISE EXCEPTION 'ENFORCE is locked until app.allow_enforce is set for this transaction';
          END IF;
          RETURN NEW;
        END;
        $$
        """
    )
    op.execute(
        """
        CREATE OR REPLACE FUNCTION security_reject_discord_mutation()
        RETURNS trigger
        LANGUAGE plpgsql
        AS $$
        BEGIN
          IF current_setting('app.allow_enforce', true) IS DISTINCT FROM 'on' THEN
            IF NEW.effective_mode = 'ENFORCE' OR NEW.discord_mutation
               OR NEW.outcome IN (
                 'ACTIVE', 'PARTIAL_QUARANTINE', 'RELEASED', 'RELEASE_PARTIAL', 'RELEASE_FAILED'
               ) THEN
              RAISE EXCEPTION 'Discord containment is locked';
            END IF;
          END IF;
          RETURN NEW;
        END;
        $$
        """
    )


def downgrade() -> None:
    op.execute(
        """
        CREATE OR REPLACE FUNCTION security_reject_operational_enforce()
        RETURNS trigger
        LANGUAGE plpgsql
        AS $$
        BEGIN
          IF NEW.human_mode = 'ENFORCE' OR NEW.bot_mode = 'ENFORCE' THEN
            RAISE EXCEPTION 'ENFORCE is not operational until containment is implemented';
          END IF;
          RETURN NEW;
        END;
        $$
        """
    )
    op.execute(
        """
        CREATE OR REPLACE FUNCTION security_reject_discord_mutation()
        RETURNS trigger
        LANGUAGE plpgsql
        AS $$
        BEGIN
          IF NEW.effective_mode = 'ENFORCE' THEN
            RAISE EXCEPTION 'ENFORCE is not operational until containment is implemented';
          END IF;
          IF NEW.discord_mutation THEN
            RAISE EXCEPTION 'Discord containment mutation is not available';
          END IF;
          IF NEW.outcome IN (
            'ACTIVE', 'PARTIAL_QUARANTINE', 'RELEASED', 'RELEASE_PARTIAL', 'RELEASE_FAILED'
          ) THEN
            RAISE EXCEPTION 'Containment outcomes are not available until quarantine execution exists';
          END IF;
          RETURN NEW;
        END;
        $$
        """
    )
