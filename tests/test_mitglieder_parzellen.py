"""Tests für Mitglieder, Parzellen und ihre m:n-Zuordnung."""
from tests.conftest import login, auth_header


async def test_mitglied_anlegen_und_abrufen(client, admin_benutzer):
    token = await login(client, "admin@example.com")

    response = await client.post(
        "/api/v1/mitglieder",
        json={"vorname": "Erika", "nachname": "Musterfrau"},
        headers=auth_header(token),
    )
    assert response.status_code == 201
    mitglied = response.json()
    assert mitglied["vorname"] == "Erika"

    response = await client.get(f"/api/v1/mitglieder/{mitglied['id']}", headers=auth_header(token))
    assert response.status_code == 200
    assert response.json()["nachname"] == "Musterfrau"


async def test_parzelle_anlegen_doppelte_gartennummer_abgelehnt(client, admin_benutzer):
    token = await login(client, "admin@example.com")

    response = await client.post(
        "/api/v1/parzellen", json={"gartennummer": "G001"}, headers=auth_header(token)
    )
    assert response.status_code == 201

    response = await client.post(
        "/api/v1/parzellen", json={"gartennummer": "g001"}, headers=auth_header(token)
    )
    assert response.status_code == 409  # Groß-/Kleinschreibung wird normalisiert (G001 == g001)


async def test_mitglied_parzelle_zuordnung_und_doppelgarten(client, admin_benutzer):
    token = await login(client, "admin@example.com")
    headers = auth_header(token)

    m1 = (await client.post("/api/v1/mitglieder", json={"vorname": "Anna", "nachname": "Eins"}, headers=headers)).json()
    m2 = (await client.post("/api/v1/mitglieder", json={"vorname": "Bruno", "nachname": "Zwei"}, headers=headers)).json()
    p1 = (await client.post("/api/v1/parzellen", json={"gartennummer": "G010"}, headers=headers)).json()
    p2 = (await client.post("/api/v1/parzellen", json={"gartennummer": "G011"}, headers=headers)).json()

    # Doppelgarten: ein Mitglied bekommt zwei Parzellen
    r1 = await client.post(
        f"/api/v1/parzellen/{p1['id']}/zuordnungen",
        json={"mitglied_id": m1["id"], "parzelle_id": p1["id"], "ist_hauptpaechter": True},
        headers=headers,
    )
    assert r1.status_code == 201

    r2 = await client.post(
        f"/api/v1/parzellen/{p2['id']}/zuordnungen",
        json={"mitglied_id": m1["id"], "parzelle_id": p2["id"], "ist_hauptpaechter": True},
        headers=headers,
    )
    assert r2.status_code == 201

    # Gemeinschaftsgarten: zweites Mitglied auf derselben Parzelle
    r3 = await client.post(
        f"/api/v1/parzellen/{p1['id']}/zuordnungen",
        json={"mitglied_id": m2["id"], "parzelle_id": p1["id"], "ist_hauptpaechter": False},
        headers=headers,
    )
    assert r3.status_code == 201

    detail = (await client.get(f"/api/v1/parzellen/{p1['id']}", headers=headers)).json()
    assert len(detail["mitglieder"]) == 2
