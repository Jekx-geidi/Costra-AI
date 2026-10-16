from datetime import date
from decimal import Decimal

import pytest
from sqlalchemy import select

from app.models.audit_event import AuditEvent
from app.models.billing_account import BillingAccount
from app.models.billing_record import BillingRecord


@pytest.fixture
async def record_id(db):
    account = BillingAccount(provider="openai", account_reference="org-r", account_name="Geidi OpenAI",
                             ownership_type="geidi", collection_method="invoice")
    db.add(account)
    await db.flush()
    record = BillingRecord(account_id=account.id, provider="openai", external_record_id="inv-1:0",
                           expense_category="seat", financial_basis="invoiced", description="ChatGPT Team",
                           period_start=date(2026, 9, 1), period_end=date(2026, 9, 30),
                           amount=Decimal("100.00"), currency="USD", validation_status="pending")
    db.add(record)
    await db.commit()
    return str(record.id)


def recon(record_id, expected, observed):
    return {"billing_record_id": record_id, "financial_reference": "XERO-INV-77",
            "expected_amount": expected, "observed_amount": observed}


@pytest.mark.parametrize("expected,observed,status,variance", [
    ("100.00", "100.00", "matched", "0.000000"),
    ("100.00", "90.00", "partial", "10.000000"),
    ("100.00", "0.00", "unmatched", "100.000000"),
])
async def test_status_follows_variance(client, auth, record_id, expected, observed, status, variance):
    res = await client.post("/api/ai-billing/reconciliation", json=recon(record_id, expected, observed),
                            headers=auth["finance_reviewer"])
    assert res.status_code == 201
    body = res.json()
    assert body["reconciliation_status"] == status
    assert body["variance"] == variance  # exact decimal string, never a float


async def test_list_filters_by_status(client, auth, record_id):
    await client.post("/api/ai-billing/reconciliation", json=recon(record_id, "100.00", "90.00"),
                      headers=auth["finance_reviewer"])
    partial = await client.get("/api/ai-billing/reconciliation", params={"reconciliation_status": "partial"},
                               headers=auth["finance_reviewer"])
    matched = await client.get("/api/ai-billing/reconciliation", params={"reconciliation_status": "matched"},
                               headers=auth["finance_reviewer"])
    assert len(partial.json()) == 1
    assert matched.json() == []


@pytest.mark.parametrize("action,validation_status", [("approve", "verified"), ("dispute", "disputed")])
async def test_review_updates_record_and_audits(client, auth, db, record_id, action, validation_status):
    await client.post("/api/ai-billing/reconciliation", json=recon(record_id, "100.00", "100.00"),
                      headers=auth["finance_reviewer"])
    res = await client.post(f"/api/ai-billing/reconciliation/{record_id}/review",
                            json={"action": action, "notes": "checked against Xero"}, headers=auth["finance_reviewer"])
    assert res.status_code == 200
    assert res.json()["reviewed_at"] is not None

    record = (await db.execute(select(BillingRecord).where(BillingRecord.id == record_id))).scalar_one()
    assert record.validation_status == validation_status
    actions = (await db.execute(select(AuditEvent.action).where(AuditEvent.resource_type == "reconciliation"))).scalars().all()
    assert sorted(actions) == sorted(["create", action])


async def test_review_without_reconciliation_is_404(client, auth, record_id):
    res = await client.post(f"/api/ai-billing/reconciliation/{record_id}/review", json={"action": "approve"},
                            headers=auth["finance_reviewer"])
    assert res.status_code == 404


async def test_viewer_is_forbidden_everywhere(client, auth, record_id):
    viewer = auth["viewer"]
    assert (await client.get("/api/ai-billing/reconciliation", headers=viewer)).status_code == 403
    assert (await client.post("/api/ai-billing/reconciliation", json=recon(record_id, "1", "1"),
                              headers=viewer)).status_code == 403
    assert (await client.post(f"/api/ai-billing/reconciliation/{record_id}/review", json={"action": "approve"},
                              headers=viewer)).status_code == 403


async def test_billing_admin_can_reconcile(client, auth, record_id):
    res = await client.post("/api/ai-billing/reconciliation", json=recon(record_id, "100.00", "100.00"),
                            headers=auth["billing_admin"])
    assert res.status_code == 201


async def test_list_shows_record_review_outcome(client, auth, record_id):
    await client.post("/api/ai-billing/reconciliation", json=recon(record_id, "100.00", "90.00"),
                      headers=auth["finance_reviewer"])
    before = (await client.get("/api/ai-billing/reconciliation", headers=auth["finance_reviewer"])).json()
    assert before[0]["record_validation_status"] == "pending"
    await client.post(f"/api/ai-billing/reconciliation/{record_id}/review", json={"action": "dispute"},
                      headers=auth["finance_reviewer"])
    after = (await client.get("/api/ai-billing/reconciliation", headers=auth["finance_reviewer"])).json()
    assert after[0]["record_validation_status"] == "disputed"
    assert after[0]["reviewed_at"] is not None


async def test_unknown_record_is_404_not_500(client, auth):
    res = await client.post("/api/ai-billing/reconciliation", headers=auth["finance_reviewer"],
                            json=recon("00000000-0000-0000-0000-000000000000", "1.00", "1.00"))
    assert res.status_code == 404


async def test_review_after_reconciling_twice_uses_latest(client, auth, record_id):
    for observed in ("90.00", "100.00"):
        res = await client.post("/api/ai-billing/reconciliation", json=recon(record_id, "100.00", observed),
                                headers=auth["finance_reviewer"])
        assert res.status_code == 201
    review = await client.post(f"/api/ai-billing/reconciliation/{record_id}/review", json={"action": "approve"},
                               headers=auth["finance_reviewer"])
    assert review.status_code == 200
    assert review.json()["reconciliation_status"] == "matched"  # the second, latest attempt
    assert review.json()["record_validation_status"] == "verified"
