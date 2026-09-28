from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_user, require_roles
from app.core.database import get_db
from app.models.plan import Plan
from app.models.user import User, UserRole
from app.schemas.plan import PlanCreate, PlanResponse, PlanUpdate
from app.services.plan_service import (
    PlanSlugAlreadyExistsError,
    create_plan,
    get_plan_by_id,
    list_plans,
    update_plan,
)


router = APIRouter(
    prefix="/plans",
    tags=["plans"],
)


Administrator = Annotated[
    User,
    Depends(require_roles(UserRole.OWNER, UserRole.ADMIN)),
]


@router.get(
    "",
    response_model=list[PlanResponse],
)
async def get_plans(
    db: Annotated[AsyncSession, Depends(get_db)],
) -> list[Plan]:
    return await list_plans(db)


@router.get(
    "/{plan_id}",
    response_model=PlanResponse,
)
async def get_plan(
    plan_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> Plan:
    plan = await get_plan_by_id(db, plan_id)

    if plan is None or not plan.is_active:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Plan not found.",
        )

    return plan


@router.post(
    "",
    response_model=PlanResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_new_plan(
    data: PlanCreate,
    current_user: Administrator,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> Plan:
    try:
        return await create_plan(db, data)
    except PlanSlugAlreadyExistsError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc


@router.patch(
    "/{plan_id}",
    response_model=PlanResponse,
)
async def update_existing_plan(
    plan_id: UUID,
    data: PlanUpdate,
    current_user: Administrator,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> Plan:
    plan = await get_plan_by_id(db, plan_id)

    if plan is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Plan not found.",
        )

    try:
        return await update_plan(db, plan, data)
    except PlanSlugAlreadyExistsError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc