from enum import Enum
from typing import Any, TYPE_CHECKING

from sqlalchemy import Enum as SqlEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import Integer, String
from sqlalchemy.dialects.postgresql import JSONB

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.subscription import Subscription
    
class BillingInterval(str, Enum):
    MONTHLY = "monthly"
    YEARLY = "yearly"
    
class Plan(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "plans"
    
    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False
    )
    
    slug: Mapped[str | None] = mapped_column(
        String(255),
        nullable=False
    )
    
    price: Mapped[int] = mapped_column(
        Integer,
        nullable=False
    )
    
    currency: Mapped[str] = mapped_column(
        String(3),
        nullable=False
    )
    
    billing_interval: Mapped[BillingInterval] = mapped_column(
        SqlEnum(
            BillingInterval,
            name="billing_interval",
            values_callable=lambda enum_cls: [
                item.value for item in enum_cls
            ],
        ),
        nullable=False
    )
    
    subscriptions: Mapped[list["Subscription"]] = relationship(
    back_populates="plan",
    )
    
    features: Mapped[dict[str, Any]] = mapped_column(
        JSONB,
        nullable=False,
        default=dict,
    )

    is_active: Mapped[bool] = mapped_column(
        nullable=False,
        default=True,
    )