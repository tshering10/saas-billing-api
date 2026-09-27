import uuid
from enum import Enum
from typing import TYPE_CHECKING, Any

from sqlalchemy import Boolean, Enum as SqlEnum, ForeignKey, JSON, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.organization import Organization


class PaymentGateway(str, Enum):
    STRIPE = "stripe"
    ESEWA = "esewa"


class PaymentMethodType(str, Enum):
    CARD = "card"
    ESEWA = "esewa"


class PaymentMethod(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "payment_methods"

    organization_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey(
            "organizations.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    gateway: Mapped[PaymentGateway] = mapped_column(
        SqlEnum(
            PaymentGateway,
            name="payment_gateway",
            values_callable=lambda enum_cls: [
                item.value for item in enum_cls
            ],
        ),
        nullable=False,
    )

    method_type: Mapped[PaymentMethodType] = mapped_column(
        SqlEnum(
            PaymentMethodType,
            name="payment_method_type",
            values_callable=lambda enum_cls: [
                item.value for item in enum_cls
            ],
        ),
        nullable=False,
    )

    external_reference: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    display_label: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    is_default: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
    )

    metadata_: Mapped[dict[str, Any]] = mapped_column(
        "metadata",
        JSON,
        nullable=False,
        default=dict,
    )

    organization: Mapped["Organization"] = relationship(
        back_populates="payment_methods",
    )