"""Tickets: spam_begruendung Feld fuer Transparenz (Etappe 3)

Revision ID: 0012_spam_begruendung
Revises: 0011_ticket_threading
Create Date: 2026-07-11
"""
from typing import Union
from alembic import op
import sqlalchemy as sa

revision: str = "0012_spam_begruendung"
down_revision: Union[str, None] = "0011_ticket_threading"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("tickets", sa.Column("spam_begruendung", sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column("tickets", "spam_begruendung")
