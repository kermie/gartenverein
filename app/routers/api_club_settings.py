"""
API-Router: Vereinseinstellungen (Stammdaten des Vereins, Flächenangaben etc.).
"""
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db
from app.models import ClubSetting, User
from app.api_auth import get_current_api_user, require_admin_api
from app.schemas import ClubSettingOut, ClubSettingUpdate

router = APIRouter(prefix="/api/v1/club-settings", tags=["API: Vereinseinstellungen"])


@router.get(
    "",
    response_model=List[ClubSettingOut],
    summary="Alle Vereinseinstellungen abrufen",
    description="Liefert Vereinsstammdaten wie Name, Adresse, A-/B-/C-Flächengrößen als Key-Value-Liste.",
)
async def settings_list(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_api_user),
):
    result = await db.execute(select(ClubSetting))
    return result.scalars().all()


@router.get(
    "/{key}",
    response_model=ClubSettingOut,
    summary="Einzelne Einstellung abrufen",
)
async def setting_get(
    key: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_api_user),
):
    result = await db.execute(
        select(ClubSetting).where(ClubSetting.key == key)
    )
    entry = result.scalar_one_or_none()
    if not entry:
        raise HTTPException(status_code=404, detail="Einstellung nicht gefunden")
    return entry


@router.put(
    "/{key}",
    response_model=ClubSettingOut,
    summary="Einstellung setzen oder aktualisieren",
    description="Legt den Schlüssel an, falls er nicht existiert (Upsert). Nur für Admin/Vorstand.",
)
async def setting_set(
    key: str,
    daten: ClubSettingUpdate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_admin_api),
):
    result = await db.execute(
        select(ClubSetting).where(ClubSetting.key == key)
    )
    entry = result.scalar_one_or_none()

    if entry:
        entry.value = daten.value
    else:
        entry = ClubSetting(key=key, value=daten.value)
        db.add(entry)

    await db.commit()
    await db.refresh(entry)
    return entry
