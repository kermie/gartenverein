"""Add inventory module: categories, items, loans

Revision ID: 0032_inventory
Revises: 0031_delivery_external_id
Create Date: 2026-07-21

New module: an asset register for what the club owns (and what
members store on club property), grouped into freely-configurable
categories, plus a lending system for borrowable items.

No changes to existing tables.
"""
from typing import Union

from alembic import op
import sqlalchemy as sa

revision: str = "0032_inventory"
down_revision: Union[str, None] = "0031_delivery_external_id"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "inventory_categories",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("name", sa.String(100), nullable=False, unique=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )

    op.create_table(
        "inventory_items",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "category_id", sa.String(36),
            sa.ForeignKey("inventory_categories.id", ondelete="SET NULL"), nullable=True,
        ),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column(
            "owner_type",
            sa.Enum("CLUB", "MEMBER", name="inventoryownertype"),
            nullable=False, server_default="CLUB",
        ),
        sa.Column(
            "owner_member_id", sa.String(36),
            sa.ForeignKey("members.id", ondelete="SET NULL"), nullable=True,
        ),
        sa.Column("storage_location", sa.String(255), nullable=True),
        sa.Column("purchase_date", sa.Date(), nullable=True),
        sa.Column("purchase_price", sa.Numeric(10, 2), nullable=True),
        sa.Column("current_value", sa.Numeric(10, 2), nullable=True),
        sa.Column("current_value_updated_at", sa.Date(), nullable=True),
        sa.Column("replacement_cost", sa.Numeric(10, 2), nullable=True),
        sa.Column("quantity_total", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("is_borrowable", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("default_loan_fee", sa.Numeric(8, 2), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("retired_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_by_id", sa.String(36),
            sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True,
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), nullable=False,
            server_default=sa.text("now()"),
        ),
    )
    op.create_index("ix_inventory_items_category_id", "inventory_items", ["category_id"])

    op.create_table(
        "item_loans",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "item_id", sa.String(36),
            sa.ForeignKey("inventory_items.id", ondelete="CASCADE"), nullable=False,
        ),
        sa.Column(
            "member_id", sa.String(36),
            sa.ForeignKey("members.id", ondelete="CASCADE"), nullable=False,
        ),
        sa.Column("quantity", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("borrowed_date", sa.Date(), nullable=False),
        sa.Column("returned_date", sa.Date(), nullable=True),
        sa.Column("fee_charged", sa.Numeric(8, 2), nullable=True),
        sa.Column("note", sa.Text(), nullable=True),
        sa.Column(
            "created_by_id", sa.String(36),
            sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True,
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )
    op.create_index("ix_item_loans_item_id", "item_loans", ["item_id"])
    op.create_index("ix_item_loans_member_id", "item_loans", ["member_id"])


def downgrade() -> None:
    op.drop_index("ix_item_loans_member_id", table_name="item_loans")
    op.drop_index("ix_item_loans_item_id", table_name="item_loans")
    op.drop_table("item_loans")
    op.drop_index("ix_inventory_items_category_id", table_name="inventory_items")
    op.drop_table("inventory_items")
    op.drop_table("inventory_categories")
    op.execute("DROP TYPE IF EXISTS inventoryownertype")
