from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import hash_password
from app.models.user import User, UserRole
from app.schemas.users import UserCreate, UserUpdate


class UserEmailAlreadyExistsError(Exception):
    pass


async def get_user_by_id(
    db: AsyncSession,
    organization_id: UUID,
    user_id: UUID,
) -> User | None:
    result = await db.execute(
        select(User).where(
            User.id == user_id,
            User.organization_id == organization_id,
        )
    )

    return result.scalar_one_or_none()


async def get_user_by_email(
    db: AsyncSession,
    email: str,
) -> User | None:
    result = await db.execute(
        select(User).where(
            User.email == email,
        )
    )

    return result.scalar_one_or_none()


async def list_users(
    db: AsyncSession,
    organization_id: UUID,
) -> list[User]:
    result = await db.execute(
        select(User)
        .where(
            User.organization_id == organization_id,
        )
        .order_by(User.created_at)
    )

    return list(result.scalars().all())


async def create_user(
    db: AsyncSession,
    organization_id: UUID,
    data: UserCreate,
    role: UserRole = UserRole.MEMBER,
) -> User:
    existing_user = await get_user_by_email(
        db,
        str(data.email),
    )

    if existing_user is not None:
        raise UserEmailAlreadyExistsError(
            f"User email '{data.email}' is already registered."
        )

    user = User(
        organization_id=organization_id,
        email=str(data.email).lower(),
        password_hash=hash_password(data.password),
        full_name=data.full_name,
        role=role,
    )

    db.add(user)
    await db.commit()
    await db.refresh(user)

    return user


async def update_user(
    db: AsyncSession,
    organization_id: UUID,
    user: User,
    data: UserUpdate,
) -> User:
    update_data = data.model_dump(exclude_unset=True)

    if "email" in update_data:
        new_email = str(update_data["email"]).lower()

        existing_user = await get_user_by_email(
            db,
            new_email,
        )

        if (
            existing_user is not None
            and existing_user.id != user.id
        ):
            raise UserEmailAlreadyExistsError(
                f"User email '{new_email}' is already registered."
            )

        user.email = new_email

    if "full_name" in update_data:
        user.full_name = update_data["full_name"]

    if user.organization_id != organization_id:
        raise ValueError(
            "User does not belong to the requested organization."
        )

    await db.commit()
    await db.refresh(user)

    return user