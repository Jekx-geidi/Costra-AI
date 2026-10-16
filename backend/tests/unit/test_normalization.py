import pytest
from decimal import Decimal
from app.services.normalization import (
    normalize_expense_category,
    normalize_financial_basis,
    normalize_provider,
    normalize_currency,
    normalize_amount,
)


@pytest.mark.parametrize("raw,expected", [
    ("subscription", "subscription"),
    ("Monthly Plan", "subscription"),
    ("seat license", "seat"),
    ("api usage", "api"),
    ("prepaid credit", "credit"),
    ("refund", "adjustment"),
    ("unknown_thing", "api"),
    (None, "api"),
    ("", "api"),
])
def test_normalize_expense_category(raw, expected):
    assert normalize_expense_category(raw) == expected


@pytest.mark.parametrize("raw,expected", [
    ("invoiced", "invoiced"),
    ("invoice", "invoiced"),
    ("usage", "usage"),
    ("consumption", "usage"),
    ("payment", "payment"),
    ("credit", "credit"),
    (None, "invoiced"),
    ("unknown", "invoiced"),
])
def test_normalize_financial_basis(raw, expected):
    assert normalize_financial_basis(raw) == expected


@pytest.mark.parametrize("raw,expected", [
    ("openai", "openai"),
    ("OpenAI Platform", "openai"),
    ("ChatGPT", "openai"),
    ("anthropic", "anthropic"),
    ("Claude API", "anthropic"),
    ("Anthropic Console", "anthropic"),
    (None, "unknown"),
])
def test_normalize_provider(raw, expected):
    assert normalize_provider(raw) == expected


@pytest.mark.parametrize("raw,default,expected", [
    ("usd", "USD", "USD"),
    ("aud", "USD", "AUD"),
    (None, "USD", "USD"),
    ("", "AUD", "AUD"),
])
def test_normalize_currency(raw, default, expected):
    assert normalize_currency(raw, default) == expected


@pytest.mark.parametrize("raw,expected", [
    ("10.50", Decimal("10.50")),
    (10, Decimal("10")),
    (Decimal("99.999999"), Decimal("99.999999")),
    ("1,000.00", ValueError),
    (None, ValueError),
])
def test_normalize_amount(raw, expected):
    if expected is ValueError:
        with pytest.raises(ValueError):
            normalize_amount(raw)
    else:
        result = normalize_amount(raw)
        assert result == expected
        assert isinstance(result, Decimal)
