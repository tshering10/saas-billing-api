from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.organization import Organization
from app.schemas.organization import (
    OrganizationCreate,
    OrganizationUpdate,
)


class OrganizationSlugAlreadyExistsError(Exception):
    pass


class OrganizationNotFoundError(Exception):
    pass


async def get_organization_by_id(
    db: AsyncSession,
    organization_id: UUID,
) -> Organization | None:
    result = await db.execute(
        select(Organization).where(
            Organization.id == organization_id,
        )
    )

    return result.scalar_one_or_none()


async def get_organization_by_slug(
    db: AsyncSession,
    slug: str,
) -> Organization | None:
    result = await db.execute(
        select(Organization).where(
            Organization.slug == slug,
        )
    )

    return result.scalar_one_or_none()


async def create_organization(
    db: AsyncSession,
    data: OrganizationCreate,
) -> Organization:
    existing_organization = await get_organization_by_slug(
        db,
        data.slug,
    )

    if existing_organization is not None:
        raise OrganizationSlugAlreadyExistsError(
            f"Organization slug '{data.slug}' is already in use."
        )

    organization = Organization(
        name=data.name,
        slug=data.slug,
    )

    db.add(organization)
    await db.commit()
    await db.refresh(organization)

    return organization


async def update_organization(
    db: AsyncSession,
    organization: Organization,
    data: OrganizationUpdate,
) -> Organization:
    #partial update
    update_data = data.model_dump(exclude_unset=True)

    if "slug" in update_data:
        existing_organization = await get_organization_by_slug(
            db,
            update_data["slug"],
        )

        if (
            existing_organization is not None
            and existing_organization.id != organization.id
        ):
            raise OrganizationSlugAlreadyExistsError(
                f"Organization slug '{update_data['slug']}' is already in use."
            )

    for field, value in update_data.items():
        setattr(organization, field, value)

    await db.commit()
    await db.refresh(organization)

    return organization