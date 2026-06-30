"""
API-Router: Authentifizierung (JWT-Token-Ausgabe).
"""
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.api_auth import authenticate_benutzer, erstelle_access_token, ACCESS_TOKEN_GUELTIG_MINUTEN, get_current_api_user
from app.schemas import TokenResponse, LoginRequest, BenutzerOut
from app.models import Benutzer

router = APIRouter(prefix="/api/v1/auth", tags=["API: Authentifizierung"])


@router.post(
    "/token",
    response_model=TokenResponse,
    summary="Zugriffstoken anfordern",
    description=(
        "Authentifiziert sich mit E-Mail und Passwort und gibt ein JWT-Bearer-Token zurück. "
        "Kompatibel mit OAuth2-Password-Flow (für Swagger-UI „Authorize“-Button) UND "
        "mit JSON-Body (für programmatische Clients, siehe /api/v1/auth/login)."
    ),
)
async def token_anfordern(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db),
):
    benutzer = await authenticate_benutzer(db, form_data.username, form_data.password)
    if not benutzer:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="E-Mail oder Passwort falsch, oder Konto deaktiviert.",
        )
    token = erstelle_access_token(benutzer.id, benutzer.email)
    return TokenResponse(access_token=token, expires_in_minuten=ACCESS_TOKEN_GUELTIG_MINUTEN)


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Zugriffstoken anfordern (JSON)",
    description="Wie /token, aber mit JSON-Body statt Formulardaten – praktischer für die meisten HTTP-Clients.",
)
async def login_json(
    daten: LoginRequest,
    db: AsyncSession = Depends(get_db),
):
    benutzer = await authenticate_benutzer(db, daten.email, daten.passwort)
    if not benutzer:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="E-Mail oder Passwort falsch, oder Konto deaktiviert.",
        )
    token = erstelle_access_token(benutzer.id, benutzer.email)
    return TokenResponse(access_token=token, expires_in_minuten=ACCESS_TOKEN_GUELTIG_MINUTEN)


@router.get(
    "/me",
    response_model=BenutzerOut,
    summary="Eigenes Benutzerprofil abrufen",
)
async def eigenes_profil(benutzer: Benutzer = Depends(get_current_api_user)):
    return benutzer
