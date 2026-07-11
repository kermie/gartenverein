"""Tests für Login/Authentifizierung."""
from tests.conftest import login, auth_header


async def test_login_erfolgreich(client, admin_benutzer):
    token = await login(client, "admin@test.local")
    assert token

    response = await client.get("/api/v1/auth/me", headers=auth_header(token))
    assert response.status_code == 200
    assert response.json()["email"] == "admin@test.local"


async def test_login_falsches_passwort(client, admin_benutzer):
    response = await client.post(
        "/api/v1/auth/login",
        json={"email": "admin@test.local", "passwort": "falsches-passwort"},
    )
    assert response.status_code == 401


async def test_login_unbekannte_email(client):
    response = await client.post(
        "/api/v1/auth/login",
        json={"email": "niemand@test.local", "passwort": "irgendwas"},
    )
    assert response.status_code == 401


async def test_geschuetzter_endpunkt_ohne_token(client):
    response = await client.get("/api/v1/mitglieder")
    assert response.status_code == 401
