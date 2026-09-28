import calendar
from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.plan import BillingInterval, Plan
from app.models.subscription import Subscription, SubscriptionStatus
from app.schemas.subscription import (
    SubscriptionCreate,
    SubscriptionUpdate,
)


ACTIVE_SUBSCRIPTION_STATUSES = (
    SubscriptionStatus.TRIALING,
    SubscriptionStatus.ACTIVE,
    SubscriptionStatus.PAST_DUE,
    SubscriptionStatus.UNPAID,
)


class PlanNotFoundError(Exception):
    pass


class PlanNotActiveError(Exception):
    pass


class ActiveSubscriptionAlreadyExistsError(Exception):
    pass


class SubscriptionNotFoundError(Exception):
    pass


def calculate_period_end(
    start: datetime,
    billing_interval: BillingInterval,
) -> datetime:
    if billing_interval == BillingInterval.YEARLY:
        target_year = start.year + 1
        target_month = start.month
    else:
        target_year = start.year
        target_month = start.month + 1

        if target_month == 13:
            target_year += 1
            target_month = 1

    last_day = calendar.monthrange(target_year, target_month)[1]
    target_day = min(start.day, last_day)

    return start.replace(
        year=target_year,
        month=target_month,
        day=target_day,
    )


async def get_subscription_by_id(
    db: AsyncSession,
    organization_id: UUID,
    subscription_id: UUID,
) -> Subscription | None:
    result = await db.execute(
        select(Subscription).where(
            Subscription.id == subscription_id,
            Subscription.organization_id == organization_id,
        )
    )

    return result.scalar_one_or_none()


async def get_current_subscription(
    db: AsyncSession,
    organization_id: UUID,
) -> Subscription | None:
    result = await db.execute(
        select(Subscription)
        .where(
            Subscription.organization_id == organization_id,
            Subscription.status.in_(ACTIVE_SUBSCRIPTION_STATUSES),
        )
        .order_by(Subscription.created_at.desc())
    )

    return result.scalars().first()


async def create_subscription(
    db: AsyncSession,
    organization_id: UUID,
    data: SubscriptionCreate,
) -> Subscription:
    existing_subscription = await get_current_subscription(
        db,
        organization_id,
    )

    if existing_subscription is not None:
        raise ActiveSubscriptionAlreadyExistsError(
            "The organization already has a current subscription."
        )

    result = await db.execute(
        select(Plan).where(
            Plan.id == data.plan_id,
        )
    )
    plan = result.scalar_one_or_none()

    if plan is None:
        raise PlanNotFoundError(
            f"Plan '{data.plan_id}' was not found."
        )

    if not plan.is_active:
        raise PlanNotActiveError(
            f"Plan '{plan.slug}' is not active."
        )

    period_start = datetime.now(timezone.utc)
    period_end = calculate_period_end(
        period_start,
        plan.billing_interval,
    )

    subscription = Subscription(
        organization_id=organization_id,
        plan_id=plan.id,
        status=SubscriptionStatus.TRIALING,
        current_period_start=period_start,
        current_period_end=period_end,
        cancel_at_period_end=False,
    )

    db.add(subscription)
    await db.commit()
    await db.refresh(subscription)

    return subscription


async def update_subscription(
    db: AsyncSession,
    organization_id: UUID,
    subscription: Subscription,
    data: SubscriptionUpdate,
) -> Subscription:
    if subscription.organization_id != organization_id:
        raise SubscriptionNotFoundError(
            "Subscription does not belong to the requested organization."
        )

    if subscription.status == SubscriptionStatus.CANCELED:
        raise SubscriptionNotFoundError(
            "A canceled subscription cannot be updated."
        )

    subscription.cancel_at_period_end = data.cancel_at_period_end

    await db.commit()
    await db.refresh(subscription)

    return subscription