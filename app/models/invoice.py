import uuid
from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Enum as SqlEnum, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.transaction import PaymentTransaction
    from app.models.organization import Organization
    from app.models.subscription import Subscription


class InvoiceStatus(str, Enum):
    DRAFT = "draft"
    OPEN = "open"
    PAID = "paid"
    VOID = "void"
    UNCOLLECTIBLE = "uncollectible"


class Invoice(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "invoices"

    organization_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey(
            "organizations.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    subscription_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey(
            "subscriptions.id",
            ondelete="RESTRICT",
        ),
        nullable=False,
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

    status: Mapped[InvoiceStatus] = mapped_column(
        SqlEnum(
            InvoiceStatus,
            name="invoice_status",
            values_callable=lambda enum_cls: [
                item.value for item in enum_cls
            ],
        ),
        nullable=False,
        default=InvoiceStatus.DRAFT,
    )

    issued_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )

    due_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    paid_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    external_invoice_id: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        index=True,
    )

    organization: Mapped["Organization"] = relationship(
        back_populates="invoices",
    )

    subscription: Mapped["Subscription"] = relationship(
        back_populates="invoices",
    )
    
    payment_transactions: Mapped[list["PaymentTransaction"]] = relationship(
        back_populates="invoice",
        cascade="all, delete-orphan",
    )