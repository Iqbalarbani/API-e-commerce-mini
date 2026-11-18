"""Unit tests for AuthService using a fake user repository."""

import uuid
from datetime import UTC, datetime

import pytest

from app.core.exceptions import AppException
from app.core.security import verify_password
from app.models.user import User, UserRole
from app.schemas.auth import LoginRequest, RegisterRequest
from app.services.auth_service import AuthService


class FakeUserRepository:
    """In-memory stand-in for UserRepository."""

    def __init__(self) -> None:
        self.users: dict[str, User] = {}

    def get_by_email(self, email: str) -> User | None:
        return self.users.get(email)

    def create(
        self, *, email: str, hashed_password: str, full_name: str, role=UserRole.CUSTOMER
    ) -> User:
        user = User(
            id=uuid.uuid4(),
            email=email,
            hashed_password=hashed_password,
            full_name=full_name,
            role=role,
            is_active=True,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )
        self.users[email] = user
        return user


def test_register_hashes_password_and_persists() -> None:
    repo = FakeUserRepository()
    service = AuthService(repository=repo)

    user = service.register(
        RegisterRequest(email="new@example.com", password="Password123", full_name="New")
    )

    assert user.email == "new@example.com"
    assert user.hashed_password != "Password123"
    assert verify_password("Password123", user.hashed_password)


def test_register_duplicate_email_fails() -> None:
    repo = FakeUserRepository()
    service = AuthService(repository=repo)
    payload = RegisterRequest(email="dup@example.com", password="Password123", full_name="Dup")
    service.register(payload)

    with pytest.raises(AppException) as exc:
        service.register(payload)

    assert exc.value.code == "EMAIL_ALREADY_REGISTERED"
    assert exc.value.status_code == 409


def test_login_success_returns_token() -> None:
    repo = FakeUserRepository()
    service = AuthService(repository=repo)
    service.register(
        RegisterRequest(email="login@example.com", password="Password123", full_name="L")
    )

    token = service.login(LoginRequest(email="login@example.com", password="Password123"))

    assert token.access_token
    assert token.token_type == "bearer"


def test_login_wrong_password_fails() -> None:
    repo = FakeUserRepository()
    service = AuthService(repository=repo)
    service.register(
        RegisterRequest(email="bad@example.com", password="Password123", full_name="B")
    )

    with pytest.raises(AppException) as exc:
        service.login(LoginRequest(email="bad@example.com", password="WrongPassword"))

    assert exc.value.code == "INVALID_CREDENTIALS"
    assert exc.value.status_code == 401


def test_login_unknown_email_fails() -> None:
    service = AuthService(repository=FakeUserRepository())

    with pytest.raises(AppException) as exc:
        service.login(LoginRequest(email="ghost@example.com", password="Password123"))

    assert exc.value.code == "INVALID_CREDENTIALS"
