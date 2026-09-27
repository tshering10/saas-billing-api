import uuid
from typing import TYPE_CHECKING

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import(
    Base,
    TimestampMixin, UUIDPrimaryKeyMixin
)

if TYPE_CHECKING:
    from app.models.subscription import Subscription
    from app.models.user import User

class Organization(
    UUIDPrimaryKeyMixin,
    TimestampMixin,
    Base
):
    __tablename__ = "organizations"
    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False
    )
    
    slug: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        unique=True,
        index=True,
    )
    
    
    users: Mapped[list["User"]] = relationship(
        back_populates="organization",
        cascade="all, delete-orphan",
    )
    
    subscriptions: Mapped[list["Subscription"]] = relationship(
    back_populates="organization",
    cascade="all, delete-orphan",
)