"""
Tests for the public signup API (see app/routers/api_public.py). Focus
on the spots with the highest regression risk: capacity enforcement
across mixed public/member signups, multi-session submissions, the
required API token on the write endpoint, and the module flag gate.
"""
from tests.conftest import login, auth_header


async def _enable_module(client, headers):
    response = await client.put(
        "/api/v1/club-settings/modul_public_signup_api",
        json={"value": "true"},
        headers=headers,
    )
    assert response.status_code == 200, response.text


async def _get_public_api_token(client, headers) -> str:
    # No dedicated read endpoint for the token is exposed via the admin
    # API in this test -- the admin UI generates/shows it. For tests we
    # go through the same club-settings upsert the admin UI itself
    # ultimately relies on, setting a known token directly.
    response = await client.put(
        "/api/v1/club-settings/public_signup_api_token",
        json={"value": "test-public-api-token"},
        headers=headers,
    )
    assert response.status_code == 200, response.text
    return "test-public-api-token"


async def _create_parcel(client, headers, plot_number="G042"):
    response = await client.post(
        "/api/v1/parcels", json={"plot_number": plot_number}, headers=headers
    )
    assert response.status_code == 201, response.text
    return response.json()


async def _create_session(client, headers, title="Standardarbeitseinsatz", max_participants=None, date="2026-08-01"):
    payload = {"title": title, "type": "STANDARD", "date": date}
    if max_participants is not None:
        payload["max_participants"] = max_participants
    response = await client.post("/api/v1/work-hours/sessions", json=payload, headers=headers)
    assert response.status_code == 201, response.text
    return response.json()


async def test_public_endpoints_require_module_flag_enabled(client, admin_user):
    """The module defaults to off -- the public endpoints must 404 until
    a board/admin explicitly turns it on, since this opens a public write
    surface."""
    response = await client.get("/api/v1/public/work-sessions/upcoming")
    assert response.status_code == 404


async def test_upcoming_sessions_and_parcels_are_unauthenticated(client, admin_user):
    token = await login(client, "admin@example.com")
    headers = auth_header(token)
    await _enable_module(client, headers)
    await _create_parcel(client, headers)
    await _create_session(client, headers)

    # No Authorization header at all -- these are public read endpoints.
    sessions_response = await client.get("/api/v1/public/work-sessions/upcoming")
    assert sessions_response.status_code == 200
    assert len(sessions_response.json()) == 1

    parcels_response = await client.get("/api/v1/public/parcels")
    assert parcels_response.status_code == 200
    assert parcels_response.json()[0]["plot_number"] == "G042"


async def test_signup_requires_valid_api_token(client, admin_user):
    token = await login(client, "admin@example.com")
    headers = auth_header(token)
    await _enable_module(client, headers)
    await _get_public_api_token(client, headers)
    await _create_parcel(client, headers)
    session = await _create_session(client, headers)

    # No token at all.
    no_token_response = await client.post(
        "/api/v1/public/work-sessions/signup",
        json={"parcel_number": "G042", "session_ids": [session["id"]]},
    )
    assert no_token_response.status_code == 401

    # Wrong token.
    wrong_token_response = await client.post(
        "/api/v1/public/work-sessions/signup",
        json={"parcel_number": "G042", "session_ids": [session["id"]]},
        headers={"X-Parcella-API-Token": "not-the-real-token"},
    )
    assert wrong_token_response.status_code == 401

    # Correct token succeeds.
    ok_response = await client.post(
        "/api/v1/public/work-sessions/signup",
        json={"parcel_number": "G042", "name": "Gerd Mustergärtner", "session_ids": [session["id"]]},
        headers={"X-Parcella-API-Token": "test-public-api-token"},
    )
    assert ok_response.status_code == 200, ok_response.text
    body = ok_response.json()
    assert body["signup_id"] is not None
    assert body["results"] == [{"session_id": session["id"], "accepted": True, "reason": None}]


async def test_signup_covers_multiple_sessions_in_one_submission(client, admin_user):
    token = await login(client, "admin@example.com")
    headers = auth_header(token)
    await _enable_module(client, headers)
    await _get_public_api_token(client, headers)
    await _create_parcel(client, headers)
    session_a = await _create_session(client, headers, date="2026-08-01")
    session_b = await _create_session(client, headers, date="2026-08-15")

    response = await client.post(
        "/api/v1/public/work-sessions/signup",
        json={"parcel_number": "G042", "session_ids": [session_a["id"], session_b["id"]]},
        headers={"X-Parcella-API-Token": "test-public-api-token"},
    )
    assert response.status_code == 200, response.text
    accepted_ids = {r["session_id"] for r in response.json()["results"] if r["accepted"]}
    assert accepted_ids == {session_a["id"], session_b["id"]}


