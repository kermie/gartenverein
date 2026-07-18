"""Add public_session_signups and public_session_signup_sessions tables
for the public signup API (CMS connectors, e.g. the WordPress plugin
under integrations/wordpress/)

Revision ID: 0027_public_signup_api
Revises: 0026_calendar_module
Create Date: 2026-07-18

New feature: lets an external CMS create work-session signups via a
public HTTP API without a Parcella login, identifying only by parcel
number (no Member match required -- the submitter may be a partner,
tenant, or helping neighbor). See docs/module-public-api.md.
"""
from typing import Union

from alembic import op
import sqlalchemy as sa

revision: str = "0027_public_signup_api"
down_revision: Union[str, None] = "0026_calendar_module"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "public_session_signups",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "parcel_id", sa.String(36),
            sa.ForeignKey("parcels.id", ondelete="CASCADE"), nullable=False,
        ),
        sa.Column("name", sa.String(255), nullable=True),
        sa.Column("phone", sa.String(50), nullable=True),
        sa.Column("email", sa.String(255), nullable=True),
        sa.Column("remarks", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )
    op.create_index("ix_public_session_signups_parcel_id", "public_session_signups", ["parcel_id"])

    op.create_table(
        "public_session_signup_sessions",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "signup_id", sa.String(36),
            sa.ForeignKey("public_session_signups.id", ondelete="CASCADE"), nullable=False,
        ),
        sa.Column(
            "session_id", sa.String(36),
            sa.ForeignKey("work_sessions.id", ondelete="CASCADE"), nullable=False,
        ),
        sa.UniqueConstraint("signup_id", "session_id", name="uq_public_signup_session"),
    )
    op.create_index("ix_public_session_signup_sessions_signup_id", "public_session_signup_sessions", ["signup_id"])
    op.create_index("ix_public_session_signup_sessions_session_id", "public_session_signup_sessions", ["session_id"])


def downgrade() -> None:
    op.drop_index("ix_public_session_signup_sessions_session_id", table_name="public_session_signup_sessions")
    op.drop_index("ix_public_session_signup_sessions_signup_id", table_name="public_session_signup_sessions")
    op.drop_table("public_session_signup_sessions")
    op.drop_index("ix_public_session_signups_parcel_id", table_name="public_session_signups")
    op.drop_table("public_session_signups")
