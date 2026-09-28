from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_user, require_roles
from app.core.database import get_db
from app.models.subscription import Subscription
from app.models.user import User, UserRole
from app.schemas.subscription import (
    SubscriptionCreate,
    SubscriptionResponse,
    SubscriptionUpdate,
)
from app.services.subs_service import (
    ActiveSubscriptionAlreadyExistsError,
    PlanNotActiveError,
    PlanNotFoundError,
    SubscriptionNotFoundError,
    create_subscription,
    get_current_subscription,
    get_subscription_by_id,
    update_subscription,
)


router = APIRouter(
    prefix="/subscriptions",
    tags=["subscriptions"],
)


CurrentUser = Annotated[
    User,
    Depends(get_current_user),
]

BillingAdministrator = Annotated[
    User,
    Depends(require_roles(UserRole.OWNER, UserRole.ADMIN)),
]


@router.get("/current", response_model=SubscriptionResponse,
)
async def get_my_current_subscription(
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> Subscription:
    subscription = await get_current_subscription(
        db,
        current_user.organization_id,
    )

    if subscription is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No current subscription found.",
        )

    return subscription


@router.post("", response_model=SubscriptionResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_organization_subscription(
    data: SubscriptionCreate,
    current_user: BillingAdministrator,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> Subscription:
    try:
        return await create_subscription(
            db,
            current_user.organization_id,
            data,
        )
    except PlanNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
    except PlanNotActiveError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc
    except ActiveSubscriptionAlreadyExistsError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc


@router.patch(
    "/{subscription_id}",
    response_model=SubscriptionResponse,
)
async def update_organization_subscription(
    subscription_id: UUID,
    data: SubscriptionUpdate,
    current_user: BillingAdministrator,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> Subscription:
    subscription = await get_subscription_by_id(
        db,
        current_user.organization_id,
        subscription_id,
    )

    if subscription is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Subscription not found.",
        )

    try:
        return await update_subscription(
            db,
            current_user.organization_id,
            subscription,
            data,
        )
    except SubscriptionNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc