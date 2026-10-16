import uuid
from decimal import Decimal
from datetime import date
from app.services.deduplication import compute_file_hash, build_fallback_record_id


def test_file_hash_deterministic():
    content = b"test invoice content"
    assert compute_file_hash(content) == compute_file_hash(content)


def test_file_hash_different_content():
    assert compute_file_hash(b"invoice A") != compute_file_hash(b"invoice B")


def test_file_hash_is_sha256_length():
    h = compute_file_hash(b"any content")
    assert len(h) == 64


def test_fallback_record_id_deterministic():
    account_id = uuid.UUID("00000000-0000-0000-0000-000000000001")
    key1 = build_fallback_record_id(
        provider="openai",
        account_id=account_id,
        invoice_number="INV-001",
        period_start=date(2026, 10, 1),
        period_end=date(2026, 10, 31),
        amount=Decimal("100.00"),
    )
    key2 = build_fallback_record_id(
        provider="openai",
        account_id=account_id,
        invoice_number="INV-001",
        period_start=date(2026, 10, 1),
        period_end=date(2026, 10, 31),
        amount=Decimal("100.00"),
    )
    assert key1 == key2
    assert key1.startswith("fallback:")


def test_fallback_record_id_different_accounts():
    acct1 = uuid.UUID("00000000-0000-0000-0000-000000000001")
    acct2 = uuid.UUID("00000000-0000-0000-0000-000000000002")
    key1 = build_fallback_record_id("openai", acct1, "INV-001", date(2026, 10, 1), date(2026, 10, 31), Decimal("100"))
    key2 = build_fallback_record_id("openai", acct2, "INV-001", date(2026, 10, 1), date(2026, 10, 31), Decimal("100"))
    assert key1 != key2


def test_fallback_record_id_different_amounts():
    acct = uuid.UUID("00000000-0000-0000-0000-000000000001")
    key1 = build_fallback_record_id("openai", acct, "INV-001", date(2026, 10, 1), date(2026, 10, 31), Decimal("100"))
    key2 = build_fallback_record_id("openai", acct, "INV-001", date(2026, 10, 1), date(2026, 10, 31), Decimal("200"))
    assert key1 != key2
