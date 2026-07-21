"""
Tests for the Inventory module: categories (freely configurable),
items (club- or member-owned, with financial fields), and the
quantity-aware lending system.

Category/item/loan CRUD is tested via the JWT API (this module has a
full REST API alongside its web UI, per the project's "API-first"
convention). A few web-UI-specific things -- route-registration
ordering (a real bug found and fixed while building this: /categories/
and /new must be registered before the single-segment /{item_id}
catch-all, or they'd be swallowed by it) and the require_admin
permission boundary for mutating actions -- are tested via the
cookie-based web login instead, since that's what those routes
actually use.
"""
from tests.conftest import login, auth_header


async def web_login(client, email: str, password: str = "testpasswort123") -> None:
    response = await client.post("/auth/login", data={"email": email, "password": password})
    assert response.status_code in (302, 303)


# ---------------------------------------------------------------------------
# Categories
# ---------------------------------------------------------------------------

async def test_create_and_list_categories(client, admin_user):
    token = await login(client, "admin@example.com")
    headers = auth_header(token)

    response = await client.post(
        "/api/v1/inventory/categories", json={"name": "Playground", "description": "Slides, swings, sandbox"},
        headers=headers,
    )
    assert response.status_code == 201
    category = response.json()
    assert category["name"] == "Playground"

    listing = await client.get("/api/v1/inventory/categories", headers=headers)
    assert listing.status_code == 200
    assert any(c["name"] == "Playground" for c in listing.json())


async def test_duplicate_category_name_rejected(client, admin_user):
    token = await login(client, "admin@example.com")
    headers = auth_header(token)

    await client.post("/api/v1/inventory/categories", json={"name": "Fences"}, headers=headers)
    duplicate = await client.post("/api/v1/inventory/categories", json={"name": "Fences"}, headers=headers)
    assert duplicate.status_code == 400


async def test_deleting_category_does_not_delete_its_items(client, admin_user):
    token = await login(client, "admin@example.com")
    headers = auth_header(token)

    category = (await client.post(
        "/api/v1/inventory/categories", json={"name": "Locks & Keys"}, headers=headers,
    )).json()

    item = (await client.post(
        "/api/v1/inventory/items",
        json={"name": "Gate padlock", "category_id": category["id"]},
        headers=headers,
    )).json()

    delete_response = await client.delete(f"/api/v1/inventory/categories/{category['id']}", headers=headers)
    assert delete_response.status_code == 204

    still_there = await client.get(f"/api/v1/inventory/items/{item['id']}", headers=headers)
    assert still_there.status_code == 200
    assert still_there.json()["category_id"] is None


# ---------------------------------------------------------------------------
# Items -- ownership and financials
# ---------------------------------------------------------------------------

async def test_create_club_owned_item_with_financials(client, admin_user):
    token = await login(client, "admin@example.com")
    headers = auth_header(token)

    response = await client.post(
        "/api/v1/inventory/items",
        json={
            "name": "Wheelbarrow", "owner_type": "CLUB",
            "purchase_date": "2022-04-01", "purchase_price": "89.90",
            "current_value": "40.00", "current_value_updated_at": "2026-01-01",
            "replacement_cost": "110.00", "quantity_total": 3,
        },
        headers=headers,
    )
    assert response.status_code == 201
    item = response.json()
    assert item["quantity_total"] == 3
    assert item["quantity_on_loan"] == 0
    assert item["available_quantity"] == 3
    assert item["purchase_price"] == "89.90"


async def test_member_owned_item_requires_owner_member_id(client, admin_user):
    token = await login(client, "admin@example.com")
    headers = auth_header(token)

    member = (await client.post(
        "/api/v1/members", json={"first_name": "Anna", "last_name": "Muster"}, headers=headers,
    )).json()

    missing_owner = await client.post(
        "/api/v1/inventory/items", json={"name": "Personal tent", "owner_type": "MEMBER"}, headers=headers,
    )
    assert missing_owner.status_code == 400

    with_owner = await client.post(
        "/api/v1/inventory/items",
        json={
            "name": "Personal tent", "owner_type": "MEMBER", "owner_member_id": member["id"],
            "purchase_price": "150.00",
        },
        headers=headers,
    )
    assert with_owner.status_code == 201
    item = with_owner.json()
    assert item["owner_type"] == "MEMBER"
    assert item["owner_member_id"] == member["id"]
    # Explicit product decision: personally-owned items get the same
    # financial fields as club-owned ones.
    assert item["purchase_price"] == "150.00"


