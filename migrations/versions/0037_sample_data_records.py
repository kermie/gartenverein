"""Add sample_data_records tracking table

Revision ID: 0037_sample_data_records
Revises: 0036_invoice_current_only
Create Date: 2026-07-22

Tracks every row created by the admin "add sample data" feature (see
app/sample_data.py) as (module, entity_type, entity_id), so "remove all
sample data" can delete exactly what was generated.
"""
from typing import Union

from alembic import op
import sqlalchemy as sa

revision: str = "0037_sample_data_records"
down_revision: Union[str, None] = "0036_invoice_current_only"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "sample_data_records",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("module", sa.String(50), nullable=False),
        sa.Column("entity_type", sa.String(100), nullable=False),
        sa.Column("entity_id", sa.String(36), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.UniqueConstraint("entity_type", "entity_id", name="uq_sample_data_record"),
    )
    op.create_index("ix_sample_data_records_module", "sample_data_records", ["module"])
    op.create_index("ix_sample_data_records_entity_type", "sample_data_records", ["entity_type"])


def downgrade() -> None:
    op.drop_index("ix_sample_data_records_entity_type", table_name="sample_data_records")
    op.drop_index("ix_sample_data_records_module", table_name="sample_data_records")
    op.drop_table("sample_data_records")
