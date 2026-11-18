"""Shared pytest fixtures.

Integration tests need a real PostgreSQL database (TEST_DATABASE_URL). Unit
tests use fake repositories and never touch the database. The database is only
created/truncated lazily when a test requests the ``db_session`` or ``client``
fixture, so unit tests can run without any database available.
"""

import os
import uuid
from collections.abc import Generator

import pytest

# Redirect the application engine to the test database BEFORE importing app.
_TEST_URL = os.getenv(
    "TEST_DATABASE_URL",
    "postgresql+psycopg://minishop:minishop_secret@localhost:5432/minishop_test_db",
)
os.environ["DATABASE_URL"] = _TEST_URL

from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy import create_engine, text  # noqa: E402
from sqlalchemy.orm import Session, sessionmaker  # noqa: E402

from app.core.database import Base, get_db  # noqa: E402
from app.core.rate_limit import limiter  # noqa: E402
from app.core.security import hash_password  # noqa: E402
from app.main import app  # noqa: E402
from app.models import Category, Product, User, UserRole  # noqa: E402

# Disable rate limiting during tests; it is covered separately by config.
limiter.enabled = False

engine = create_engine(
    _TEST_URL,
    pool_pre_ping=True,
    future=True,
    connect_args={"connect_timeout": 3},
)
TestingSessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


def _database_reachable() -> bool:
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return True
    except Exception:  # noqa: BLE001 - any connection failure means unavailable
        return False


@pytest.fixture(scope="session")
def _database() -> Generator[None, None, None]:
    """Create the schema once for the whole test session (integration only)."""
    if not _database_reachable():
        pytest.skip(
            f"PostgreSQL test database not reachable at {_TEST_URL!r}; "
            "skipping integration tests."
        )
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def db_session(_database: None) -> Generator[Session, None, None]:
    """Provide a session bound to the test database, cleaned between tests."""
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        with engine.begin() as conn:
            conn.execute(
                text(
                    "TRUNCATE order_items, orders, cart_items, carts, products, "
                    "categories, users RESTART IDENTITY CASCADE"
                )
            )


@pytest.fixture
def client(db_session: Session) -> Generator[TestClient, None, None]:
    """FastAPI TestClient with the DB dependency overridden to the test session."""

    def _override_get_db() -> Generator[Session, None, None]:
        yield db_session

    app.dependency_overrides[get_db] = _override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


# ----- data factories -----
def make_user(
    db: Session,
    *,
    email: str | None = None,
    password: str = "Password123",
    role: UserRole = UserRole.CUSTOMER,
    is_active: bool = True,
) -> User:
    user = User(
        email=email or f"user_{uuid.uuid4().hex[:8]}@example.com",
        hashed_password=hash_password(password),
        full_name="Test User",
        role=role,
        is_active=is_active,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def make_product(
    db: Session,
    *,
    name: str = "Produk Uji",
    sku: str | None = None,
    price: str = "10000.00",
    stock: int = 10,
    is_active: bool = True,
    category: Category | None = None,
) -> Product:
    from decimal import Decimal

    product = Product(
        sku=sku or f"SKU-{uuid.uuid4().hex[:8]}",
        name=name,
        price=Decimal(price),
        stock_quantity=stock,
        is_active=is_active,
        category_id=category.id if category else None,
    )
    db.add(product)
    db.commit()
    db.refresh(product)
    return product


def auth_headers(client: TestClient, email: str, password: str) -> dict[str, str]:
    response = client.post(
        "/api/v1/auth/login", json={"email": email, "password": password}
    )
    assert response.status_code == 200, response.text
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}
