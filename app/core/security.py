from datetime import timedelta, datetime, timezone
from typing import Any
from jose import JWTError, jwt
from pwdlib import PasswordHash
from app.core.config import settings

password_hash = PasswordHash.recommended()

def hash_password(password: str) -> str:
    return password_hash.hash(password)

def verify_password(password: str, hashed_password: str) -> bool:
    return password_hash.verify(password, hashed_password)

def create_access_token(subject: str) -> str:
    expires_at = datetime.now(timezone.utc) + timedelta(
        minutes=settings.access_token_expire_minutes
    )
    
    payload: dict[str, Any] = {
        "sub": subject,
        "type": "access",
        "expire": expires_at
    }
    
    return jwt.encode(
        payload,
        settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm
    )
    

def create_refresh_token(subject: str) -> str:
    expires_at = datetime.now(timezone.utc) + timedelta(
        days=settings.refresh_token_expire_days
    )
    
    payload: dict[str, Any] = {
            "sub": subject,
            "type": "refresh",
            "expire": expires_at
        }
        
    return jwt.encode(
            payload,
            settings.jwt_secret_key,
            algorithm=settings.jwt_algorithm
        )
    
def decode_token(token: str) -> dict[str, Any]:
    return jwt.encode(
        token,
        settings.jwt_secret_key,
        algorithm=[settings.jwt_algorithm]
    )