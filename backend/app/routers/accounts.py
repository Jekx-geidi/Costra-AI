import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.models.billing_account import BillingAccount
from app.models.user import User
from app.auth.dependencies import require_viewer, require_billing_admin
from app.schemas.billing_account import BillingAccountCreate, BillingAccountUpdate, BillingAccountResponse
from app.utils.audit import write_audit

router = APIRouter()


@router.get("", response_model=list[BillingAccountResponse])
async def list_accounts(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_viewer),
):
    result = await db.execute(select(BillingAccount).order_by(BillingAccount.created_at.desc()))
    return result.scalars().all()


@router.post("", response_model=BillingAccountResponse, status_code=status.HTTP_201_CREATED)
async def create_account(
    body: BillingAccountCreate,
    db: AsyncSession = Depends(get_db),
    actor: User = Depends(require_billing_admin),
):
    account = BillingAccount(**body.model_dump())
    db.add(account)
    await db.flush()
    await write_audit(db, action="create", resource_type="billing_account", resource_id=account.id, actor=actor)
    return account


@router.patch("/{account_id}", response_model=BillingAccountResponse)
async def update_account(
    account_id: uuid.UUID,
    body: BillingAccountUpdate,
    db: AsyncSession = Depends(get_db),
    actor: User = Depends(require_billing_admin),
):
    result = await db.execute(select(BillingAccount).where(BillingAccount.id == account_id))
    account = result.scalar_one_or_none()
    if not account:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Account not found")
    for field, value in body.model_dump(exclude_none=True).items():
        setattr(account, field, value)
    await write_audit(db, action="update", resource_type="billing_account", resource_id=account.id, actor=actor)
    return account
