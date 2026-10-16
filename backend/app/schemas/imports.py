import uuid
from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel, ConfigDict, field_serializer


class ParsedLineItem(BaseModel):
    description: str | None
    expense_category: str
    financial_basis: str
    period_start: str | None
    period_end: str | None
    amount: Decimal
    currency: str
    confidence: str

    @field_serializer("amount")
    def serialize_decimal(self, v: Decimal) -> str:
        return f"{v:.6f}"


class ImportResponse(BaseModel):
    id: uuid.UUID
    account_id: uuid.UUID
    source_type: str
    status: str
    source_hash: str | None
    billing_period_start: str | None
    billing_period_end: str | None
    parsed_items: list[ParsedLineItem]
    validation_warnings: list[str]
    requires_review: bool
    imported_at: datetime


class ImportHistoryItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    account_id: uuid.UUID
    source_type: str
    source_reference: str | None
    billing_period_start: datetime | None
    billing_period_end: datetime | None
    imported_at: datetime
    status: str
