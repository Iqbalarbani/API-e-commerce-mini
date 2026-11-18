"""Shared FastAPI dependency injection definitions."""

import uuid
from typing import Annotated

import jwt
from fastapi import Depends, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.exceptions import AppException
from app.core.security import decode_access_token
from app.models.user import User, UserRole
from app.repositories.user_repository import UserRepository

DbSession = Annotated[Session, Depends(get_db)]

bearer_scheme = HTTPBearer(auto_error=False)


def _unauthorized(message: str = "Autentikasi diperlukan.") -> AppException:
    return AppException(
        code="UNAUTHORIZED",
        message=message,
        status_code=status.HTTP_401_UNAUTHORIZED,
    )


def get_current_user(
    db: DbSession,
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)],
) -> User:
    """Resolve the authenticated user from the Bearer token."""
    if credentials is None:
        raise _unauthorized()
    try:
        payload = decode_access_token(credentials.credentials)
        user_id = uuid.UUID(payload["sub"])
    except (jwt.PyJWTError, KeyError, ValueError) as exc:
        raise _unauthorized("Token tidak valid atau kedaluwarsa.") from exc

    user = UserRepository(db).get_by_id(user_id)
    if user is None or not user.is_active:
        raise _unauthorized("User tidak ditemukan atau tidak aktif.")
    return user


CurrentUser = Annotated[User, Depends(get_current_user)]


def require_admin(current_user: CurrentUser) -> User:
    """Allow only users with the admin role."""
    if current_user.role != UserRole.ADMIN:
        raise AppException(
            code="FORBIDDEN",
            message="Akses ditolak: hanya admin.",
            status_code=status.HTTP_403_FORBIDDEN,
        )
    return current_user


AdminUser = Annotated[User, Depends(require_admin)]
