"""
Pydantic-Schemas für die REST-API.

Trennung von DB-Modellen (app/models.py) und API-Schemas ist bewusst:
so können wir API-Verträge stabil halten, auch wenn sich interne
Modelle ändern, und unterschiedliche Felder für Erstellung/Antwort haben.
"""
from datetime import date, datetime
from typing import Optional, List
from decimal import Decimal

from pydantic import BaseModel, EmailStr, ConfigDict, Field

from app.models import ParzelleStatus, BenutzerRolle


# ---------------------------------------------------------------------------
# Auth
# ---------------------------------------------------------------------------

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in_minuten: int


class LoginRequest(BaseModel):
    email: EmailStr
    passwort: str


class BenutzerOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    email: str
    name: str
    rolle: BenutzerRolle
    ist_aktiv: bool


# ---------------------------------------------------------------------------
# Telefon / E-Mail (Unterobjekte von Mitglied)
# ---------------------------------------------------------------------------

class TelefonBase(BaseModel):
    nummer: str = Field(..., max_length=50)
    bezeichnung: Optional[str] = Field(None, max_length=50)
    ist_primaer: bool = False


class TelefonCreate(TelefonBase):
    pass


class TelefonOut(TelefonBase):
    model_config = ConfigDict(from_attributes=True)
    id: str


class EmailAdresseBase(BaseModel):
    adresse: EmailStr
    bezeichnung: Optional[str] = Field(None, max_length=50)
    ist_primaer: bool = False


class EmailAdresseCreate(EmailAdresseBase):
    pass


class EmailAdresseOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    adresse: str
    bezeichnung: Optional[str] = None
    ist_primaer: bool


# ---------------------------------------------------------------------------
# Mitglied
# ---------------------------------------------------------------------------

class MitgliedBase(BaseModel):
    vorname: str = Field(..., max_length=100)
    nachname: str = Field(..., max_length=100)
    geburtsdatum: Optional[date] = None
    strasse: Optional[str] = Field(None, max_length=255)
    plz: Optional[str] = Field(None, max_length=10)
    ort: Optional[str] = Field(None, max_length=100)
    iban: Optional[str] = Field(None, max_length=34)
    mitglied_seit: Optional[date] = None
    mitglied_bis: Optional[date] = None
    email_benachrichtigungen: bool = True
    notizen: Optional[str] = None


class MitgliedCreate(MitgliedBase):
    pass


class MitgliedUpdate(BaseModel):
    """Alle Felder optional – für PATCH-artige Teilupdates via PUT."""
    vorname: Optional[str] = Field(None, max_length=100)
    nachname: Optional[str] = Field(None, max_length=100)
    geburtsdatum: Optional[date] = None
    strasse: Optional[str] = Field(None, max_length=255)
    plz: Optional[str] = Field(None, max_length=10)
    ort: Optional[str] = Field(None, max_length=100)
    iban: Optional[str] = Field(None, max_length=34)
    mitglied_seit: Optional[date] = None
    mitglied_bis: Optional[date] = None
    email_benachrichtigungen: Optional[bool] = None
    notizen: Optional[str] = None


class ParzelleZuordnungKurz(BaseModel):
    """Kompakte Parzelleninfo innerhalb einer Mitglied-Antwort."""
    model_config = ConfigDict(from_attributes=True)
    parzelle_id: str
    gartennummer: str
    ist_hauptpaechter: bool


class MitgliedOut(MitgliedBase):
    model_config = ConfigDict(from_attributes=True)
    id: str
    created_at: datetime
    updated_at: datetime
    ist_aktiv: bool
    telefonnummern: List[TelefonOut] = []
    email_adressen: List[EmailAdresseOut] = []


class MitgliedDetailOut(MitgliedOut):
    """Erweiterte Ansicht inkl. zugeordneter Parzellen, für GET /mitglieder/{id}."""
    parzellen: List[ParzelleZuordnungKurz] = []


# ---------------------------------------------------------------------------
# Parzelle
# ---------------------------------------------------------------------------

class ParzelleBase(BaseModel):
    gartennummer: str = Field(..., max_length=20)
    flaeche_qm: Optional[Decimal] = None
    notizen: Optional[str] = None


class ParzelleCreate(ParzelleBase):
    pass


class ParzelleUpdate(BaseModel):
    gartennummer: Optional[str] = Field(None, max_length=20)
    flaeche_qm: Optional[Decimal] = None
    status: Optional[ParzelleStatus] = None
    kuendigung_datum: Optional[date] = None
    kuendigung_notiz: Optional[str] = None
    notizen: Optional[str] = None


class MitgliedZuordnungKurz(BaseModel):
    """Kompakte Mitgliedinfo innerhalb einer Parzelle-Antwort."""
    model_config = ConfigDict(from_attributes=True)
    mitglied_id: str
    name: str
    ist_hauptpaechter: bool


class ParzelleOut(ParzelleBase):
    model_config = ConfigDict(from_attributes=True)
    id: str
    status: ParzelleStatus
    kuendigung_datum: Optional[date] = None
    kuendigung_notiz: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class ParzelleDetailOut(ParzelleOut):
    mitglieder: List[MitgliedZuordnungKurz] = []


# ---------------------------------------------------------------------------
# Mitglied-Parzelle-Zuordnung
# ---------------------------------------------------------------------------

class ZuordnungCreate(BaseModel):
    mitglied_id: str
    parzelle_id: str
    ist_hauptpaechter: bool = True
    zuordnung_von: Optional[date] = None
    zuordnung_bis: Optional[date] = None


class ZuordnungOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    mitglied_id: str
    parzelle_id: str
    ist_hauptpaechter: bool
    zuordnung_von: Optional[date] = None
    zuordnung_bis: Optional[date] = None


# ---------------------------------------------------------------------------
# Vereinseinstellung
# ---------------------------------------------------------------------------

class VereinseinstellungOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    schluessel: str
    wert: Optional[str] = None
    beschreibung: Optional[str] = None


class VereinseinstellungUpdate(BaseModel):
    wert: Optional[str] = None


# ---------------------------------------------------------------------------
# Generische Listenantwort (Pagination-ready)
# ---------------------------------------------------------------------------

class PaginierteAntwort(BaseModel):
    gesamt: int
    limit: int
    offset: int
