import uuid
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.database import get_db
from app.models.billing_record import BillingRecord
from app.models.billing_account import BillingAccount
from app.models.reconciliation import Reconciliation
from app.models.user import User
from app.auth.dependencies import require_viewer
from app.schemas.billing_record import BillingRecordResponse, BillingRecordListResponse

router = APIRouter()


@router.get("", response_model=BillingRecordListResponse)
async def list_records(
    provider: str | None = Query(None),
    account_id: uuid.UUID | None = Query(None),
    period: str | None = Query(None, description="YYYY-MM"),
    expense_category: str | None = Query(None),
    financial_basis: str | None = Query(None),
    ownership_type: str | None = Query(None),
    validation_status: str | None = Query(None),
    reconciliation_status: str | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_viewer),
):
    query = (
        select(BillingRecord)
        .join(BillingAccount, BillingRecord.account_id == BillingAccount.id)
    )

    if ownership_type:
        query = query.where(BillingAccount.ownership_type == ownership_type)
    else:
        query = query.where(BillingAccount.ownership_type == "geidi")

    if provider:
        query = query.where(BillingRecord.provider == provider)
    if account_id:
        query = query.where(BillingRecord.account_id == account_id)
    if period:
        try:
            year, month = int(period[:4]), int(period[5:7])
            from datetime import date
            import calendar
            start = date(year, month, 1)
            end = date(year, month, calendar.monthrange(year, month)[1])
            query = query.where(BillingRecord.period_start >= start, BillingRecord.period_start <= end)
        except (ValueError, IndexError):
            pass
    if expense_category:
        query = query.where(BillingRecord.expense_category == expense_category)
    if financial_basis:
        query = query.where(BillingRecord.financial_basis == financial_basis)
    if validation_status:
        query = query.where(BillingRecord.validation_status == validation_status)
    if reconciliation_status:
        query = query.where(
            select(Reconciliation.id)
            .where(
                Reconciliation.billing_record_id == BillingRecord.id,
                Reconciliation.reconciliation_status == reconciliation_status,
            )
            .exists()
        )

    count_result = await db.execute(select(func.count()).select_from(query.subquery()))
    total = count_result.scalar_one()

    query = query.order_by(BillingRecord.period_start.desc(), BillingRecord.id).offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    items = result.scalars().all()

    return BillingRecordListResponse(total=total, page=page, page_size=page_size, items=items)
