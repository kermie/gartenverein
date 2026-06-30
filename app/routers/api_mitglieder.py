"""
API-Router: Mitglieder – vollständiges CRUD über REST.
"""
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_, func
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.models import Mitglied, MitgliedTelefon, MitgliedEmail, MitgliedParzelle
from app.api_auth import get_current_api_user, require_schreibzugriff
from app.schemas import (
    MitgliedOut, MitgliedDetailOut, MitgliedCreate, MitgliedUpdate,
    TelefonOut, TelefonCreate, EmailAdresseOut, EmailAdresseCreate,
    PaginierteAntwort,
)
from app.models import Benutzer

router = APIRouter(prefix="/api/v1/mitglieder", tags=["API: Mitglieder"])


async def _hole_mitglied_oder_404(db: AsyncSession, mitglied_id: str, mit_details: bool = False) -> Mitglied:
    query = select(Mitglied).where(Mitglied.id == mitglied_id, Mitglied.deleted_at.is_(None))
    if mit_details:
        query = query.options(
            selectinload(Mitglied.telefonnummern),
            selectinload(Mitglied.email_adressen),
            selectinload(Mitglied.parzellen_zuordnungen).selectinload(MitgliedParzelle.parzelle),
        )
    else:
        query = query.options(
            selectinload(Mitglied.telefonnummern),
            selectinload(Mitglied.email_adressen),
        )
    result = await db.execute(query)
    mitglied = result.scalar_one_or_none()
    if not mitglied:
        raise HTTPException(status_code=404, detail="Mitglied nicht gefunden")
    return mitglied


def _zu_detail_schema(mitglied: Mitglied) -> MitgliedDetailOut:
    out = MitgliedDetailOut.model_validate(mitglied)
    out.parzellen = [
        {
            "parzelle_id": z.parzelle.id,
            "gartennummer": z.parzelle.gartennummer,
            "ist_hauptpaechter": z.ist_hauptpaechter,
        }
        for z in mitglied.parzellen_zuordnungen
    ]
    return out


@router.get(
    "",
    response_model=List[MitgliedOut],
    summary="Mitglieder auflisten",
    description="Gibt alle (nicht gelöschten) Mitglieder zurück. Unterstützt Volltextsuche und Paginierung.",
)
async def mitglieder_auflisten(
    suche: Optional[str] = Query(None, description="Suche in Vor-/Nachname und Ort"),
    nur_aktive: bool = Query(False, description="Nur aktive Mitgliedschaften (mitglied_bis in der Zukunft oder leer)"),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    benutzer: Benutzer = Depends(get_current_api_user),
):
    query = (
        select(Mitglied)
        .options(selectinload(Mitglied.telefonnummern), selectinload(Mitglied.email_adressen))
        .where(Mitglied.deleted_at.is_(None))
        .order_by(Mitglied.nachname, Mitglied.vorname)
        .limit(limit)
        .offset(offset)
    )
    if suche:
        query = query.where(
            or_(
                Mitglied.vorname.ilike(f"%{suche}%"),
                Mitglied.nachname.ilike(f"%{suche}%"),
                Mitglied.ort.ilike(f"%{suche}%"),
            )
        )

    result = await db.execute(query)
    mitglieder = result.scalars().all()

    if nur_aktive:
        mitglieder = [m for m in mitglieder if m.ist_aktiv]

    return mitglieder


@router.get(
    "/{mitglied_id}",
    response_model=MitgliedDetailOut,
    summary="Einzelnes Mitglied abrufen",
    description="Gibt ein Mitglied inkl. zugeordneter Parzellen, Telefonnummern und E-Mail-Adressen zurück.",
)
async def mitglied_abrufen(
    mitglied_id: str,
    db: AsyncSession = Depends(get_db),
    benutzer: Benutzer = Depends(get_current_api_user),
):
    mitglied = await _hole_mitglied_oder_404(db, mitglied_id, mit_details=True)
    return _zu_detail_schema(mitglied)


@router.post(
    "",
    response_model=MitgliedOut,
    status_code=status.HTTP_201_CREATED,
    summary="Neues Mitglied anlegen",
)
async def mitglied_erstellen(
    daten: MitgliedCreate,
    db: AsyncSession = Depends(get_db),
    benutzer: Benutzer = Depends(require_schreibzugriff),
):
    mitglied = Mitglied(**daten.model_dump())
    db.add(mitglied)
    await db.commit()
    await db.refresh(mitglied, attribute_names=["telefonnummern", "email_adressen"])
    return mitglied


