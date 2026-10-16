import uuid
from datetime import datetime, date
from pydantic import BaseModel, ConfigDict


class SyncTriggerRequest(BaseModel):
    period_start: date | None = None
    period_end: date | None = None


class SyncRunResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    account_id: uuid.UUID | None
    provider: str
    job_type: str
    requested_period_start: date | None
    requested_period_end: date | None
    started_at: datetime
    finished_at: datetime | None
    status: str
    capability_status: str
    records_processed: int
    error_summary: str | None
