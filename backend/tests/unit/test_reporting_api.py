from datetime import date
from decimal import Decimal

from app.models.billing_account import BillingAccount
from app.models.billing_record import BillingRecord


async def seed(db, *rows):
    accounts = {}
    for provider, ownership in {(r[0], r[1]) for r in rows}:
        accounts[(provider, ownership)] = BillingAccount(
            provider=provider, account_reference=f"{provider}-{ownership}", account_name=f"{provider} {ownership}",
            ownership_type=ownership, collection_method="invoice")
    db.add_all(accounts.values())
    await db.flush()
    for i, (provider, ownership, month, basis, category, amount, status) in enumerate(rows):
        db.add(BillingRecord(account_id=accounts[(provider, ownership)].id, provider=provider, external_record_id=f"r{i}",
                             expense_category=category, financial_basis=basis, period_start=date(2026, month, 1),
                             amount=Decimal(amount), currency="USD", validation_status=status))
    await db.commit()


async def test_trends_cover_twelve_months_and_empty_months_are_unavailable(client, auth):
    res = await client.get("/api/ai-billing/trends", params={"months": 12}, headers=auth["viewer"])
    assert res.status_code == 200
    months = res.json()["months"]
    assert len(months) == 12
    for m in months:
        assert m["coverage_status"] == "unavailable"
        assert m["actual_expense"] is None  # never a fake "0.000000"


async def test_summary_rules(client, auth, db):
    await seed(
        db,
        ("openai", "geidi", 9, "invoiced", "seat", "150.00", "pending"),
        ("openai", "geidi", 9, "usage", "api", "82.45", "verified"),
        ("anthropic", "geidi", 9, "invoiced", "subscription", "30.00", "verified"),
        ("anthropic", "geidi", 9, "invoiced", "api", "999.00", "disputed"),   # disputed: excluded
        ("openai", "personal", 9, "invoiced", "subscription", "20.00", "verified"),  # not Geidi: excluded
    )
    res = await client.get("/api/ai-billing/summary", params={"period": "2026-09"}, headers=auth["viewer"])
    assert res.status_code == 200
    s = res.json()
    assert s["actual_expense"] == "180.000000"        # invoiced only: 150 + 30
    assert s["api_consumption_cost"] == "82.450000"   # usage basis
    assert s["subscription_cost"] == "180.000000"     # seat + subscription
    assert s["providers"]["openai"] == "232.450000"
    assert s["providers"]["anthropic"] == "30.000000"
    assert s["data_status"] == "complete"
    assert s["unreconciled_records"] == 1
    assert s["missing_providers"] == []


async def test_summary_partial_and_unavailable(client, auth, db):
    await seed(db, ("openai", "geidi", 9, "invoiced", "seat", "10.00", "pending"))
    partial = (await client.get("/api/ai-billing/summary", params={"period": "2026-09"}, headers=auth["viewer"])).json()
    assert partial["data_status"] == "partial"
    assert partial["missing_providers"] == ["anthropic"]
    assert partial["providers"]["anthropic"] is None

    empty = (await client.get("/api/ai-billing/summary", params={"period": "2026-08"}, headers=auth["viewer"])).json()
    assert empty["data_status"] == "unavailable"


async def test_summary_requires_period(client, auth):
    res = await client.get("/api/ai-billing/summary", headers=auth["viewer"])
    assert res.status_code == 422