@router.put(
    "/{mitglied_id}",
    response_model=MitgliedOut,
    summary="Mitglied aktualisieren",
    description="Teilupdate: nur übergebene Felder werden geändert.",
)
async def mitglied_aktualisieren(
    mitglied_id: str,
    daten: MitgliedUpdate,
    db: AsyncSession = Depends(get_db),
    benutzer: Benutzer = Depends(require_schreibzugriff),
):
    mitglied = await _hole_mitglied_oder_404(db, mitglied_id)

    for feld, wert in daten.model_dump(exclude_unset=True).items():
        setattr(mitglied, feld, wert)

    await db.commit()
    await db.refresh(mitglied, attribute_names=["telefonnummern", "email_adressen"])
    return mitglied


@router.delete(
    "/{mitglied_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Mitglied löschen (Soft-Delete)",
    description="Markiert das Mitglied als gelöscht (deleted_at gesetzt). Daten bleiben in der Datenbank erhalten.",
)
async def mitglied_loeschen(
    mitglied_id: str,
    db: AsyncSession = Depends(get_db),
    benutzer: Benutzer = Depends(require_schreibzugriff),
):
    from datetime import datetime, timezone

    mitglied = await _hole_mitglied_oder_404(db, mitglied_id)
    mitglied.deleted_at = datetime.now(timezone.utc)
    await db.commit()


# ---------------------------------------------------------------------------
# Telefonnummern (Unterressource)
# ---------------------------------------------------------------------------

@router.post(
    "/{mitglied_id}/telefonnummern",
    response_model=TelefonOut,
    status_code=status.HTTP_201_CREATED,
    summary="Telefonnummer hinzufügen",
)
async def telefon_hinzufuegen(
    mitglied_id: str,
    daten: TelefonCreate,
    db: AsyncSession = Depends(get_db),
    benutzer: Benutzer = Depends(require_schreibzugriff),
):
    await _hole_mitglied_oder_404(db, mitglied_id)
    telefon = MitgliedTelefon(mitglied_id=mitglied_id, **daten.model_dump())
    db.add(telefon)
    await db.commit()
    await db.refresh(telefon)
    return telefon


@router.delete(
    "/{mitglied_id}/telefonnummern/{telefon_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Telefonnummer entfernen",
)
async def telefon_entfernen(
    mitglied_id: str,
    telefon_id: str,
    db: AsyncSession = Depends(get_db),
    benutzer: Benutzer = Depends(require_schreibzugriff),
):
    result = await db.execute(
        select(MitgliedTelefon).where(
            MitgliedTelefon.id == telefon_id, MitgliedTelefon.mitglied_id == mitglied_id
        )
    )
    telefon = result.scalar_one_or_none()
    if not telefon:
        raise HTTPException(status_code=404, detail="Telefonnummer nicht gefunden")
    await db.delete(telefon)
    await db.commit()


# ---------------------------------------------------------------------------
# E-Mail-Adressen (Unterressource)
# ---------------------------------------------------------------------------

@router.post(
    "/{mitglied_id}/email-adressen",
    response_model=EmailAdresseOut,
    status_code=status.HTTP_201_CREATED,
    summary="E-Mail-Adresse hinzufügen",
)
async def email_hinzufuegen(
    mitglied_id: str,
    daten: EmailAdresseCreate,
    db: AsyncSession = Depends(get_db),
    benutzer: Benutzer = Depends(require_schreibzugriff),
):
    await _hole_mitglied_oder_404(db, mitglied_id)
    email_obj = MitgliedEmail(
        mitglied_id=mitglied_id,
        adresse=str(daten.adresse).lower(),
        bezeichnung=daten.bezeichnung,
        ist_primaer=daten.ist_primaer,
    )
    db.add(email_obj)
    await db.commit()
    await db.refresh(email_obj)
    return email_obj


@router.delete(
    "/{mitglied_id}/email-adressen/{email_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="E-Mail-Adresse entfernen",
)
async def email_entfernen(
    mitglied_id: str,
    email_id: str,
    db: AsyncSession = Depends(get_db),
    benutzer: Benutzer = Depends(require_schreibzugriff),
):
    result = await db.execute(
        select(MitgliedEmail).where(
            MitgliedEmail.id == email_id, MitgliedEmail.mitglied_id == mitglied_id
        )
    )
    email_obj = result.scalar_one_or_none()
    if not email_obj:
        raise HTTPException(status_code=404, detail="E-Mail-Adresse nicht gefunden")
    await db.delete(email_obj)
    await db.commit()
