"""Add grants_full_access/grants_system_admin to groups, invitation group targets

Revision ID: 0039_group_access_flags
Revises: 0038_groups_and_permissions
Create Date: 2026-07-23

ADR 0041: a Group can now grant the same effective access a role used
to be the only way to get -- full module access (grants_full_access,
today's BOARD behavior) and/or admin-panel access (grants_system_admin,
today's ADMIN behavior). This is additive: ADMIN/BOARD roles keep
working exactly as before for whoever already has them; new users are
assigned to groups instead of a role going forward.

invitation_group_targets mirrors group_memberships' shape for
Invitation instead of User -- which group(s) a pending invite will
place the new user into once accepted.

Data migration: seeds an "Administrators" group (grants_system_admin)
and a "Board" group (grants_full_access), and adds every existing
ADMIN/BOARD user to the matching one -- same pattern 0038 used for its
"Full Access" seed group -- so an admin opens Groups right after
upgrading and finds exactly the two starting groups this feature was
designed around, already populated with who currently holds that
access.
"""
from typing import Union
import uuid

from alembic import op
import sqlalchemy as sa

revision: str = "0039_group_access_flags"
down_revision: Union[str, None] = "0038_groups_and_permissions"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "groups",
        sa.Column("grants_full_access", sa.Boolean(), nullable=False, server_default="false"),
    )
    op.add_column(
        "groups",
        sa.Column("grants_system_admin", sa.Boolean(), nullable=False, server_default="false"),
    )

    op.create_table(
        "invitation_group_targets",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("invitation_id", sa.String(36), sa.ForeignKey("invitations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("group_id", sa.String(36), sa.ForeignKey("groups.id", ondelete="CASCADE"), nullable=False),
        sa.UniqueConstraint("invitation_id", "group_id", name="uq_invitation_group_target"),
    )
    op.create_index("ix_invitation_group_targets_invitation_id", "invitation_group_targets", ["invitation_id"])
    op.create_index("ix_invitation_group_targets_group_id", "invitation_group_targets", ["group_id"])

    connection = op.get_bind()

    admins_group_id = str(uuid.uuid4())
    connection.execute(
        sa.text(
            "INSERT INTO groups (id, name, description, grants_system_admin) "
            "VALUES (:id, :name, :description, true)"
        ),
        {
            "id": admins_group_id, "name": "Administrators",
            "description": "Created automatically when group-based access was introduced -- "
                            "full access everywhere, including the administration panel.",
        },
    )
    admin_users = connection.execute(sa.text("SELECT id FROM users WHERE role = 'ADMIN'")).fetchall()
    for (user_id,) in admin_users:
        connection.execute(
            sa.text("INSERT INTO group_memberships (id, user_id, group_id) VALUES (:id, :user_id, :group_id)"),
            {"id": str(uuid.uuid4()), "user_id": user_id, "group_id": admins_group_id},
        )

    board_group_id = str(uuid.uuid4())
    connection.execute(
        sa.text(
            "INSERT INTO groups (id, name, description, grants_full_access) "
            "VALUES (:id, :name, :description, true)"
        ),
        {
            "id": board_group_id, "name": "Board",
            "description": "Created automatically when group-based access was introduced -- "
                            "full read/write/delete on every module, but not the administration panel.",
        },
    )
    board_users = connection.execute(sa.text("SELECT id FROM users WHERE role = 'BOARD'")).fetchall()
    for (user_id,) in board_users:
        connection.execute(
            sa.text("INSERT INTO group_memberships (id, user_id, group_id) VALUES (:id, :user_id, :group_id)"),
            {"id": str(uuid.uuid4()), "user_id": user_id, "group_id": board_group_id},
        )


def downgrade() -> None:
    connection = op.get_bind()
    # Memberships cascade-delete with the group row (group_memberships.group_id
    # is ondelete=CASCADE, see 0038) -- best-effort by name, since an admin may
    # have renamed these by the time a downgrade happens.
    connection.execute(sa.text("DELETE FROM groups WHERE name IN ('Administrators', 'Board')"))

    op.drop_index("ix_invitation_group_targets_group_id", table_name="invitation_group_targets")
    op.drop_index("ix_invitation_group_targets_invitation_id", table_name="invitation_group_targets")
    op.drop_table("invitation_group_targets")
    op.drop_column("groups", "grants_system_admin")
    op.drop_column("groups", "grants_full_access")
