import uuid
from datetime import datetime
from decimal import Decimal
from sqlalchemy import String, DateTime, ForeignKey, func, Numeric
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID
from app.database import Base


class Reconciliation(Base):
    __tablename__ = "ai_billing_reconciliations"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    billing_record_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("ai_billing_records.id", ondelete="CASCADE"), nullable=False, index=True)
    financial_reference: Mapped[str | None] = mapped_column(String(512), nullable=True)
    expected_amount: Mapped[Decimal] = mapped_column(Numeric(20, 6), nullable=False)
    observed_amount: Mapped[Decimal] = mapped_column(Numeric(20, 6), nullable=False)
    variance: Mapped[Decimal] = mapped_column(Numeric(20, 6), nullable=False)
    reconciliation_status: Mapped[str] = mapped_column(String(16), nullable=False, default="unmatched")
    reviewed_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
