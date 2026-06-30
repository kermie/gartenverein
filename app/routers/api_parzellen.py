"""
API-Router: Parzellen – vollständiges CRUD über REST, inkl. Mitgliederzuordnung.
"""
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db
from app.models import Parzelle, ParzelleStatus, MitgliedParzelle, Mitglied
from app.api_auth import get_current_api_user, require_schreibzugriff
from app.schemas import (
    ParzelleOut, ParzelleDetailOut, ParzelleCreate, ParzelleUpdate,
    ZuordnungCreate, ZuordnungOut,
)
from app.models import Benutzer
from sqlalchemy.orm import selectinload

router = APIRouter(prefix="/api/v1/parzellen", tags=["API: Parzellen"])


async def _hole_parzelle_oder_404(db: AsyncSession, parzelle_id: str, mit_details: bool = False) -> Parzelle:
    query = select(Parzelle).where(Parzelle.id == parzelle_id)
    if mit_details:
        query = query.options(
            selectinload(Parzelle.mitglieder_zuordnungen).selectinload(MitgliedParzelle.mitglied)
        )
    result = await db.execute(query)
    parzelle = result.scalar_one_or_none()
    if not parzelle:
        raise HTTPException(status_code=404, detail="Parzelle nicht gefunden")
    return parzelle


def _zu_detail_schema(parzelle: Parzelle) -> ParzelleDetailOut:
    out = ParzelleDetailOut.model_validate(parzelle)
    out.mitglieder = [
        {
            "mitglied_id": z.mitglied.id,
            "name": z.mitglied.vollname,
            "ist_hauptpaechter": z.ist_hauptpaechter,
        }
        for z in parzelle.mitglieder_zuordnungen
    ]
    return out


@router.get(
    "",
    response_model=List[ParzelleOut],
    summary="Parzellen auflisten",
)
async def parzellen_auflisten(
    suche: Optional[str] = Query(None, description="Suche in Gartennummer"),
    status_filter: Optional[ParzelleStatus] = Query(None, alias="status"),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    benutzer: Benutzer = Depends(get_current_api_user),
):
    query = select(Parzelle).order_by(Parzelle.gartennummer).limit(limit).offset(offset)

    if suche:
        query = query.where(Parzelle.gartennummer.ilike(f"%{suche}%"))
    if status_filter:
        query = query.where(Parzelle.status == status_filter)

    result = await db.execute(query)
    return result.scalars().all()


@router.get(
    "/{parzelle_id}",
    response_model=ParzelleDetailOut,
    summary="Einzelne Parzelle abrufen",
    description="Gibt eine Parzelle inkl. zugeordneter Mitglieder zurück.",
)
async def parzelle_abrufen(
    parzelle_id: str,
    db: AsyncSession = Depends(get_db),
    benutzer: Benutzer = Depends(get_current_api_user),
):
    parzelle = await _hole_parzelle_oder_404(db, parzelle_id, mit_details=True)
    return _zu_detail_schema(parzelle)


@router.post(
    "",
    response_model=ParzelleOut,
    status_code=status.HTTP_201_CREATED,
    summary="Neue Parzelle anlegen",
)
async def parzelle_erstellen(
    daten: ParzelleCreate,
    db: AsyncSession = Depends(get_db),
    benutzer: Benutzer = Depends(require_schreibzugriff),
):
    gartennummer = daten.gartennummer.strip().upper()

    existing = await db.execute(select(Parzelle).where(Parzelle.gartennummer == gartennummer))
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Gartennummer '{gartennummer}' existiert bereits.",
        )

    parzelle = Parzelle(
        gartennummer=gartennummer,
        flaeche_qm=daten.flaeche_qm,
        notizen=daten.notizen,
    )
    db.add(parzelle)
    await db.commit()
    await db.refresh(parzelle)
    return parzelle


