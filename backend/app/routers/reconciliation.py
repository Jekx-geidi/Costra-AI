import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.models.reconciliation import Reconciliation
from app.models.billing_record import BillingRecord
from app.models.user import User
from app.auth.dependencies import require_finance_reviewer
from app.schemas.reconciliation import ReconciliationCreate, ReconciliationReviewRequest, ReconciliationResponse
from app.utils.audit import write_audit
from datetime import datetime, timezone

router = APIRouter()


def _response(rec: Reconciliation, record_validation_status: str | None) -> ReconciliationResponse:
    return ReconciliationResponse.model_validate(rec).model_copy(
        update={"record_validation_status": record_validation_status}
    )


@router.get("", response_model=list[ReconciliationResponse])
async def list_reconciliation(
    reconciliation_status: str | None = None,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_finance_reviewer),
):
    query = select(Reconciliation, BillingRecord.validation_status).join(
        BillingRecord, BillingRecord.id == Reconciliation.billing_record_id
    )
    if reconciliation_status:
        query = query.where(Reconciliation.reconciliation_status == reconciliation_status)
    result = await db.execute(query.order_by(Reconciliation.created_at.desc()))
    return [_response(rec, validation_status) for rec, validation_status in result.all()]


@router.post("", response_model=ReconciliationResponse, status_code=status.HTTP_201_CREATED)
async def create_reconciliation(
    body: ReconciliationCreate,
    db: AsyncSession = Depends(get_db),
    actor: User = Depends(require_finance_reviewer),
):
    record = (await db.execute(
        select(BillingRecord).where(BillingRecord.id == body.billing_record_id)
    )).scalar_one_or_none()
    if not record:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Billing record not found")

    variance = body.expected_amount - body.observed_amount
    rec_status = "matched" if variance == 0 else "partial" if abs(variance) < body.expected_amount * 1 else "unmatched"
    rec = Reconciliation(
        billing_record_id=body.billing_record_id,
        financial_reference=body.financial_reference,
        expected_amount=body.expected_amount,
        observed_amount=body.observed_amount,
        variance=variance,
        reconciliation_status=rec_status,
    )
    db.add(rec)
    await db.flush()
    await write_audit(db, action="create", resource_type="reconciliation", resource_id=rec.id, actor=actor)
    return _response(rec, record.validation_status)


@router.post("/{billing_record_id}/review", response_model=ReconciliationResponse)
async def review_record(
    billing_record_id: uuid.UUID,
    body: ReconciliationReviewRequest,
    db: AsyncSession = Depends(get_db),
    actor: User = Depends(require_finance_reviewer),
):
    # A record can be reconciled more than once; the review applies to the latest attempt.
    rec_result = await db.execute(
        select(Reconciliation)
        .where(Reconciliation.billing_record_id == billing_record_id)
        .order_by(Reconciliation.created_at.desc())
        .limit(1)
    )
    rec = rec_result.scalar_one_or_none()
    if not rec:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Reconciliation record not found")

    br_result = await db.execute(select(BillingRecord).where(BillingRecord.id == billing_record_id))
    br = br_result.scalar_one_or_none()

    if body.action == "approve" and br:
        br.validation_status = "verified"
    elif body.action == "dispute" and br:
        br.validation_status = "disputed"

    rec.reviewed_by = actor.id
    rec.reviewed_at = datetime.now(timezone.utc)

    await write_audit(
        db, action=body.action, resource_type="reconciliation",
        resource_id=rec.id, actor=actor,
        metadata={"action": body.action, "notes": body.notes},
    )
    return _response(rec, br.validation_status if br else None)
