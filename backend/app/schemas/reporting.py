from decimal import Decimal
from typing import Literal
from pydantic import BaseModel, field_serializer


CoverageStatus = Literal["complete", "partial", "unavailable"]
DataStatus = Literal["complete", "partial", "unavailable"]


class ProviderTotals(BaseModel):
    openai: Decimal | None = None
    anthropic: Decimal | None = None
    currency: str

    @field_serializer("openai", "anthropic")
    def serialize_decimal(self, v: Decimal | None) -> str | None:
        if v is None:
            return None
        return f"{v:.6f}"


class SummaryResponse(BaseModel):
    period: str
    currency: str
    actual_expense: Decimal
    api_consumption_cost: Decimal
    subscription_cost: Decimal
    providers: ProviderTotals
    data_status: DataStatus
    unreconciled_records: int
    missing_providers: list[str]

    @field_serializer("actual_expense", "api_consumption_cost", "subscription_cost")
    def serialize_decimal(self, v: Decimal) -> str:
        return f"{v:.6f}"


class MonthTrend(BaseModel):
    period: str
    actual_expense: Decimal | None
    coverage_status: CoverageStatus
    currency: str

    @field_serializer("actual_expense")
    def serialize_decimal(self, v: Decimal | None) -> str | None:
        if v is None:
            return None
        return f"{v:.6f}"


class TrendResponse(BaseModel):
    months: list[MonthTrend]
    currency: str
