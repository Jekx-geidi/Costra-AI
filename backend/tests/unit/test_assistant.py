import pytest
from datetime import date
from decimal import Decimal
from app.services.assistant.guard import (
    BLOCKED_REPLY,
    build_system_prompt,
    contains_code,
    sanitize_reply,
)
from app.services.assistant.invoice import _parse_json_object, normalize_extraction


@pytest.mark.parametrize("text", [
    "```sql\nSELECT 1\n```",
    "Run SELECT amount FROM ai_billing_records to see it.",
    "select * from users",
    "INSERT INTO ai_billing_records VALUES (1)",
    "UPDATE ai_billing_accounts SET is_active = false",
    "DELETE FROM ai_billing_sources",
    "drop table users",
    "def total(records):\n    return sum(records)",
    "import requests",
    "const f = () => { return 1 }",
    "$ curl http://localhost:8001/api",
])
def test_code_and_sql_are_detected(text):
    assert contains_code(text)
    assert sanitize_reply(text) == BLOCKED_REPLY


@pytest.mark.parametrize("text", [
    "Ang total nga AI spend sa 2026-09 kay 232.45 USD.",
    "Select the Anthropic account from the dropdown, then click Import.",
    "You can update the account from the Integrations screen.",
    "OpenAI: 150.00 USD (subscription), 82.45 USD (API usage).",
    "Delete is not something I can do — ask a billing admin.",
])
def test_plain_answers_pass_through(text):
    assert not contains_code(text)
    assert sanitize_reply(text) == text


def test_reasoning_blocks_are_stripped():
    assert sanitize_reply("<think>internal notes</think>Ang total kay 10.00 USD.") == "Ang total kay 10.00 USD."
    assert sanitize_reply("notes cut off</think>Answer") == "Answer"


def test_bold_markers_are_removed():
    assert sanitize_reply("Total kay **244.82 USD** ug __partial__.") == "Total kay 244.82 USD ug partial."


def test_empty_reply_gets_fallback():
    assert "try again" in sanitize_reply("   ")


def test_system_prompt_contains_rules_and_snapshot():
    prompt = build_system_prompt('{"today":"2026-10-16"}', "2026-10-16T00:00:00+00:00")
    assert "Never write code" in prompt
    assert "politely decline" in prompt
    assert '{"today":"2026-10-16"}' in prompt


def test_parse_json_object_handles_fences_and_chatter():
    assert _parse_json_object('```json\n{"a": 1}\n```') == {"a": 1}
    assert _parse_json_object('Here it is: {"a": {"b": 2}} done') == {"a": {"b": 2}}
    with pytest.raises(ValueError):
        _parse_json_object("no json here")


def test_normalize_extraction_keeps_exact_decimals():
    raw = {
        "is_invoice": True, "vendor_name": "OpenAI, L.L.C.", "provider": None, "invoice_number": "INV-2041",
        "currency": "usd", "period_start": "2026-09-01", "period_end": "2026-09-30", "total": "232.45",
        "line_items": [
            {"description": "ChatGPT Team seats x5", "category": "seat", "financial_basis": "invoiced", "amount": "150.00"},
            {"description": "API usage", "category": "api", "financial_basis": "usage", "amount": 82.45},
        ],
    }
    result = normalize_extraction(raw, "USD")
    assert result["provider"] == "openai"
    assert result["currency"] == "USD"
    assert [i["amount"] for i in result["items"]] == [Decimal("150.00"), Decimal("82.45")]
    assert all(isinstance(i["amount"], Decimal) for i in result["items"])
    assert result["items"][0]["period_start"] == date(2026, 9, 1)  # inherits invoice period
    assert result["warnings"] == []


def test_normalize_extraction_flags_problems():
    raw = {
        "total": "100.00",
        "line_items": [
            {"description": "Claude Team", "category": "subscription", "amount": "90.00"},
            {"description": "Unreadable", "amount": None},
        ],
    }
    result = normalize_extraction(raw, "USD")
    assert len(result["items"]) == 1
    warnings = " ".join(result["warnings"])
    assert "Line 2" in warnings
    assert "add up to 90.00" in warnings
    assert "No billing period" in warnings


def test_non_invoice_is_reported():
    result = normalize_extraction({"is_invoice": False}, "USD")
    assert result["is_invoice"] is False
    assert result["items"] == []


def test_line_item_dump_keeps_decimal_but_json_is_exact_string():
    from app.schemas.assistant import InvoiceLineItem
    item = InvoiceLineItem(description="API usage", expense_category="api", financial_basis="invoiced",
                           amount="82.45", currency="USD")
    assert item.model_dump()["amount"] == Decimal("82.45")  # services add these up
    assert item.model_dump(mode="json")["amount"] == "82.450000"  # API responses stay exact strings
