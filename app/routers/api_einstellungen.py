"""
API-Router: Vereinseinstellungen (Stammdaten des Vereins, Flächenangaben etc.).
"""
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db
from app.models import Vereinseinstellung, Benutzer
from app.api_auth import get_current_api_user, require_admin_api
from app.schemas import VereinseinstellungOut, VereinseinstellungUpdate

router = APIRouter(prefix="/api/v1/einstellungen", tags=["API: Vereinseinstellungen"])


@router.get(
    "",
    response_model=List[VereinseinstellungOut],
    summary="Alle Vereinseinstellungen abrufen",
    description="Liefert Vereinsstammdaten wie Name, Adresse, A-/B-/C-Flächengrößen als Key-Value-Liste.",
)
async def einstellungen_auflisten(
    db: AsyncSession = Depends(get_db),
    benutzer: Benutzer = Depends(get_current_api_user),
):
    result = await db.execute(select(Vereinseinstellung))
    return result.scalars().all()


@router.get(
    "/{schluessel}",
    response_model=VereinseinstellungOut,
    summary="Einzelne Einstellung abrufen",
)
async def einstellung_abrufen(
    schluessel: str,
    db: AsyncSession = Depends(get_db),
    benutzer: Benutzer = Depends(get_current_api_user),
):
    result = await db.execute(
        select(Vereinseinstellung).where(Vereinseinstellung.schluessel == schluessel)
    )
    eintrag = result.scalar_one_or_none()
    if not eintrag:
        raise HTTPException(status_code=404, detail="Einstellung nicht gefunden")
    return eintrag


@router.put(
    "/{schluessel}",
    response_model=VereinseinstellungOut,
    summary="Einstellung setzen oder aktualisieren",
    description="Legt den Schlüssel an, falls er nicht existiert (Upsert). Nur für Admin/Vorstand.",
)
async def einstellung_setzen(
    schluessel: str,
    daten: VereinseinstellungUpdate,
    db: AsyncSession = Depends(get_db),
    benutzer: Benutzer = Depends(require_admin_api),
):
    result = await db.execute(
        select(Vereinseinstellung).where(Vereinseinstellung.schluessel == schluessel)
    )
    eintrag = result.scalar_one_or_none()

    if eintrag:
        eintrag.wert = daten.wert
    else:
        eintrag = Vereinseinstellung(schluessel=schluessel, wert=daten.wert)
        db.add(eintrag)

    await db.commit()
    await db.refresh(eintrag)
    return eintrag
