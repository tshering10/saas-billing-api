from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.plan import Plan
from app.schemas.plan import PlanCreate, PlanUpdate


class PlanSlugAlreadyExistsError(Exception):
    pass


async def get_plan_by_id(
    db: AsyncSession,
    plan_id: UUID,
) -> Plan | None:
    result = await db.execute(
        select(Plan).where(
            Plan.id == plan_id,
        )
    )

    return result.scalar_one_or_none()


async def get_plan_by_slug(
    db: AsyncSession,
    slug: str,
) -> Plan | None:
    result = await db.execute(
        select(Plan).where(
            Plan.slug == slug,
        )
    )

    return result.scalar_one_or_none()


async def list_plans(
    db: AsyncSession,
    active_only: bool = True,
) -> list[Plan]:
    query = select(Plan).order_by(Plan.name)

    if active_only:
        query = query.where(
            Plan.is_active.is_(True),
        )

    result = await db.execute(query)

    return list(result.scalars().all())


async def create_plan(
    db: AsyncSession,
    data: PlanCreate,
) -> Plan:
    existing_plan = await get_plan_by_slug(
        db,
        data.slug,
    )

    if existing_plan is not None:
        raise PlanSlugAlreadyExistsError(
            f"Plan slug '{data.slug}' is already in use."
        )

    plan = Plan(
        name=data.name,
        slug=data.slug,
        description=data.description,
        price=data.price,
        currency=data.currency,
        billing_interval=data.billing_interval,
        features=data.features,
    )

    db.add(plan)
    await db.commit()
    await db.refresh(plan)

    return plan


async def update_plan(
    db: AsyncSession,
    plan: Plan,
    data: PlanUpdate,
) -> Plan:
    update_data = data.model_dump(exclude_unset=True)

    if "slug" in update_data:
        existing_plan = await get_plan_by_slug(
            db,
            update_data["slug"],
        )

        if (
            existing_plan is not None
            and existing_plan.id != plan.id
        ):
            raise PlanSlugAlreadyExistsError(
                f"Plan slug '{update_data['slug']}' is already in use."
            )

    for field, value in update_data.items():
        setattr(plan, field, value)

    await db.commit()
    await db.refresh(plan)

    return plan