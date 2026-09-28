from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.models.plan import BillingInterval

class PlanBase(BaseModel):
    name: str = Field(
        min_length=1,
        max_length=100,
    )
    slug: str = Field(
        min_length=1,
        max_length=100,
        pattern=r"^[a-z0-9]+(?:-[a-z0-9]+)*$",
    )
    description: str | None = Field(
        default=None,
        max_length=500,
    )
    price: int = Field(
        ge=0,
    )
    currency: str = Field(
        min_length=3,
        max_length=3,
    )
    billing_interval: BillingInterval
    features: dict[str, Any] = Field(default_factory=dict)
    
    @field_validator("currency")
    @classmethod
    def normalize_currency(cls, value: str) -> str:
        return value.upper()
    

class PlanCreate(PlanBase):
    pass

class PlanUpdate(BaseModel):
    name: str | None = Field(
        default=None,
        min_length=1,
        max_length=100,
    )
    slug: str | None = Field(
        default=None,
        min_length=1,
        max_length=100,
        pattern=r"^[a-z0-9]+(?:-[a-z0-9]+)*$",
    )
    description: str | None = Field(
        default=None,
        max_length=500,
    )
    price: int | None = Field(
        default=None,
        ge=0,
    )
    currency: str | None = Field(
        default=None,
        min_length=3,
        max_length=3,
    )
    billing_interval: BillingInterval | None = None
    features: dict[str, Any] | None = None
    is_active: bool | None = None
    
    @field_validator("currency")
    @classmethod
    def normalize_currency(cls, value: str | None) -> str | None:
        if value is None:
            return None
        return value.upper()
    
    
class PlanResponse(PlanBase):
    id: UUID
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)