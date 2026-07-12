"""
API-Router: Authentifizierung (JWT-Token-Ausgabe).
"""
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.api_auth import authenticate_user, create_access_token, ACCESS_TOKEN_VALID_MINUTES, get_current_api_user
from app.schemas import TokenResponse, LoginRequest, UserOut
from app.models import User

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
    user = await authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="E-Mail oder Passwort falsch, oder Konto deaktiviert.",
        )
    token = create_access_token(user.id, user.email)
    return TokenResponse(access_token=token, expires_in_minutes=ACCESS_TOKEN_VALID_MINUTES)


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
    user = await authenticate_user(db, daten.email, daten.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="E-Mail oder Passwort falsch, oder Konto deaktiviert.",
        )
    token = create_access_token(user.id, user.email)
    return TokenResponse(access_token=token, expires_in_minutes=ACCESS_TOKEN_VALID_MINUTES)


@router.get(
    "/me",
    response_model=UserOut,
    summary="Eigenes Benutzerprofil abrufen",
)
async def eigenes_profil(user: User = Depends(get_current_api_user)):
    return user
