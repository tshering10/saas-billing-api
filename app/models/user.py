import uuid
from enum import Enum
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, Enum as SqlEnum, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import (
    Base,
    TimestampMixin,
    UUIDPrimaryKeyMixin
)

if TYPE_CHECKING:
    from app.models.organization import Organization
    
class UserRole(str, Enum):
    OWNER = "owner"
    ADMIN = "admin"
    MEMBER = "member"
    
class User(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    
    __tablename__ = "users"
    
    organization_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey(
            "organizations.id",
            ondelete="CASCADE"
        ),
        nullable=False,
        index=True,
    )
    
    email: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        unique=True,
        index=True,
    )
    
    password_hash: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    
    full_name: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )
    
    role: Mapped[UserRole] = mapped_column(
        SqlEnum(
            UserRole,
            name="user_role",
            values_callable=lambda enum_type: [
                role.value for role in enum_type
            ],
        ),
        nullable=False,
        default=UserRole.MEMBER,
    )
    
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
    )

    organization: Mapped["Organization"] = relationship(
        back_populates="users",
    )