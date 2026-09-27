import uuid
from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING, Any

from sqlalchemy import (
    DateTime,
    Enum as SqlEnum,
    ForeignKey,
    Integer,
    JSON,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin
from app.models.payment_method import PaymentGateway

if TYPE_CHECKING:
    from app.models.invoice import Invoice
    from app.models.organization import Organization
    from app.models.payment_method import PaymentMethod


class PaymentTransactionStatus(str, Enum):
    PENDING = "pending"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    CANCELED = "canceled"


class PaymentTransaction(
    UUIDPrimaryKeyMixin,
    TimestampMixin,
    Base,
):
    __tablename__ = "payment_transactions"

    __table_args__ = (
        UniqueConstraint(
            "gateway",
            "external_reference",
            name="uq_payment_transaction_gateway_reference",
        ),
    )

    organization_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey(
            "organizations.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    invoice_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey(
            "invoices.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    payment_method_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey(
            "payment_methods.id",
            ondelete="SET NULL",
        ),
        nullable=True,
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

    external_reference: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        index=True,
    )

    amount: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    currency: Mapped[str] = mapped_column(
        String(3),
        nullable=False,
    )

    status: Mapped[PaymentTransactionStatus] = mapped_column(
        SqlEnum(
            PaymentTransactionStatus,
            name="payment_transaction_status",
            values_callable=lambda enum_cls: [
                item.value for item in enum_cls
            ],
        ),
        nullable=False,
        default=PaymentTransactionStatus.PENDING,
    )

    failure_reason: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
    )

    processed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    raw_payload: Mapped[dict[str, Any] | None] = mapped_column(
        JSON,
        nullable=True,
    )

    organization: Mapped["Organization"] = relationship(
        back_populates="payment_transactions",
    )

    invoice: Mapped["Invoice"] = relationship(
        back_populates="payment_transactions",
    )

    payment_method: Mapped["PaymentMethod | None"] = relationship()