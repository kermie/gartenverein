"""
Zentrale Test-Konfiguration.

Wichtig: DATABASE_URL wird HIER, ganz am Anfang, VOR jedem App-Import
gesetzt. Python cached Modul-Importe – wenn app.database (und damit die
Engine/Session) schon einmal mit der Produktions-URL importiert wurde,
würde jeder spätere Import dieselbe (falsche) Verbindung wiederverwenden.
Da wir hier zuerst os.environ setzen und ERST DANACH die App importieren,
verwenden auch interne Mechanismen der App selbst (Middleware, Startup-
Logik) automatisch die Testdatenbank – ohne dass wir jede einzelne
Stelle einzeln überschreiben müssten.

Tests laufen bewusst gegen echtes PostgreSQL, nicht SQLite: mehrere
frühere Bugs in diesem Projekt traten NUR mit PostgreSQL auf (z.B.
Groß-/Kleinschreibung bei Enum-Werten) – SQLite hätte diese Bugs
unsichtbar gemacht, statt sie zu fangen.
"""
import os

os.environ.setdefault(
    "DATABASE_URL",
    "postgresql+asyncpg://gartenverein:test@db_test:5432/gartenverein_test",
)
os.environ.setdefault("SECRET_KEY", "test-secret-key-nur-fuer-tests")
os.environ.setdefault("ENVIRONMENT", "development")

import pytest_asyncio
from httpx import AsyncClient, ASGITransport

from app.database import Base, engine, AsyncSessionLocal
from app.main import app
from app.models import Benutzer, BenutzerRolle
from app.auth import hash_passwort


@pytest_asyncio.fixture(scope="session", autouse=True)
async def _tabellen_erstellen():
    """Legt einmal pro Testlauf alle Tabellen frisch an (aus den aktuellen
    Modellen, nicht über Alembic – für Tests reicht der aktuelle Modellstand)."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    yield
    await engine.dispose()


@pytest_asyncio.fixture(autouse=True)
async def _frische_verbindung():
    """
    Verwirft den Connection-Pool VOR jedem einzelnen Test.

    Nötig, weil pytest-asyncio jeder Testfunktion einen eigenen Event-Loop
    gibt, unsere Datenbank-Engine (app.database.engine) aber ein Singleton
    ist. Ohne dies würde die Engine versuchen, eine Verbindung aus einem
    bereits beendeten Loop (vom vorherigen Test) wiederzuverwenden – das
    äußert sich als "attached to a different loop"-Fehler. Durch das
    Verwerfen entstehen neue Verbindungen automatisch im aktuell laufenden
    Loop, sobald sie das nächste Mal gebraucht werden.

    Dieser Ansatz ist absichtlich unabhängig von pytest-asyncios eigener
    Loop-Scope-Konfiguration – die hat sich zwischen Versionen mehrfach
    geändert (siehe docs/testing.md) und war keine verlässliche Basis.
    """
    await engine.dispose()
    yield


@pytest_asyncio.fixture(autouse=True)
async def _tabellen_leeren(_frische_verbindung):
    """
    Leert vor JEDEM einzelnen Test alle Tabellen. Einfacher und robuster
    als verschachtelte Transaktionen/Savepoints – funktioniert zuverlässig
    auch dort, wo die Anwendung selbst mittendrin committet (was bei
    verschachtelten Test-Transaktionen sonst Probleme macht).
    """
    async with AsyncSessionLocal() as session:
        for tabelle in reversed(Base.metadata.sorted_tables):
            await session.execute(tabelle.delete())
        await session.commit()
    yield


@pytest_asyncio.fixture
async def client():
    """HTTP-Client, der direkt gegen die FastAPI-App spricht (kein echter Server nötig)."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as ac:
        yield ac


@pytest_asyncio.fixture
async def admin_benutzer():
    """Legt einen Admin-Benutzer an und gibt ihn zurück."""
    async with AsyncSessionLocal() as session:
        benutzer = Benutzer(
            email="admin@example.com",
            name="Test-Admin",
            passwort_hash=hash_passwort("testpasswort123"),
            rolle=BenutzerRolle.ADMIN,
        )
        session.add(benutzer)
        await session.commit()
        await session.refresh(benutzer)
        return benutzer


@pytest_asyncio.fixture
async def vorstand_benutzer():
    """Ein zweiter Benutzer mit Vorstands-Rolle (für Vier-Augen-Prinzip-Tests)."""
    async with AsyncSessionLocal() as session:
        benutzer = Benutzer(
            email="vorstand@example.com",
            name="Test-Vorstand",
            passwort_hash=hash_passwort("testpasswort123"),
            rolle=BenutzerRolle.VORSTAND,
        )
        session.add(benutzer)
        await session.commit()
        await session.refresh(benutzer)
        return benutzer


@pytest_asyncio.fixture
async def zweiter_vorstand_benutzer():
    """Ein dritter Benutzer mit Vorstands-Rolle (für Tests, die 2 unterschiedliche Freigeber brauchen)."""
    async with AsyncSessionLocal() as session:
        benutzer = Benutzer(
            email="vorstand2@example.com",
            name="Test-Vorstand Zwei",
            passwort_hash=hash_passwort("testpasswort123"),
            rolle=BenutzerRolle.VORSTAND,
        )
        session.add(benutzer)
        await session.commit()
        await session.refresh(benutzer)
        return benutzer


async def login(client: AsyncClient, email: str, passwort: str = "testpasswort123") -> str:
    """Hilfsfunktion: loggt einen Benutzer ein und gibt das JWT-Access-Token zurück."""
    response = await client.post("/api/v1/auth/login", json={"email": email, "passwort": passwort})
    assert response.status_code == 200, response.text
    return response.json()["access_token"]


def auth_header(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}