async def test_retired_items_excluded_from_list_by_default(client, admin_user):
    token = await login(client, "admin@example.com")
    headers = auth_header(token)

    item = (await client.post(
        "/api/v1/inventory/items", json={"name": "Old lawnmower"}, headers=headers,
    )).json()

    await client.post(f"/api/v1/inventory/items/{item['id']}/retire", headers=headers)

    default_list = await client.get("/api/v1/inventory/items", headers=headers)
    assert not any(i["id"] == item["id"] for i in default_list.json())

    with_retired = await client.get("/api/v1/inventory/items?include_retired=true", headers=headers)
    assert any(i["id"] == item["id"] for i in with_retired.json())


# ---------------------------------------------------------------------------
# Loans -- quantity-aware checkout/return
# ---------------------------------------------------------------------------

async def test_loan_checkout_reduces_available_quantity(client, admin_user):
    token = await login(client, "admin@example.com")
    headers = auth_header(token)

    member = (await client.post(
        "/api/v1/members", json={"first_name": "Bernd", "last_name": "Beispiel"}, headers=headers,
    )).json()
    item = (await client.post(
        "/api/v1/inventory/items",
        json={"name": "Tent", "is_borrowable": True, "quantity_total": 5, "default_loan_fee": "5.00"},
        headers=headers,
    )).json()

    loan = await client.post(
        f"/api/v1/inventory/items/{item['id']}/loans",
        json={"member_id": member["id"], "quantity": 2, "borrowed_date": "2026-07-01"},
        headers=headers,
    )
    assert loan.status_code == 201
    loan_data = loan.json()
    # No fee_charged given -> falls back to the item's default_loan_fee.
    assert loan_data["fee_charged"] == "5.00"

    updated_item = (await client.get(f"/api/v1/inventory/items/{item['id']}", headers=headers)).json()
    assert updated_item["quantity_on_loan"] == 2
    assert updated_item["available_quantity"] == 3


async def test_loan_checkout_rejects_more_than_available(client, admin_user):
    token = await login(client, "admin@example.com")
    headers = auth_header(token)

    member = (await client.post(
        "/api/v1/members", json={"first_name": "Carla", "last_name": "Testperson"}, headers=headers,
    )).json()
    item = (await client.post(
        "/api/v1/inventory/items", json={"name": "Tent", "is_borrowable": True, "quantity_total": 2},
        headers=headers,
    )).json()

    too_many = await client.post(
        f"/api/v1/inventory/items/{item['id']}/loans",
        json={"member_id": member["id"], "quantity": 3, "borrowed_date": "2026-07-01"},
        headers=headers,
    )
    assert too_many.status_code == 400


async def test_loan_checkout_rejected_for_non_borrowable_item(client, admin_user):
    token = await login(client, "admin@example.com")
    headers = auth_header(token)

    member = (await client.post(
        "/api/v1/members", json={"first_name": "Dieter", "last_name": "Testperson"}, headers=headers,
    )).json()
    item = (await client.post(
        "/api/v1/inventory/items", json={"name": "Office printer", "is_borrowable": False},
        headers=headers,
    )).json()

    response = await client.post(
        f"/api/v1/inventory/items/{item['id']}/loans",
        json={"member_id": member["id"], "quantity": 1, "borrowed_date": "2026-07-01"},
        headers=headers,
    )
    assert response.status_code == 400


