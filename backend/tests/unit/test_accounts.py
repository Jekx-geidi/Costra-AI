from sqlalchemy import select
from app.models.audit_event import AuditEvent

ACCOUNT = {
    "provider": "anthropic",
    "account_reference": "org-test-anthropic",
    "account_name": "Geidi Claude Team",
    "ownership_type": "geidi",
    "collection_method": "invoice",
}


async def test_create_list_and_audit(client, auth, db):
    res = await client.post("/api/ai-billing/accounts", json=ACCOUNT, headers=auth["billing_admin"])
    assert res.status_code == 201
    created = res.json()
    assert created["default_currency"] == "USD"
    assert created["authorization_status"] == "pending"

    listed = await client.get("/api/ai-billing/accounts", headers=auth["viewer"])
    assert listed.status_code == 200
    assert [a["id"] for a in listed.json()] == [created["id"]]

    events = (await db.execute(select(AuditEvent).where(AuditEvent.resource_type == "billing_account"))).scalars().all()
    assert len(events) == 1
    assert events[0].principal_email == "billing_admin@test.geidi"


async def test_only_billing_admin_can_create(client, auth):
    for role in ("viewer", "finance_reviewer"):
        res = await client.post("/api/ai-billing/accounts", json=ACCOUNT, headers=auth[role])
        assert res.status_code == 403, role


async def test_update_account(client, auth):
    created = (await client.post("/api/ai-billing/accounts", json=ACCOUNT, headers=auth["billing_admin"])).json()
    res = await client.patch(
        f"/api/ai-billing/accounts/{created['id']}",
        json={"authorization_status": "authorized"},
        headers=auth["billing_admin"],
    )
    assert res.status_code == 200
    assert res.json()["authorization_status"] == "authorized"

    denied = await client.patch(
        f"/api/ai-billing/accounts/{created['id']}", json={"is_active": False}, headers=auth["viewer"],
    )
    assert denied.status_code == 403


async def test_invalid_currency_rejected(client, auth):
    res = await client.post(
        "/api/ai-billing/accounts", json={**ACCOUNT, "default_currency": "DOLLARS"}, headers=auth["billing_admin"],
    )
    assert res.status_code == 422


async def test_requests_without_valid_token_are_rejected(client, auth):
    assert (await client.get("/api/auth/me")).status_code == 401
    assert (await client.get("/api/ai-billing/accounts")).status_code == 401
    bad = {"Authorization": "Bearer not.a.token"}
    assert (await client.get("/api/auth/me", headers=bad)).status_code == 401


async def test_me_returns_role_without_secrets(client, auth):
    res = await client.get("/api/auth/me", headers=auth["finance_reviewer"])
    assert res.status_code == 200
    body = res.json()
    assert body["role"] == "finance_reviewer"
    assert "hashed_password" not in body
