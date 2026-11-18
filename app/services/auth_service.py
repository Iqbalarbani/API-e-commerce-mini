"""Service layer for registration and login."""

from fastapi import status

from app.core.exceptions import AppException
from app.core.security import create_access_token, hash_password, verify_password
from app.models.user import User
from app.repositories.user_repository import UserRepository
from app.schemas.auth import LoginRequest, RegisterRequest, TokenResponse


class AuthService:
    """Coordinates user registration and authentication."""

    def __init__(self, repository: UserRepository) -> None:
        self.repository = repository

    def register(self, payload: RegisterRequest) -> User:
        email = payload.email.lower()
        if self.repository.get_by_email(email) is not None:
            raise AppException(
                code="EMAIL_ALREADY_REGISTERED",
                message="Email sudah terdaftar.",
                status_code=status.HTTP_409_CONFLICT,
            )
        return self.repository.create(
            email=email,
            hashed_password=hash_password(payload.password),
            full_name=payload.full_name.strip(),
        )

    def login(self, payload: LoginRequest) -> TokenResponse:
        user = self.repository.get_by_email(payload.email.lower())
        if (
            user is None
            or not user.is_active
            or not verify_password(payload.password, user.hashed_password)
        ):
            raise AppException(
                code="INVALID_CREDENTIALS",
                message="Email atau password salah.",
                status_code=status.HTTP_401_UNAUTHORIZED,
            )
        token = create_access_token(subject=str(user.id), role=user.role.value)
        return TokenResponse(access_token=token)
