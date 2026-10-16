import io
from decimal import Decimal

import pytest
from sqlalchemy import func, select

from app.config import settings
from app.models.audit_event import AuditEvent
from app.models.billing_record import BillingRecord
from app.models.billing_source import BillingSource
from app.services.deduplication import compute_file_hash
from app.services.ingestion.file_processor import FileProcessor

CSV = (
    "description,category,basis,amount,currency,period_start,period_end\n"
    "Claude Team seats,seat,invoice,150.00,usd,2026-09-01,2026-09-30\n"
    "API usage,api usage,invoice,82.456789,USD,2026-09-01,2026-09-30\n"
).encode()


def test_parse_csv_keeps_exact_decimals_and_normalizes():
    items, warnings = FileProcessor(db=None)._parse_csv(CSV, "USD")
    assert warnings == []
    assert [i.amount for i in items] == [Decimal("150.00"), Decimal("82.456789")]
    assert all(isinstance(i.amount, Decimal) for i in items)
    assert [i.expense_category for i in items] == ["seat", "api"]
    assert {i.financial_basis for i in items} == {"invoiced"}
    assert {i.currency for i in items} == {"USD"}


def test_parse_csv_reports_bad_rows_without_dropping_good_ones():
    content = b"description,amount\nGood,10.00\nBad,ten dollars\n"
    items, warnings = FileProcessor(db=None)._parse_csv(content, "AUD")
    assert [i.amount for i in items] == [Decimal("10.00")]
    assert items[0].currency == "AUD"  # falls back to the account currency
    assert len(warnings) == 1 and warnings[0].startswith("Row 3")


def test_file_hash_is_stable_and_content_based():
    assert compute_file_hash(CSV) == compute_file_hash(bytes(CSV))
    assert compute_file_hash(CSV) != compute_file_hash(CSV + b"\n")


@pytest.fixture
async def account_id(client, auth):
    res = await client.post("/api/ai-billing/accounts", headers=auth["billing_admin"], json={
        "provider": "anthropic", "account_reference": "org-1", "account_name": "Geidi Claude",
        "ownership_type": "geidi", "collection_method": "csv",
    })
    return res.json()["id"]


def _upload(client, headers, account_id, name, content):
    return client.post(
        "/api/ai-billing/imports",
        headers=headers,
        data={"account_id": account_id},
        files={"file": (name, io.BytesIO(content), "application/octet-stream")},
    )


async def test_csv_upload_posts_records_and_audits(client, auth, db, account_id):
    res = await _upload(client, auth["billing_admin"], account_id, "sept.csv", CSV)
    assert res.status_code == 201
    body = res.json()
    assert body["status"] == "validated"
    assert body["requires_review"] is False
    assert [i["amount"] for i in body["parsed_items"]] == ["150.000000", "82.456789"]

    records = (await db.execute(select(BillingRecord))).scalars().all()
    assert sorted(r.amount for r in records) == [Decimal("82.456789"), Decimal("150.000000")]
    assert {r.validation_status for r in records} == {"pending"}
    assert (await db.execute(select(func.count()).select_from(AuditEvent)
                             .where(AuditEvent.action == "upload"))).scalar_one() == 1


async def test_same_file_twice_is_rejected(client, auth, db, account_id):
    assert (await _upload(client, auth["billing_admin"], account_id, "a.csv", CSV)).status_code == 201
    again = await _upload(client, auth["billing_admin"], account_id, "renamed.csv", CSV)
    assert again.status_code == 409
    assert "already imported" in again.json()["detail"]
    assert (await db.execute(select(func.count()).select_from(BillingSource))).scalar_one() == 1


async def test_oversized_file_is_rejected(client, auth, monkeypatch, account_id):
    monkeypatch.setattr(settings, "max_upload_size_mb", 0)
    res = await _upload(client, auth["billing_admin"], account_id, "big.csv", CSV)
    assert res.status_code == 413


async def test_disallowed_file_type_is_rejected(client, auth, account_id):
    res = await _upload(client, auth["billing_admin"], account_id, "notes.txt", b"hello")
    assert res.status_code == 415


async def test_unknown_account_is_rejected(client, auth):
    res = await _upload(client, auth["billing_admin"], "00000000-0000-0000-0000-000000000000", "x.csv", CSV)
    assert res.status_code == 404


async def test_viewer_cannot_upload(client, auth, account_id):
    res = await _upload(client, auth["viewer"], account_id, "sept.csv", CSV)
    assert res.status_code == 403


async def test_unreadable_pdf_needs_review_and_posts_nothing(client, auth, db, account_id):
    from PIL import Image
    buf = io.BytesIO()
    Image.new("RGB", (200, 100), "white").save(buf, format="PDF")  # a PDF with no text layer
    res = await _upload(client, auth["billing_admin"], account_id, "scan.pdf", buf.getvalue())
    assert res.status_code == 201
    body = res.json()
    assert body["requires_review"] is True
    assert body["status"] == "imported"
    assert body["validation_warnings"]
    assert (await db.execute(select(func.count()).select_from(BillingRecord))).scalar_one() == 0
