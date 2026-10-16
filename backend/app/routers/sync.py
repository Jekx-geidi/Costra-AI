from typing import Literal
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.models.user import User
from app.auth.dependencies import require_billing_admin
from app.schemas.sync_run import SyncTriggerRequest, SyncRunResponse
from app.services.ingestion.openai_connector import OpenAIConnector
from app.services.ingestion.anthropic_connector import AnthropicConnector
from app.utils.audit import write_audit

router = APIRouter()

_connectors = {
    "openai": OpenAIConnector,
    "anthropic": AnthropicConnector,
}


@router.post("/{provider}", response_model=SyncRunResponse)
async def trigger_sync(
    provider: Literal["openai", "anthropic"],
    body: SyncTriggerRequest,
    db: AsyncSession = Depends(get_db),
    actor: User = Depends(require_billing_admin),
):
    connector_cls = _connectors[provider]
    connector = connector_cls(db)
    sync_run = await connector.sync(period_start=body.period_start, period_end=body.period_end)
    await write_audit(
        db, action="sync", resource_type="sync_run",
        resource_id=sync_run.id, actor=actor,
        metadata={"provider": provider, "capability_status": sync_run.capability_status},
    )
    return sync_run
