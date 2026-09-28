from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import hash_password
from app.models.organization import Organization
from app.models.user import User, UserRole
from app.schemas.auth import RegisterRequest


class RegistrationOrganizationSlugAlreadyExistsError(Exception):
    pass


class RegistrationUserEmailAlreadyExistsError(Exception):
    pass


async def register_organization_owner(
    db: AsyncSession,
    data: RegisterRequest,
) -> tuple[Organization, User]:
    normalized_email = str(data.email).lower()

    existing_organization = await db.scalar(
        select(Organization).where(
            Organization.slug == data.organization_slug,
        )
    )

    if existing_organization is not None:
        raise RegistrationOrganizationSlugAlreadyExistsError(
            f"Organization slug '{data.organization_slug}' is already in use."
        )

    existing_user = await db.scalar(
        select(User).where(
            User.email == normalized_email,
        )
    )

    if existing_user is not None:
        raise RegistrationUserEmailAlreadyExistsError(
            f"User email '{normalized_email}' is already registered."
        )

    organization = Organization(
        name=data.organization_name,
        slug=data.organization_slug,
    )

    user = User(
        organization=organization,
        email=normalized_email,
        password_hash=hash_password(data.password),
        full_name=data.full_name,
        role=UserRole.OWNER,
        is_active=True,
    )

    db.add(organization)
    db.add(user)

    try:
        await db.commit()
    except Exception:
        await db.rollback()
        raise

    await db.refresh(organization)
    await db.refresh(user)

    return organization, user