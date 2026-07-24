"""Widen invoices.invoice_number for free-form number formats

Revision ID: 0042_widen_invoice_number
Revises: 0041_invoice_sequence_number
Create Date: 2026-07-24

Issue #65 follow-up: the format is now a freely-typed string (any
literal text around {year}/{number}, e.g. "R-{year}-{number}"), not
one of six fixed combinations -- String(20) was sized for the fixed
set and could truncate a longer custom prefix/suffix. String(50) is
generous for the "one club's per-year sequence" range this app
operates at, with plenty of room for literal text either side of the
two placeholders.
"""
from typing import Union

from alembic import op
import sqlalchemy as sa

revision: str = "0042_widen_invoice_number"
down_revision: Union[str, None] = "0041_invoice_sequence_number"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.alter_column("invoices", "invoice_number", type_=sa.String(50), existing_type=sa.String(20))


def downgrade() -> None:
    op.alter_column("invoices", "invoice_number", type_=sa.String(20), existing_type=sa.String(50))
