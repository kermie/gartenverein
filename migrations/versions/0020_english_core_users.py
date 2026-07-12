"""Kernmodul (Benutzer/Einladung/Einstellungen/Historie) auf Englisch umstellen

Revision ID: 0020_english_core_users
Revises: 0019_english_purchase_requests
Create Date: 2026-07-13
"""
from typing import Union
from alembic import op
import sqlalchemy as sa

revision: str = "0020_english_core_users"
down_revision: Union[str, None] = "0019_english_purchase_requests"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # -----------------------------------------------------------------
    # 1. Enum-Typen umbenennen + Werte aktualisieren
    # -----------------------------------------------------------------
    op.execute("ALTER TYPE benutzerrolle RENAME TO userrole_old")
    op.execute("CREATE TYPE userrole AS ENUM ('ADMIN', 'BOARD', 'TREASURER', 'READONLY')")
    op.execute("""
        ALTER TABLE benutzer ALTER COLUMN rolle TYPE userrole USING (
            CASE rolle::text
                WHEN 'ADMIN' THEN 'ADMIN'
                WHEN 'VORSTAND' THEN 'BOARD'
                WHEN 'KASSIERER' THEN 'TREASURER'
                WHEN 'LESEND' THEN 'READONLY'
                ELSE 'READONLY'
            END
        )::userrole
    """)
    op.execute("""
        ALTER TABLE einladungen ALTER COLUMN rolle TYPE userrole USING (
            CASE rolle::text
                WHEN 'ADMIN' THEN 'ADMIN'
                WHEN 'VORSTAND' THEN 'BOARD'
                WHEN 'KASSIERER' THEN 'TREASURER'
                WHEN 'LESEND' THEN 'READONLY'
                ELSE 'READONLY'
            END
        )::userrole
    """)
    op.execute("DROP TYPE userrole_old")

    op.execute("ALTER TYPE einladungstatus RENAME TO invitationstatus_old")
    op.execute("CREATE TYPE invitationstatus AS ENUM ('PENDING', 'ACCEPTED', 'EXPIRED')")
    op.execute("""
        ALTER TABLE einladungen ALTER COLUMN status TYPE invitationstatus USING (
            CASE status::text
                WHEN 'AUSSTEHEND' THEN 'PENDING'
                WHEN 'ANGENOMMEN' THEN 'ACCEPTED'
                WHEN 'ABGELAUFEN' THEN 'EXPIRED'
                ELSE 'PENDING'
            END
        )::invitationstatus
    """)
    op.execute("DROP TYPE invitationstatus_old")

    # -----------------------------------------------------------------
    # 2. Spalten umbenennen (VOR dem Tabellen-Rename, damit FK-Ziele
    #    beim Umbenennen von "benutzer" -> "users" bereits konsistent sind)
    # -----------------------------------------------------------------
    op.alter_column("benutzer", "passwort_hash", new_column_name="password_hash")
    op.alter_column("benutzer", "rolle", new_column_name="role")
    op.alter_column("benutzer", "ist_aktiv", new_column_name="is_active")
    op.alter_column("benutzer", "letzter_login", new_column_name="last_login")

    op.alter_column("einladungen", "rolle", new_column_name="role")
    op.alter_column("einladungen", "eingeladen_von_id", new_column_name="invited_by_id")
    op.alter_column("einladungen", "gueltig_bis", new_column_name="expires_at")

    op.alter_column("vereinseinstellungen", "schluessel", new_column_name="key")
    op.alter_column("vereinseinstellungen", "wert", new_column_name="value")
    op.alter_column("vereinseinstellungen", "beschreibung", new_column_name="description")

    op.alter_column("aenderungshistorie", "entitaet_typ", new_column_name="entity_type")
    op.alter_column("aenderungshistorie", "entitaet_id", new_column_name="entity_id")
    op.alter_column("aenderungshistorie", "feldname", new_column_name="field_name")
    op.alter_column("aenderungshistorie", "alter_wert", new_column_name="old_value")
    op.alter_column("aenderungshistorie", "neuer_wert", new_column_name="new_value")
    op.alter_column("aenderungshistorie", "geaendert_von_id", new_column_name="changed_by_id")
    op.alter_column("aenderungshistorie", "geaendert_am", new_column_name="changed_at")

    # -----------------------------------------------------------------
    # 3. Tabellen umbenennen (FK-Constraints folgen dem Tabellennamen
    #    automatisch, siehe vorige Modul-Migrationen 0016-0019)
    # -----------------------------------------------------------------
    op.rename_table("benutzer", "users")
    op.rename_table("einladungen", "invitations")
    op.rename_table("vereinseinstellungen", "club_settings")
    op.rename_table("aenderungshistorie", "change_history")

    # -----------------------------------------------------------------
    # 4. Indizes umbenennen
    # -----------------------------------------------------------------
    op.execute("ALTER INDEX IF EXISTS ix_benutzer_email RENAME TO ix_users_email")
    op.execute("ALTER INDEX IF EXISTS ix_einladungen_email RENAME TO ix_invitations_email")
    op.execute("ALTER INDEX IF EXISTS ix_aenderungshistorie_entitaet_typ RENAME TO ix_change_history_entity_type")
    op.execute("ALTER INDEX IF EXISTS ix_aenderungshistorie_entitaet_id RENAME TO ix_change_history_entity_id")
    op.execute("ALTER INDEX IF EXISTS ix_aenderungshistorie_geaendert_am RENAME TO ix_change_history_changed_at")


