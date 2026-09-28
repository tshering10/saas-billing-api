from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_user, require_roles
from app.core.database import get_db
from app.models.user import User, UserRole
from app.schemas.users import UserCreate, UserResponse, UserUpdate
from app.services.user_service import (
    UserEmailAlreadyExistsError,
    create_user,
    get_user_by_id,
    list_users,
    update_user,
)


router = APIRouter(
    prefix="/users",
    tags=["users"],
)


CurrentUser = Annotated[User, Depends(get_current_user)]
BillingAdministrator = Annotated[
    User,
    Depends(require_roles(UserRole.OWNER, UserRole.ADMIN)),
]


@router.get("", response_model=list[UserResponse],
)
async def get_users(
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> list[User]:
    return await list_users(
        db,
        current_user.organization_id,
    )


@router.post("",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_organization_user(
    data: UserCreate,
    current_user: BillingAdministrator,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> User:
    try:
        return await create_user(
            db,
            current_user.organization_id,
            data,
        )
    except UserEmailAlreadyExistsError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc


@router.get(
    "/{user_id}",
    response_model=UserResponse,
)
async def get_organization_user(
    user_id: UUID,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> User:
    user = await get_user_by_id(
        db,
        current_user.organization_id,
        user_id,
    )

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found.",
        )

    return user


@router.patch(
    "/{user_id}",
    response_model=UserResponse,
)
async def update_organization_user(
    user_id: UUID,
    data: UserUpdate,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> User:
    user = await get_user_by_id(
        db,
        current_user.organization_id,
        user_id,
    )

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found.",
        )

    try:
        return await update_user(
            db,
            current_user.organization_id,
            user,
            data,
        )
    except UserEmailAlreadyExistsError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc