import hashlib
import uuid
from datetime import date
from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.dialects.postgresql import insert
from app.models.billing_record import BillingRecord


def compute_file_hash(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def build_fallback_record_id(
    provider: str,
    account_id: uuid.UUID,
    invoice_number: str | None,
    period_start: date | None,
    period_end: date | None,
    amount: Decimal,
) -> str:
    """Fallback dedup key when provider supplies no external_record_id."""
    parts = [
        provider,
        str(account_id),
        invoice_number or "",
        str(period_start or ""),
        str(period_end or ""),
        f"{amount:.6f}",
    ]
    digest = hashlib.sha256("|".join(parts).encode()).hexdigest()
    return f"fallback:{digest}"


async def upsert_billing_record(
    db: AsyncSession,
    *,
    account_id: uuid.UUID,
    source_id: uuid.UUID | None,
    provider: str,
    external_record_id: str,
    expense_category: str,
    financial_basis: str,
    description: str | None,
    period_start: date | None,
    period_end: date | None,
    quantity: Decimal | None,
    amount: Decimal,
    currency: str,
    validation_status: str = "pending",
) -> uuid.UUID:
    """
    Idempotent upsert keyed on (account_id, external_record_id).
    Returns the record id (new or existing).
    """
    record_id = uuid.uuid4()
    stmt = (
        insert(BillingRecord)
        .values(
            id=record_id,
            account_id=account_id,
            source_id=source_id,
            provider=provider,
            external_record_id=external_record_id,
            expense_category=expense_category,
            financial_basis=financial_basis,
            description=description,
            period_start=period_start,
            period_end=period_end,
            quantity=quantity,
            amount=amount,
            currency=currency,
            validation_status=validation_status,
        )
        .on_conflict_do_update(
            constraint="uq_billing_record_dedup",
            set_={
                "source_id": source_id,
                "expense_category": expense_category,
                "financial_basis": financial_basis,
                "description": description,
                "period_start": period_start,
                "period_end": period_end,
                "quantity": quantity,
                "amount": amount,
                "currency": currency,
            },
        )
        .returning(BillingRecord.id)
    )
    result = await db.execute(stmt)
    return result.scalar_one()
