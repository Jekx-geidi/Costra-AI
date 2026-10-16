import uuid
from abc import ABC, abstractmethod
from datetime import date, datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.sync_run import SyncRun


class BaseConnector(ABC):
    provider: str = ""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def sync(self, period_start: date | None = None, period_end: date | None = None) -> SyncRun:
        run = SyncRun(
            provider=self.provider,
            job_type="api_sync",
            requested_period_start=period_start,
            requested_period_end=period_end,
            status="running",
            capability_status="unknown",
        )
        self.db.add(run)
        await self.db.flush()

        try:
            capability, records_processed = await self._execute(run.id, period_start, period_end)
            run.capability_status = capability
            run.status = "completed" if capability in ("enabled",) else "blocked"
            run.records_processed = records_processed
        except Exception as exc:
            run.status = "failed"
            run.capability_status = "error"
            run.error_summary = str(exc)[:500]

        run.finished_at = datetime.now(timezone.utc)
        return run

    @abstractmethod
    async def _execute(
        self, run_id: uuid.UUID, period_start: date | None, period_end: date | None
    ) -> tuple[str, int]:
        """Returns (capability_status, records_processed)."""
