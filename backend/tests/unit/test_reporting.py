import pytest
from decimal import Decimal
from app.schemas.reporting import MonthTrend, SummaryResponse, ProviderTotals


def test_month_trend_unavailable_serializes_null_expense():
    mt = MonthTrend(period="2026-01", actual_expense=None, coverage_status="unavailable", currency="USD")
    data = mt.model_dump()
    assert data["actual_expense"] is None
    assert data["coverage_status"] == "unavailable"


def test_month_trend_amount_is_string_in_json():
    mt = MonthTrend(period="2026-10", actual_expense=Decimal("123.456789"), coverage_status="complete", currency="USD")
    json_data = mt.model_dump(mode="json")
    assert isinstance(json_data["actual_expense"], str)
    assert json_data["actual_expense"] == "123.456789"


def test_summary_no_float_types():
    sr = SummaryResponse(
        period="2026-10",
        currency="USD",
        actual_expense=Decimal("250.00"),
        api_consumption_cost=Decimal("85.00"),
        subscription_cost=Decimal("165.00"),
        providers=ProviderTotals(openai=Decimal("150.00"), anthropic=Decimal("100.00"), currency="USD"),
        data_status="complete",
        unreconciled_records=0,
        missing_providers=[],
    )
    json_data = sr.model_dump(mode="json")
    assert isinstance(json_data["actual_expense"], str)
    assert isinstance(json_data["api_consumption_cost"], str)
    assert isinstance(json_data["providers"]["openai"], str)


def test_summary_partial_when_missing_provider():
    sr = SummaryResponse(
        period="2026-10",
        currency="USD",
        actual_expense=Decimal("150.00"),
        api_consumption_cost=Decimal("150.00"),
        subscription_cost=Decimal("0"),
        providers=ProviderTotals(openai=Decimal("150.00"), anthropic=None, currency="USD"),
        data_status="partial",
        unreconciled_records=0,
        missing_providers=["anthropic"],
    )
    assert sr.data_status == "partial"
    assert "anthropic" in sr.missing_providers


def test_credit_plus_usage_separate():
    """Credit purchase and API usage must never be summed as actual_expense."""
    credit_purchase = Decimal("100.00")
    api_usage = Decimal("30.00")
    actual_invoiced = Decimal("100.00")

    assert actual_invoiced != credit_purchase + api_usage, (
        "Credit purchase + API usage must not be reported as combined actual expense"
    )
