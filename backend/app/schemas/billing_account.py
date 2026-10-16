import uuid
from datetime import datetime
from typing import Literal
from pydantic import BaseModel, ConfigDict, field_validator


ProviderType = Literal["openai", "anthropic"]
OwnershipType = Literal["geidi", "personal", "other_venture"]
CollectionMethod = Literal["api", "invoice", "csv"]
AuthorizationStatus = Literal["authorized", "pending", "revoked"]


class BillingAccountCreate(BaseModel):
    provider: ProviderType
    account_reference: str
    account_name: str
    ownership_type: OwnershipType
    collection_method: CollectionMethod
    default_currency: str = "USD"
    authorization_status: AuthorizationStatus = "pending"

    @field_validator("default_currency")
    @classmethod
    def currency_must_be_iso(cls, v: str) -> str:
        if len(v) != 3:
            raise ValueError("currency must be a 3-letter ISO code")
        return v.upper()


class BillingAccountUpdate(BaseModel):
    account_name: str | None = None
    ownership_type: OwnershipType | None = None
    collection_method: CollectionMethod | None = None
    authorization_status: AuthorizationStatus | None = None
    is_active: bool | None = None


class BillingAccountResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    provider: str
    account_reference: str
    account_name: str
    ownership_type: str
    collection_method: str
    default_currency: str
    authorization_status: str
    is_active: bool
    created_at: datetime
    updated_at: datetime