@router.put(
    "/{parzelle_id}",
    response_model=ParzelleOut,
    summary="Parzelle aktualisieren",
    description="Teilupdate: nur übergebene Felder werden geändert. Hier auch Statuswechsel (aktiv/gekündigt/gelöscht) und Kündigungsdaten.",
)
async def parzelle_aktualisieren(
    parzelle_id: str,
    daten: ParzelleUpdate,
    db: AsyncSession = Depends(get_db),
    benutzer: Benutzer = Depends(require_schreibzugriff),
):
    parzelle = await _hole_parzelle_oder_404(db, parzelle_id)

    update_daten = daten.model_dump(exclude_unset=True)

    if "gartennummer" in update_daten and update_daten["gartennummer"]:
        neue_nummer = update_daten["gartennummer"].strip().upper()
        if neue_nummer != parzelle.gartennummer:
            existing = await db.execute(
                select(Parzelle).where(Parzelle.gartennummer == neue_nummer, Parzelle.id != parzelle_id)
            )
            if existing.scalar_one_or_none():
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"Gartennummer '{neue_nummer}' existiert bereits.",
                )
        update_daten["gartennummer"] = neue_nummer

    for feld, wert in update_daten.items():
        setattr(parzelle, feld, wert)

    await db.commit()
    await db.refresh(parzelle)
    return parzelle


@router.delete(
    "/{parzelle_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Parzelle als gelöscht markieren",
    description="Setzt den Status auf 'geloescht' (kein echtes DB-Löschen, Historie bleibt erhalten).",
)
async def parzelle_loeschen(
    parzelle_id: str,
    db: AsyncSession = Depends(get_db),
    benutzer: Benutzer = Depends(require_schreibzugriff),
):
    parzelle = await _hole_parzelle_oder_404(db, parzelle_id)
    parzelle.status = ParzelleStatus.GELOESCHT
    await db.commit()


# ---------------------------------------------------------------------------
# Mitglied-Zuordnung (Unterressource)
# ---------------------------------------------------------------------------

@router.post(
    "/{parzelle_id}/zuordnungen",
    response_model=ZuordnungOut,
    status_code=status.HTTP_201_CREATED,
    summary="Mitglied einer Parzelle zuordnen",
    description="Ermöglicht Doppelgärten (mehrere Parzellen pro Mitglied) und Gemeinschaftsgärten (mehrere Mitglieder pro Parzelle).",
)
async def mitglied_zuordnen(
    parzelle_id: str,
    daten: ZuordnungCreate,
    db: AsyncSession = Depends(get_db),
    benutzer: Benutzer = Depends(require_schreibzugriff),
):
    if daten.parzelle_id != parzelle_id:
        raise HTTPException(status_code=400, detail="parzelle_id im Body muss mit URL übereinstimmen")

    await _hole_parzelle_oder_404(db, parzelle_id)

    mitglied_result = await db.execute(
        select(Mitglied).where(Mitglied.id == daten.mitglied_id, Mitglied.deleted_at.is_(None))
    )
    if not mitglied_result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Mitglied nicht gefunden")

    existing = await db.execute(
        select(MitgliedParzelle).where(
            MitgliedParzelle.parzelle_id == parzelle_id,
            MitgliedParzelle.mitglied_id == daten.mitglied_id,
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Zuordnung existiert bereits")

    zuordnung = MitgliedParzelle(
        parzelle_id=parzelle_id,
        mitglied_id=daten.mitglied_id,
        ist_hauptpaechter=daten.ist_hauptpaechter,
        zuordnung_von=daten.zuordnung_von,
        zuordnung_bis=daten.zuordnung_bis,
    )
    db.add(zuordnung)
    await db.commit()
    await db.refresh(zuordnung)
    return zuordnung


@router.delete(
    "/{parzelle_id}/zuordnungen/{zuordnung_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Mitgliederzuordnung entfernen",
)
async def zuordnung_entfernen(
    parzelle_id: str,
    zuordnung_id: str,
    db: AsyncSession = Depends(get_db),
    benutzer: Benutzer = Depends(require_schreibzugriff),
):
    result = await db.execute(
        select(MitgliedParzelle).where(
            MitgliedParzelle.id == zuordnung_id, MitgliedParzelle.parzelle_id == parzelle_id
        )
    )
    zuordnung = result.scalar_one_or_none()
    if not zuordnung:
        raise HTTPException(status_code=404, detail="Zuordnung nicht gefunden")
    await db.delete(zuordnung)
    await db.commit()
