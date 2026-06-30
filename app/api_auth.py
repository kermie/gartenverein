"""
JWT-Authentifizierung für die REST-API.

Getrennt von der Cookie-basierten Session-Authentifizierung der Web-UI
(siehe app/auth.py). Die API nutzt klassische Bearer-Token im
Authorization-Header.
"""
from datetime import datetime, timedelta, timezone
from typing import Optional

from jose import jwt, JWTError
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.config import settings
from app.database import get_db
from app.models import Benutzer, BenutzerRolle
from app.auth import verify_passwort

JWT_ALGORITHM = "HS256"
ACCESS_TOKEN_GUELTIG_MINUTEN = 60 * 24  # 24 Stunden

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/token", auto_error=False)


def erstelle_access_token(benutzer_id: str, email: str) -> str:
    ablauf = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_GUELTIG_MINUTEN)
    payload = {
        "sub": benutzer_id,
        "email": email,
        "exp": ablauf,
        "iat": datetime.now(timezone.utc),
        "type": "access",
    }
    return jwt.encode(payload, settings.secret_key, algorithm=JWT_ALGORITHM)


def decode_access_token(token: str) -> Optional[dict]:
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[JWT_ALGORITHM])
        if payload.get("type") != "access":
            return None
        return payload
    except JWTError:
        return None


async def authenticate_benutzer(db: AsyncSession, email: str, passwort: str) -> Optional[Benutzer]:
    result = await db.execute(select(Benutzer).where(Benutzer.email == email.lower()))
    benutzer = result.scalar_one_or_none()
    if not benutzer or not benutzer.passwort_hash:
        return None
    if not verify_passwort(passwort, benutzer.passwort_hash):
        return None
    if not benutzer.ist_aktiv:
        return None
    return benutzer


async def get_current_api_user(
    token: Optional[str] = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
) -> Benutzer:
    """Dependency für geschützte API-Endpunkte. Erfordert gültigen Bearer-Token."""
    unauthorized = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Ungültige oder fehlende Authentifizierung",
        headers={"WWW-Authenticate": "Bearer"},
    )

    if not token:
        raise unauthorized

    payload = decode_access_token(token)
    if not payload:
        raise unauthorized

    benutzer_id = payload.get("sub")
    result = await db.execute(select(Benutzer).where(Benutzer.id == benutzer_id))
    benutzer = result.scalar_one_or_none()

    if not benutzer or not benutzer.ist_aktiv:
        raise unauthorized

    return benutzer


def require_api_rolle(*erlaubte_rollen: BenutzerRolle):
    """Dependency-Factory: schränkt Endpunkte auf bestimmte Rollen ein."""

    async def checker(benutzer: Benutzer = Depends(get_current_api_user)) -> Benutzer:
        if benutzer.rolle not in erlaubte_rollen:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Diese Aktion erfordert eine der Rollen: {', '.join(r.value for r in erlaubte_rollen)}",
            )
        return benutzer

    return checker


# Häufige Kombinationen als fertige Dependencies
require_schreibzugriff = require_api_rolle(
    BenutzerRolle.ADMIN, BenutzerRolle.VORSTAND, BenutzerRolle.KASSIERER
)
require_admin_api = require_api_rolle(BenutzerRolle.ADMIN, BenutzerRolle.VORSTAND)
