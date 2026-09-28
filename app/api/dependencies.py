from collections.abc import Callable
from typing import Annotated
from uuid import UUID

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import decode_token
from app.models.user import User, UserRole
from app.services.user_service import get_user_by_email


oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="/api/auth/login",
)


async def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials.",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = decode_token(token)
    except JWTError:
        raise credentials_exception from None

    subject = payload.get("sub")
    token_type = payload.get("type")

    if subject is None or token_type != "access":
        raise credentials_exception

    try:
        user_id = UUID(subject)
    except (TypeError, ValueError):
        raise credentials_exception from None

    result = await db.get(User, user_id)

    if result is None or not result.is_active:
        raise credentials_exception

    return result

def require_roles(
    *allowed_roles: UserRole,
) -> Callable:
    async def role_dependency(
        current_user: Annotated[
            User,
            Depends(get_current_user),
        ],
    ) -> User:
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to perform this action.",
            )

        return current_user

    return role_dependency