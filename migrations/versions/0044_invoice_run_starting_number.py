"""Add invoice_runs.starting_sequence_override

Revision ID: 0044_invoice_run_starting_number
Revises: 0043_finance_categories
Create Date: 2026-07-24

Issue #73: the global "invoice_number_start" ClubSetting (see #65) is
only ever consulted for a year that has zero invoices -- it silently
stops mattering the moment any invoice exists for that year, with no
way to force a deliberate jump afterward. This adds a per-run,
always-available override: set on a DRAFT run at creation, checked
first in app/invoice_generation.py's finalize_run(), independent of
whatever numbering happened in any other run/year.
"""
from typing import Union

from alembic import op
import sqlalchemy as sa

revision: str = "0044_invoice_run_starting_number"
down_revision: Union[str, None] = "0043_finance_categories"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("invoice_runs", sa.Column("starting_sequence_override", sa.Integer(), nullable=True))


def downgrade() -> None:
    op.drop_column("invoice_runs", "starting_sequence_override")
