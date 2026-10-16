import uuid
from datetime import datetime, date
from decimal import Decimal
from typing import Literal
from pydantic import BaseModel, ConfigDict, field_serializer


ExpenseCategory = Literal["subscription", "seat", "api", "credit", "adjustment"]
FinancialBasis = Literal["invoiced", "usage", "payment", "credit"]
ValidationStatus = Literal["pending", "verified", "disputed"]


class BillingRecordResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    account_id: uuid.UUID
    source_id: uuid.UUID | None
    provider: str
    external_record_id: str | None
    expense_category: str
    financial_basis: str
    description: str | None
    period_start: date | None
    period_end: date | None
    quantity: Decimal | None
    amount: Decimal
    currency: str
    validation_status: str
    created_at: datetime
    updated_at: datetime

    @field_serializer("amount", "quantity")
    def serialize_decimal(self, v: Decimal | None) -> str | None:
        if v is None:
            return None
        return f"{v:.6f}"


class BillingRecordListResponse(BaseModel):
    total: int
    page: int
    page_size: int
    items: list[BillingRecordResponse]
