"""Add content_html column to ticket_messages

Revision ID: 0024_ticket_message_html
Revises: 0023_ticket_status_redesign
Create Date: 2026-07-16

Stores a sanitized HTML version of an incoming ticket email alongside
the existing plain-text `content` column, so HTML emails can be
rendered properly instead of showing raw tag soup or losing all
formatting. Only ever populated for INCOMING messages whose email had a
text/html part; always None for OUTGOING/INTERNAL messages (those are
always plain text typed by staff). See app/html_sanitizer.py for the
sanitization applied before anything is stored here -- this column must
never be trusted as safe-by-construction elsewhere without re-checking
that assumption, since its ultimate source is an arbitrary external
email sender.

Existing historical messages are unaffected (content_html stays NULL
for anything already in the database) -- there was no way to recover
the original HTML for those after the fact, since only plain text was
ever stored before this migration.
"""
from typing import Union

from alembic import op
import sqlalchemy as sa

revision: str = "0024_ticket_message_html"
down_revision: Union[str, None] = "0023_ticket_status_redesign"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("ticket_messages", sa.Column("content_html", sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column("ticket_messages", "content_html")
