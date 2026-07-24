"""Add invoices.sequence_number, backfilled from existing invoice_number

Revision ID: 0041_invoice_sequence_number
Revises: 0040_annual_invoices
Create Date: 2026-07-24

Issue #65: invoice number FORMAT becomes club-configurable
(ClubSetting "invoice_number_format", e.g. "{year}/{number}",
"{number}-{year}", ...). Numbering (app/invoice_generation.py) needs
the raw sequence number to find "the next one" without parsing it back
out of invoice_number, since a past invoice's format must never change
once assigned (invoice numbers are permanent -- see InvoiceRun's
FINALIZED state). Every invoice created before this migration used the
one hardcoded format "{year}/{sequence}", so the backfill just splits
on "/" -- safe precisely because that was the *only* format that could
have ever been produced up to this point.
"""
from typing import Union

from alembic import op
import sqlalchemy as sa

revision: str = "0041_invoice_sequence_number"
down_revision: Union[str, None] = "0040_annual_invoices"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("invoices", sa.Column("sequence_number", sa.Integer(), nullable=True))

    connection = op.get_bind()
    connection.execute(sa.text(
        "UPDATE invoices SET sequence_number = split_part(invoice_number, '/', 2)::integer"
    ))

    op.alter_column("invoices", "sequence_number", nullable=False)


def downgrade() -> None:
    op.drop_column("invoices", "sequence_number")
