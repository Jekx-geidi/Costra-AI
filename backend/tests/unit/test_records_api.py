"""Billing records listing (filters, ownership scoping) and the database-level dedup guarantee."""
from datetime import date
from decimal import Decimal

import pytest
from sqlalchemy import func, select

from app.models.billing_account import BillingAccount
from app.models.billing_record import BillingRecord
from app.models.reconciliation import Reconciliation
from app.services.deduplication import upsert_billing_record


@pytest.fixture
async def seeded(db):
    geidi_openai = BillingAccount(provider="openai", account_reference="o", account_name="Geidi OpenAI",
                                  ownership_type="geidi", collection_method="api")
    geidi_claude = BillingAccount(provider="anthropic", account_reference="a", account_name="Geidi Claude",
                                  ownership_type="geidi", collection_method="invoice")
    personal = BillingAccount(provider="openai", account_reference="p", account_name="Personal ChatGPT",
                              ownership_type="personal", collection_method="invoice")
    db.add_all([geidi_openai, geidi_claude, personal])
    await db.flush()

    def rec(account, ext, month, category, basis, amount, status="pending"):
        return BillingRecord(account_id=account.id, provider=account.provider, external_record_id=ext,
                             expense_category=category, financial_basis=basis,
                             period_start=date(2026, month, 1), period_end=date(2026, month, 28),
                             amount=Decimal(amount), currency="USD", validation_status=status)

    records = [
        rec(geidi_openai, "o-9-api", 9, "api", "usage", "82.45", "verified"),
        rec(geidi_openai, "o-10-api", 10, "api", "usage", "96.10"),
        rec(geidi_claude, "a-9-seat", 9, "seat", "invoiced", "150.00"),
        rec(personal, "p-9-sub", 9, "subscription", "invoiced", "20.00"),
    ]
    db.add_all(records)
    await db.flush()
    db.add(Reconciliation(billing_record_id=records[2].id, expected_amount=Decimal("150.00"),
                          observed_amount=Decimal("140.00"), variance=Decimal("10.00"),
                          reconciliation_status="partial"))
    await db.commit()


async def list_records(client, auth, **params):
    res = await client.get("/api/ai-billing/records", params=params, headers=auth["viewer"])
    assert res.status_code == 200
    return res.json()


async def test_defaults_to_geidi_owned_accounts_only(client, auth, seeded):
    body = await list_records(client, auth)
    assert body["total"] == 3
    assert "Personal" not in str(body)
    personal = await list_records(client, auth, ownership_type="personal")
    assert personal["total"] == 1


@pytest.mark.parametrize("params,expected_amounts", [
    ({"provider": "openai"}, ["82.450000", "96.100000"]),
    ({"period": "2026-09"}, ["150.000000", "82.450000"]),
    ({"period": "2026-09", "provider": "anthropic"}, ["150.000000"]),
    ({"expense_category": "seat"}, ["150.000000"]),
    ({"financial_basis": "usage", "validation_status": "pending"}, ["96.100000"]),
    ({"validation_status": "verified"}, ["82.450000"]),
    ({"reconciliation_status": "partial"}, ["150.000000"]),
    ({"reconciliation_status": "matched"}, []),
])
async def test_filters_return_the_right_subset(client, auth, seeded, params, expected_amounts):
    body = await list_records(client, auth, **params)
    assert sorted(r["amount"] for r in body["items"]) == sorted(expected_amounts)
    assert body["total"] == len(expected_amounts)


async def test_paging(client, auth, seeded):
    first = await list_records(client, auth, page=1, page_size=2)
    second = await list_records(client, auth, page=2, page_size=2)
    assert first["total"] == second["total"] == 3
    assert len(first["items"]) == 2 and len(second["items"]) == 1
    assert {r["id"] for r in first["items"]}.isdisjoint({r["id"] for r in second["items"]})


async def test_upsert_with_same_dedup_key_keeps_one_row(db, seeded):
    account = (await db.execute(select(BillingAccount).where(BillingAccount.account_name == "Geidi OpenAI"))).scalar_one()
    kwargs = dict(account_id=account.id, source_id=None, provider="openai", external_record_id="dup-key",
                  expense_category="api", financial_basis="usage", description="first", period_start=None,
                  period_end=None, quantity=None, currency="USD")
    first_id = await upsert_billing_record(db, amount=Decimal("1.00"), **kwargs)
    second_id = await upsert_billing_record(db, amount=Decimal("2.00"), **{**kwargs, "description": "second"})
    await db.commit()

    assert first_id == second_id
    rows = (await db.execute(select(BillingRecord).where(BillingRecord.external_record_id == "dup-key"))).scalars().all()
    assert len(rows) == 1
    assert rows[0].amount == Decimal("2.00") and rows[0].description == "second"  # latest values win
    assert (await db.execute(select(func.count()).select_from(BillingRecord))).scalar_one() == 5
