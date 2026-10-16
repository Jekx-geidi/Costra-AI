import uuid
from datetime import datetime
from decimal import Decimal
from typing import Literal
from pydantic import BaseModel, ConfigDict, field_serializer


ReconciliationStatus = Literal["matched", "unmatched", "partial"]
ReviewAction = Literal["approve", "dispute"]


class ReconciliationCreate(BaseModel):
    billing_record_id: uuid.UUID
    financial_reference: str | None = None
    expected_amount: Decimal
    observed_amount: Decimal

    @property
    def variance(self) -> Decimal:
        return self.expected_amount - self.observed_amount


class ReconciliationReviewRequest(BaseModel):
    action: ReviewAction
    notes: str | None = None


class ReconciliationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    billing_record_id: uuid.UUID
    financial_reference: str | None
    expected_amount: Decimal
    observed_amount: Decimal
    variance: Decimal
    reconciliation_status: str
    reviewed_by: uuid.UUID | None
    reviewed_at: datetime | None
    created_at: datetime
    record_validation_status: str | None = None  # pending / verified / disputed on the billing record

    @field_serializer("expected_amount", "observed_amount", "variance")
    def serialize_decimal(self, v: Decimal) -> str:
        return f"{v:.6f}"