async def test_returning_a_loan_restores_availability(client, admin_user):
    token = await login(client, "admin@example.com")
    headers = auth_header(token)

    member = (await client.post(
        "/api/v1/members", json={"first_name": "Erika", "last_name": "Testperson"}, headers=headers,
    )).json()
    item = (await client.post(
        "/api/v1/inventory/items", json={"name": "Rake", "is_borrowable": True, "quantity_total": 1},
        headers=headers,
    )).json()

    loan = (await client.post(
        f"/api/v1/inventory/items/{item['id']}/loans",
        json={"member_id": member["id"], "quantity": 1, "borrowed_date": "2026-07-01"},
        headers=headers,
    )).json()

    fully_booked = (await client.get(f"/api/v1/inventory/items/{item['id']}", headers=headers)).json()
    assert fully_booked["available_quantity"] == 0

    return_response = await client.post(
        f"/api/v1/inventory/loans/{loan['id']}/return", json={"returned_date": "2026-07-05"}, headers=headers,
    )
    assert return_response.status_code == 200
    assert return_response.json()["returned_date"] == "2026-07-05"

    available_again = (await client.get(f"/api/v1/inventory/items/{item['id']}", headers=headers)).json()
    assert available_again["available_quantity"] == 1

    # Returning an already-returned loan is rejected, not silently
    # no-op'd -- catches a double-click or duplicate submission.
    double_return = await client.post(
        f"/api/v1/inventory/loans/{loan['id']}/return", json={}, headers=headers,
    )
    assert double_return.status_code == 400


async def test_active_loans_endpoint_lists_only_outstanding(client, admin_user):
    token = await login(client, "admin@example.com")
    headers = auth_header(token)

    member = (await client.post(
        "/api/v1/members", json={"first_name": "Franz", "last_name": "Testperson"}, headers=headers,
    )).json()
    item = (await client.post(
        "/api/v1/inventory/items", json={"name": "Ladder", "is_borrowable": True, "quantity_total": 2},
        headers=headers,
    )).json()

    loan_a = (await client.post(
        f"/api/v1/inventory/items/{item['id']}/loans",
        json={"member_id": member["id"], "quantity": 1, "borrowed_date": "2026-07-01"},
        headers=headers,
    )).json()
    loan_b = (await client.post(
        f"/api/v1/inventory/items/{item['id']}/loans",
        json={"member_id": member["id"], "quantity": 1, "borrowed_date": "2026-07-02"},
        headers=headers,
    )).json()
    await client.post(f"/api/v1/inventory/loans/{loan_a['id']}/return", json={}, headers=headers)

    active = await client.get("/api/v1/inventory/loans", headers=headers)
    assert active.status_code == 200
    active_ids = [loan["id"] for loan in active.json()]
    assert loan_b["id"] in active_ids
    assert loan_a["id"] not in active_ids


# ---------------------------------------------------------------------------
# Web UI -- route ordering and permissions
# ---------------------------------------------------------------------------

async def test_web_categories_page_is_not_shadowed_by_item_detail_route(client, admin_user):
    """Regression check for a real bug found while building this: the
    single-segment GET /{item_id} catch-all was initially registered
    before GET /categories/, which would have made Starlette match
    "categories" as an item_id and 404 instead of showing the
    categories page."""
    await web_login(client, "admin@example.com")
    response = await client.get("/inventory/categories/")
    assert response.status_code == 200
    assert "categor" in response.text.lower()


async def test_web_new_item_form_is_not_shadowed_by_item_detail_route(client, admin_user):
    await web_login(client, "admin@example.com")
    response = await client.get("/inventory/new")
    assert response.status_code == 200


async def test_web_active_loans_page_is_not_shadowed_by_item_detail_route(client, admin_user):
    await web_login(client, "admin@example.com")
    response = await client.get("/inventory/loans/active")
    assert response.status_code == 200


async def test_readonly_role_can_view_but_not_create_items(client, admin_user):
    token = await login(client, "admin@example.com")
    headers = auth_header(token)

    from app.database import AsyncSessionLocal
    from app.models import User, UserRole
    from app.auth import hash_password

    async with AsyncSessionLocal() as session:
        session.add(User(
            email="readonly@example.com", name="Test-Readonly",
            password_hash=hash_password("testpasswort123"), role=UserRole.READONLY,
        ))
        await session.commit()

    await web_login(client, "readonly@example.com")

    view_response = await client.get("/inventory/")
    assert view_response.status_code == 200

    create_response = await client.get("/inventory/new")
    assert create_response.status_code == 403
