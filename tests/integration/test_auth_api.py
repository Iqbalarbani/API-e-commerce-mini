"""Integration tests for auth endpoints."""

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models import UserRole
from tests.conftest import auth_headers, make_user


def test_register_then_login(client: TestClient) -> None:
    payload = {
        "email": "integration@example.com",
        "password": "Password123",
        "full_name": "Integration User",
    }
    resp = client.post("/api/v1/auth/register", json=payload)
    assert resp.status_code == 201
    assert resp.json()["email"] == "integration@example.com"

    login = client.post(
        "/api/v1/auth/login",
        json={"email": payload["email"], "password": payload["password"]},
    )
    assert login.status_code == 200
    assert login.json()["access_token"]


def test_register_short_password_rejected(client: TestClient) -> None:
    resp = client.post(
        "/api/v1/auth/register",
        json={"email": "short@example.com", "password": "1234567", "full_name": "S"},
    )
    assert resp.status_code == 422
    assert resp.json()["error"]["code"] == "VALIDATION_ERROR"


def test_login_wrong_password_fails(client: TestClient, db_session: Session) -> None:
    make_user(db_session, email="known@example.com", password="Password123")

    resp = client.post(
        "/api/v1/auth/login",
        json={"email": "known@example.com", "password": "NopeNope123"},
    )

    assert resp.status_code == 401
    assert resp.json()["error"]["code"] == "INVALID_CREDENTIALS"


def test_protected_endpoint_without_token_401(client: TestClient) -> None:
    resp = client.get("/api/v1/auth/me")
    assert resp.status_code == 401


def test_protected_endpoint_with_token_ok(client: TestClient, db_session: Session) -> None:
    user = make_user(db_session, email="me@example.com", password="Password123")
    headers = auth_headers(client, "me@example.com", "Password123")

    resp = client.get("/api/v1/auth/me", headers=headers)

    assert resp.status_code == 200
    assert resp.json()["id"] == str(user.id)


def test_admin_endpoint_forbidden_for_customer(client: TestClient, db_session: Session) -> None:
    make_user(db_session, email="cust@example.com", password="Password123")
    headers = auth_headers(client, "cust@example.com", "Password123")

    resp = client.get("/api/v1/auth/admin-check", headers=headers)

    assert resp.status_code == 403
    assert resp.json()["error"]["code"] == "FORBIDDEN"


def test_admin_endpoint_allowed_for_admin(client: TestClient, db_session: Session) -> None:
    make_user(
        db_session, email="admin@example.com", password="Password123", role=UserRole.ADMIN
    )
    headers = auth_headers(client, "admin@example.com", "Password123")

    resp = client.get("/api/v1/auth/admin-check", headers=headers)

    assert resp.status_code == 200
