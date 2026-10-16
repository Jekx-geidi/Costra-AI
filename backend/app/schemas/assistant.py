import uuid
from datetime import date
from decimal import Decimal
from typing import Literal
from pydantic import BaseModel, Field, field_serializer


class ChatMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str = Field(min_length=1, max_length=4000)


class ChatRequest(BaseModel):
    messages: list[ChatMessage] = Field(min_length=1, max_length=40)


class ChatResponse(BaseModel):
    reply: str


class InvoiceLineItem(BaseModel):
    description: str | None = Field(default=None, max_length=500)
    expense_category: Literal["subscription", "seat", "api", "credit", "adjustment"]
    financial_basis: Literal["invoiced", "usage", "payment", "credit"]
    amount: Decimal
    currency: str = Field(min_length=3, max_length=3)
    period_start: date | None = None
    period_end: date | None = None

    @field_serializer("amount", when_used="json")
    def serialize_amount(self, v: Decimal) -> str:
        return f"{v:.6f}"


class AccountOption(BaseModel):
    id: uuid.UUID
    name: str
    provider: str


class InvoiceDraftResponse(BaseModel):
    draft_id: uuid.UUID
    filename: str | None
    is_invoice: bool
    vendor_name: str | None
    provider: str
    invoice_number: str | None
    currency: str
    period_start: date | None
    period_end: date | None
    total: Decimal | None
    items: list[InvoiceLineItem]
    warnings: list[str]
    suggested_account_id: uuid.UUID | None
    accounts: list[AccountOption]

    @field_serializer("total", when_used="json")
    def serialize_total(self, v: Decimal | None) -> str | None:
        return None if v is None else f"{v:.6f}"


class InvoiceConfirmRequest(BaseModel):
    account_id: uuid.UUID
    invoice_number: str | None = Field(default=None, max_length=128)
    items: list[InvoiceLineItem] = Field(min_length=1, max_length=200)


class InvoiceConfirmResponse(BaseModel):
    source_id: uuid.UUID
    account_name: str
    records_imported: int
    total: Decimal
    currency: str

    @field_serializer("total", when_used="json")
    def serialize_total(self, v: Decimal) -> str:
        return f"{v:.6f}"