def downgrade() -> None:
    op.execute("ALTER INDEX IF EXISTS ix_change_history_changed_at RENAME TO ix_aenderungshistorie_geaendert_am")
    op.execute("ALTER INDEX IF EXISTS ix_change_history_entity_id RENAME TO ix_aenderungshistorie_entitaet_id")
    op.execute("ALTER INDEX IF EXISTS ix_change_history_entity_type RENAME TO ix_aenderungshistorie_entitaet_typ")
    op.execute("ALTER INDEX IF EXISTS ix_invitations_email RENAME TO ix_einladungen_email")
    op.execute("ALTER INDEX IF EXISTS ix_users_email RENAME TO ix_benutzer_email")

    op.rename_table("change_history", "aenderungshistorie")
    op.rename_table("club_settings", "vereinseinstellungen")
    op.rename_table("invitations", "einladungen")
    op.rename_table("users", "benutzer")

    op.alter_column("aenderungshistorie", "changed_at", new_column_name="geaendert_am")
    op.alter_column("aenderungshistorie", "changed_by_id", new_column_name="geaendert_von_id")
    op.alter_column("aenderungshistorie", "new_value", new_column_name="neuer_wert")
    op.alter_column("aenderungshistorie", "old_value", new_column_name="alter_wert")
    op.alter_column("aenderungshistorie", "field_name", new_column_name="feldname")
    op.alter_column("aenderungshistorie", "entity_id", new_column_name="entitaet_id")
    op.alter_column("aenderungshistorie", "entity_type", new_column_name="entitaet_typ")

    op.alter_column("vereinseinstellungen", "description", new_column_name="beschreibung")
    op.alter_column("vereinseinstellungen", "value", new_column_name="wert")
    op.alter_column("vereinseinstellungen", "key", new_column_name="schluessel")

    op.alter_column("einladungen", "expires_at", new_column_name="gueltig_bis")
    op.alter_column("einladungen", "invited_by_id", new_column_name="eingeladen_von_id")
    op.alter_column("einladungen", "role", new_column_name="rolle")

    op.alter_column("benutzer", "last_login", new_column_name="letzter_login")
    op.alter_column("benutzer", "is_active", new_column_name="ist_aktiv")
    op.alter_column("benutzer", "role", new_column_name="rolle")
    op.alter_column("benutzer", "password_hash", new_column_name="passwort_hash")

    op.execute("ALTER TYPE invitationstatus RENAME TO invitationstatus_old")
    op.execute("CREATE TYPE einladungstatus AS ENUM ('AUSSTEHEND', 'ANGENOMMEN', 'ABGELAUFEN')")
    op.execute("""
        ALTER TABLE einladungen ALTER COLUMN status TYPE einladungstatus USING (
            CASE status::text
                WHEN 'PENDING' THEN 'AUSSTEHEND'
                WHEN 'ACCEPTED' THEN 'ANGENOMMEN'
                WHEN 'EXPIRED' THEN 'ABGELAUFEN'
                ELSE 'AUSSTEHEND'
            END
        )::einladungstatus
    """)
    op.execute("DROP TYPE invitationstatus_old")

    op.execute("ALTER TYPE userrole RENAME TO userrole_old")
    op.execute("CREATE TYPE benutzerrolle AS ENUM ('ADMIN', 'VORSTAND', 'KASSIERER', 'LESEND')")
    op.execute("""
        ALTER TABLE benutzer ALTER COLUMN rolle TYPE benutzerrolle USING (
            CASE rolle::text
                WHEN 'ADMIN' THEN 'ADMIN'
                WHEN 'BOARD' THEN 'VORSTAND'
                WHEN 'TREASURER' THEN 'KASSIERER'
                WHEN 'READONLY' THEN 'LESEND'
                ELSE 'LESEND'
            END
        )::benutzerrolle
    """)
    op.execute("""
        ALTER TABLE einladungen ALTER COLUMN rolle TYPE benutzerrolle USING (
            CASE rolle::text
                WHEN 'ADMIN' THEN 'ADMIN'
                WHEN 'BOARD' THEN 'VORSTAND'
                WHEN 'TREASURER' THEN 'KASSIERER'
                WHEN 'READONLY' THEN 'LESEND'
                ELSE 'LESEND'
            END
        )::benutzerrolle
    """)
    op.execute("DROP TYPE userrole_old")
