import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.audit_event import AuditEvent
from app.models.user import User


async def write_audit(
    db: AsyncSession,
    *,
    action: str,
    resource_type: str,
    resource_id: uuid.UUID | None = None,
    outcome: str = "success",
    metadata: dict | None = None,
    actor: User | None = None,
) -> None:
    event = AuditEvent(
        principal_id=actor.id if actor else None,
        principal_email=actor.email if actor else None,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        outcome=outcome,
        metadata_=metadata,
    )
    db.add(event)
