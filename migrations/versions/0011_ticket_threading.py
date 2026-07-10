"""Ticket-Nachrichten: Message-ID Felder fuer E-Mail-Threading (Etappe 2)

Revision ID: 0011_ticket_threading
Revises: 0010_tickets
Create Date: 2026-07-10
"""
from typing import Union
from alembic import op
import sqlalchemy as sa

revision: str = "0011_ticket_threading"
down_revision: Union[str, None] = "0010_tickets"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("ticket_nachrichten", sa.Column("message_id", sa.String(255), nullable=True))
    op.add_column("ticket_nachrichten", sa.Column("in_reply_to", sa.String(255), nullable=True))
    op.create_index("ix_ticket_nachrichten_message_id", "ticket_nachrichten", ["message_id"])


def downgrade() -> None:
    op.drop_index("ix_ticket_nachrichten_message_id", table_name="ticket_nachrichten")
    op.drop_column("ticket_nachrichten", "in_reply_to")
    op.drop_column("ticket_nachrichten", "message_id")
