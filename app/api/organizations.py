from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_user
from app.core.database import get_db
from app.models.organization import Organization
from app.models.user import User
from app.schemas.organization import (
    OrganizationResponse,
    OrganizationUpdate,
)
from app.services.organization_service import (
    OrganizationSlugAlreadyExistsError,
    get_organization_by_id,
    update_organization,
)


router = APIRouter(
    prefix="/organizations",
    tags=["organizations"],
)


@router.get(
    "/me",
    response_model=OrganizationResponse,
)
async def get_my_organization(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> Organization:
    organization = await get_organization_by_id(
        db,
        current_user.organization_id,
    )

    if organization is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organization not found.",
        )

    return organization


@router.patch(
    "/me",
    response_model=OrganizationResponse,
)
async def update_my_organization(
    data: OrganizationUpdate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> Organization:
    organization = await get_organization_by_id(
        db,
        current_user.organization_id,
    )

    if organization is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organization not found.",
        )

    try:
        return await update_organization(
            db,
            organization,
            data,
        )
    except OrganizationSlugAlreadyExistsError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc