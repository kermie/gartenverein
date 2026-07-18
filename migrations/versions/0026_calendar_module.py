"""Add calendar module: calendar_events, council_presence, council_absence

Revision ID: 0026_calendar_module
Revises: 0025_work_tasks
Create Date: 2026-07-18

New calendar module with three new tables:
- calendar_events: manually-created community calendar entries (member
  meetings, parcel inspections). Work sessions are deliberately NOT
  duplicated here -- the community calendar reads WorkSession directly
  at request time and merges it with this table.
- council_presence: scheduled on-site slots for board/council members.
- council_absence: self-reported absence periods for any user account.

No changes to existing tables. Birthdays are not a stored table at all
-- the birthday calendar/ICS feed is generated on the fly from
Member.date_of_birth.
"""
from typing import Union

from alembic import op
import sqlalchemy as sa

revision: str = "0026_calendar_module"
down_revision: Union[str, None] = "0025_work_tasks"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "calendar_events",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "event_type",
            sa.Enum("MEMBER_MEETING", "PARCEL_INSPECTION", "OTHER", name="calendareventtype"),
            nullable=False,
            server_default="OTHER",
        ),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("location", sa.String(255), nullable=True),
        sa.Column("start_date", sa.Date(), nullable=False),
        sa.Column("start_time", sa.String(5), nullable=True),
        sa.Column("end_date", sa.Date(), nullable=True),
        sa.Column("end_time", sa.String(5), nullable=True),
        sa.Column(
            "created_by_id", sa.String(36),
            sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True,
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )
    op.create_index("ix_calendar_events_start_date", "calendar_events", ["start_date"])

    op.create_table(
        "council_presence",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "user_id", sa.String(36),
            sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False,
        ),
        sa.Column("date", sa.Date(), nullable=False),
        sa.Column("time_from", sa.String(5), nullable=True),
        sa.Column("time_until", sa.String(5), nullable=True),
        sa.Column("note", sa.String(255), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )
    op.create_index("ix_council_presence_user_id", "council_presence", ["user_id"])
    op.create_index("ix_council_presence_date", "council_presence", ["date"])

    op.create_table(
        "council_absence",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "user_id", sa.String(36),
            sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False,
        ),
        sa.Column("start_date", sa.Date(), nullable=False),
        sa.Column("end_date", sa.Date(), nullable=False),
        sa.Column("note", sa.String(255), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )
    op.create_index("ix_council_absence_user_id", "council_absence", ["user_id"])
    op.create_index("ix_council_absence_start_date", "council_absence", ["start_date"])


def downgrade() -> None:
    op.drop_index("ix_council_absence_start_date", table_name="council_absence")
    op.drop_index("ix_council_absence_user_id", table_name="council_absence")
    op.drop_table("council_absence")

    op.drop_index("ix_council_presence_date", table_name="council_presence")
    op.drop_index("ix_council_presence_user_id", table_name="council_presence")
    op.drop_table("council_presence")

    op.drop_index("ix_calendar_events_start_date", table_name="calendar_events")
    op.drop_table("calendar_events")
    sa.Enum(name="calendareventtype").drop(op.get_bind(), checkfirst=True)
