"""
Authentifizierung: Passwort-Hashing, Sessions, Einladungstoken.
"""
import secrets
import bcrypt
from datetime import datetime, timedelta, timezone
from typing import Optional

from itsdangerous import URLSafeTimedSerializer, BadSignature, SignatureExpired
from fastapi import Request, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.config import settings
from app.models import Benutzer

serializer = URLSafeTimedSerializer(settings.secret_key)

EINLADUNG_GUELTIG_TAGE = 7


def hash_passwort(passwort: str) -> str:
    return bcrypt.hashpw(passwort.encode(), bcrypt.gensalt()).decode()


def verify_passwort(passwort: str, hashed: str) -> bool:
    return bcrypt.checkpw(passwort.encode(), hashed.encode())


def erstelle_einladungstoken(email: str) -> str:
    return serializer.dumps(email, salt="einladung")


def pruefe_einladungstoken(token: str, max_age: int = EINLADUNG_GUELTIG_TAGE * 86400) -> Optional[str]:
    try:
        email = serializer.loads(token, salt="einladung", max_age=max_age)
        return email
    except (BadSignature, SignatureExpired):
        return None


def erstelle_session_token(benutzer_id: str) -> str:
    return serializer.dumps(benutzer_id, salt="session")


def pruefe_session_token(token: str) -> Optional[str]:
    try:
        benutzer_id = serializer.loads(
            token, salt="session", max_age=settings.session_max_age
        )
        return benutzer_id
    except (BadSignature, SignatureExpired):
        return None


async def get_current_user(request: Request, db: AsyncSession) -> Optional[Benutzer]:
    token = request.cookies.get("session")
    if not token:
        return None
    benutzer_id = pruefe_session_token(token)
    if not benutzer_id:
        return None
    result = await db.execute(select(Benutzer).where(Benutzer.id == benutzer_id))
    benutzer = result.scalar_one_or_none()
    if benutzer and not benutzer.ist_aktiv:
        return None
    return benutzer


async def require_user(request: Request, db: AsyncSession) -> Benutzer:
    benutzer = await get_current_user(request, db)
    if not benutzer:
        raise HTTPException(
            status_code=status.HTTP_303_SEE_OTHER,
            headers={"Location": "/auth/login"}
        )
    return benutzer


async def require_admin(request: Request, db: AsyncSession) -> Benutzer:
    from app.models import BenutzerRolle
    benutzer = await require_user(request, db)
    if benutzer.rolle not in (BenutzerRolle.ADMIN, BenutzerRolle.VORSTAND):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Keine Berechtigung")
    return benutzer
