import uuid
from datetime import datetime, date
from typing import Literal
from pydantic import BaseModel, ConfigDict


SourceType = Literal["api", "pdf", "csv", "statement"]
SourceStatus = Literal["imported", "validated", "rejected"]


class BillingSourceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    account_id: uuid.UUID
    source_type: str
    source_reference: str | None
    billing_period_start: date | None
    billing_period_end: date | None
    imported_at: datetime
    status: str
