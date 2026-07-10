"""Versicherungsmodul: Sach- und Unfallversicherung pro Parzelle

Revision ID: 0009_versicherungen
Revises: 0008_zaehlerwesen
Create Date: 2026-07-08
"""
from typing import Union
from alembic import op
import sqlalchemy as sa

revision: str = "0009_versicherungen"
down_revision: Union[str, None] = "0008_zaehlerwesen"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "sachversicherung_pakete",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("jahr", sa.Integer(), nullable=False),
        sa.Column("bezeichnung", sa.String(100), nullable=False),
        sa.Column("betrag_eur", sa.Numeric(8, 2), nullable=False),
        sa.Column("reihenfolge", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_sachversicherung_pakete_jahr", "sachversicherung_pakete", ["jahr"])

    op.create_table(
        "versicherungs_konfiguration",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("jahr", sa.Integer(), nullable=False),
        sa.Column("unfall_grundbetrag_eur", sa.Numeric(8, 2), nullable=False),
        sa.Column("unfall_zusatzbetrag_eur", sa.Numeric(8, 2), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index(
        "ix_versicherungs_konfiguration_jahr", "versicherungs_konfiguration", ["jahr"], unique=True
    )

    op.create_table(
        "parzelle_versicherung",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("parzelle_id", sa.String(36),
                  sa.ForeignKey("parzellen.id", ondelete="CASCADE"), nullable=False),
        sa.Column("jahr", sa.Integer(), nullable=False),
        sa.Column("hat_sachversicherung", sa.Boolean(), nullable=False),
        sa.Column("sach_paket_id", sa.String(36),
                  sa.ForeignKey("sachversicherung_pakete.id", ondelete="SET NULL"), nullable=True),
        sa.Column("hat_unfallversicherung", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("parzelle_id", "jahr", name="uq_parzelle_versicherung_jahr"),
    )
    op.create_index("ix_parzelle_versicherung_parzelle_id", "parzelle_versicherung", ["parzelle_id"])

    op.create_table(
        "unfallversicherung_zusatzpersonen",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("parzelle_versicherung_id", sa.String(36),
                  sa.ForeignKey("parzelle_versicherung.id", ondelete="CASCADE"), nullable=False),
        sa.Column("mitglied_id", sa.String(36),
                  sa.ForeignKey("mitglieder.id", ondelete="CASCADE"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("parzelle_versicherung_id", "mitglied_id", name="uq_versicherung_mitglied"),
    )
    op.create_index(
        "ix_unfallversicherung_zusatzpersonen_pv_id",
        "unfallversicherung_zusatzpersonen", ["parzelle_versicherung_id"]
    )
    op.create_index(
        "ix_unfallversicherung_zusatzpersonen_mitglied_id",
        "unfallversicherung_zusatzpersonen", ["mitglied_id"]
    )


def downgrade() -> None:
    op.drop_table("unfallversicherung_zusatzpersonen")
    op.drop_table("parzelle_versicherung")
    op.drop_table("versicherungs_konfiguration")
    op.drop_table("sachversicherung_pakete")
