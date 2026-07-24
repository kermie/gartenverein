"""Add finance_categories and invoice_item_definitions.category_id

Revision ID: 0043_finance_categories
Revises: 0042_widen_invoice_number
Create Date: 2026-07-24

Issue #67: bookkeeping categories (5-character code + title, grouped
into income/expense/fixed assets/equity & liabilities/other), loosely
inspired by German chart-of-accounts conventions (SKR42) without
shipping any of SKR42's actual copyrighted codes -- a club imports its
own via CSV or types them in. Optional link from InvoiceItemDefinition
to a category for the club's own bookkeeping/reporting; doesn't affect
invoice generation.
"""
from typing import Union

from alembic import op
import sqlalchemy as sa

revision: str = "0043_finance_categories"
down_revision: Union[str, None] = "0042_widen_invoice_number"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "finance_categories",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("code", sa.String(5), nullable=False, unique=True),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column(
            "group",
            sa.Enum("INCOME", "EXPENSE", "FIXED_ASSETS", "EQUITY_LIABILITIES", "OTHER", name="financecategorygroup"),
            nullable=False,
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_finance_categories_code", "finance_categories", ["code"], unique=True)

    op.add_column(
        "invoice_item_definitions",
        sa.Column("category_id", sa.String(36), sa.ForeignKey("finance_categories.id", ondelete="SET NULL"), nullable=True),
    )
    op.create_index(
        "ix_invoice_item_definitions_category_id", "invoice_item_definitions", ["category_id"],
    )


def downgrade() -> None:
    op.drop_index("ix_invoice_item_definitions_category_id", table_name="invoice_item_definitions")
    op.drop_column("invoice_item_definitions", "category_id")

    op.drop_index("ix_finance_categories_code", table_name="finance_categories")
    op.drop_table("finance_categories")
    op.execute("DROP TYPE IF EXISTS financecategorygroup")