async def test_signup_respects_capacity_and_counts_toward_available_spots(client, admin_user):
    """Highest-regression-risk case: a session with max_participants=1
    must reject a second public signup, and available_spots (used
    elsewhere in the app) must reflect public signups too, not just
    member SessionParticipations."""
    token = await login(client, "admin@example.com")
    headers = auth_header(token)
    await _enable_module(client, headers)
    await _get_public_api_token(client, headers)
    await _create_parcel(client, headers, plot_number="G042")
    await _create_parcel(client, headers, plot_number="G043")
    session = await _create_session(client, headers, max_participants=1)

    first_response = await client.post(
        "/api/v1/public/work-sessions/signup",
        json={"parcel_number": "G042", "session_ids": [session["id"]]},
        headers={"X-Parcella-API-Token": "test-public-api-token"},
    )
    assert first_response.status_code == 200
    assert first_response.json()["results"][0]["accepted"] is True

    # The session should no longer be listed as available at all now.
    upcoming = (await client.get("/api/v1/public/work-sessions/upcoming")).json()
    assert upcoming == []

    second_response = await client.post(
        "/api/v1/public/work-sessions/signup",
        json={"parcel_number": "G043", "session_ids": [session["id"]]},
        headers={"X-Parcella-API-Token": "test-public-api-token"},
    )
    assert second_response.status_code == 200
    result = second_response.json()["results"][0]
    assert result["accepted"] is False
    assert result["reason"] == "Session is full"


async def test_signup_honeypot_field_silently_ignored(client, admin_user):
    """A filled-in honeypot field must look like a normal success to the
    caller (so a bot doesn't learn it was detected), but must not
    actually create a signup."""
    token = await login(client, "admin@example.com")
    headers = auth_header(token)
    await _enable_module(client, headers)
    await _get_public_api_token(client, headers)
    await _create_parcel(client, headers)
    session = await _create_session(client, headers, max_participants=1)

    response = await client.post(
        "/api/v1/public/work-sessions/signup",
        json={"parcel_number": "G042", "session_ids": [session["id"]], "website": "http://spam.example"},
        headers={"X-Parcella-API-Token": "test-public-api-token"},
    )
    assert response.status_code == 200
    assert response.json()["signup_id"] is None

    # Capacity must be untouched -- a real signup should still succeed.
    real_response = await client.post(
        "/api/v1/public/work-sessions/signup",
        json={"parcel_number": "G042", "session_ids": [session["id"]]},
        headers={"X-Parcella-API-Token": "test-public-api-token"},
    )
    assert real_response.status_code == 200
    assert real_response.json()["results"][0]["accepted"] is True


async def test_signup_accepts_blank_phone_and_email(client, admin_user):
    """Regression test: a real bug found via the WordPress connector --
    HTML forms send untouched optional fields as "" rather than omitting
    them, and EmailStr used to reject "" outright (422), breaking every
    submission that left email blank."""
    token = await login(client, "admin@example.com")
    headers = auth_header(token)
    await _enable_module(client, headers)
    await _get_public_api_token(client, headers)
    await _create_parcel(client, headers)
    session = await _create_session(client, headers)

    response = await client.post(
        "/api/v1/public/work-sessions/signup",
        json={
            "parcel_number": "G042", "name": "", "phone": "", "email": "",
            "remarks": "", "session_ids": [session["id"]],
        },
        headers={"X-Parcella-API-Token": "test-public-api-token"},
    )
    assert response.status_code == 200, response.text
    assert response.json()["results"][0]["accepted"] is True


async def test_signup_rejects_unknown_parcel_number(client, admin_user):
    token = await login(client, "admin@example.com")
    headers = auth_header(token)
    await _enable_module(client, headers)
    await _get_public_api_token(client, headers)
    session = await _create_session(client, headers)

    response = await client.post(
        "/api/v1/public/work-sessions/signup",
        json={"parcel_number": "DOES-NOT-EXIST", "session_ids": [session["id"]]},
        headers={"X-Parcella-API-Token": "test-public-api-token"},
    )
    assert response.status_code == 404
