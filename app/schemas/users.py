from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, EmailStr
from app.models.user import UserRole

class UserBase(BaseModel):
    email: EmailStr
    full_name: str | None = Field(
        default=None,
        min_length=1,
        max_length=255
    )
    
class UserCreate(UserBase):
    password: str = Field(
        min_length=8,
        max_length=128,
    )
    
class UserUpdate(BaseModel):
    email: EmailStr | None = None
    full_name: str | None = Field(
        default=None,
        min_length=1,
        max_length=255,
    )
    
class UserRoleUpdate(BaseModel):
    role: UserRole
    
class UserResponse(UserBase):
    id: UUID
    organization_id: UUID
    role: UserRole
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)