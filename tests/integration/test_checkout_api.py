"""Integration tests for cart, checkout, and concurrent stock handling."""

import concurrent.futures

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models import UserRole
from tests.conftest import auth_headers, make_product, make_user


def _setup_customer_with_cart(
    client: TestClient, db_session: Session, *, stock: int, quantity: int
):
    make_user(db_session, email="buyer@example.com", password="Password123")
    product = make_product(db_session, stock=stock, price="10000.00", name="Produk Uji")
    headers = auth_headers(client, "buyer@example.com", "Password123")

    add = client.post(
        "/api/v1/cart/items",
        json={"product_id": str(product.id), "quantity": quantity},
        headers=headers,
    )
    assert add.status_code == 200, add.text
    return product, headers


def test_cart_requires_auth(client: TestClient) -> None:
    assert client.get("/api/v1/cart").status_code == 401


def test_add_item_exceeds_stock_409(client: TestClient, db_session: Session) -> None:
    make_user(db_session, email="stock@example.com", password="Password123")
    product = make_product(db_session, stock=2)
    headers = auth_headers(client, "stock@example.com", "Password123")

    resp = client.post(
        "/api/v1/cart/items",
        json={"product_id": str(product.id), "quantity": 5},
        headers=headers,
    )

    assert resp.status_code == 409
    assert resp.json()["error"]["code"] == "INSUFFICIENT_STOCK"


def test_add_item_quantity_min_1(client: TestClient, db_session: Session) -> None:
    make_user(db_session, email="q@example.com", password="Password123")
    product = make_product(db_session, stock=5)
    headers = auth_headers(client, "q@example.com", "Password123")

    resp = client.post(
        "/api/v1/cart/items",
        json={"product_id": str(product.id), "quantity": 0},
        headers=headers,
    )
    assert resp.status_code == 422


def test_checkout_success(client: TestClient, db_session: Session) -> None:
    product, headers = _setup_customer_with_cart(
        client, db_session, stock=10, quantity=3
    )

    resp = client.post(
        "/api/v1/checkout",
        json={"shipping_address": "Jl. Merdeka No. 10, Jakarta"},
        headers=headers,
    )

    assert resp.status_code == 201, resp.text
    body = resp.json()
    assert body["total_amount"] == "30000.00"
    assert body["status"] == "pending"
    assert body["items"][0]["product_name_snapshot"] == product.name

    db_session.refresh(product)
    assert product.stock_quantity == 7

    cart = client.get("/api/v1/cart", headers=headers)
    assert cart.json()["items"] == []


def test_checkout_then_order_history_and_detail(
    client: TestClient, db_session: Session
) -> None:
    _, headers = _setup_customer_with_cart(client, db_session, stock=5, quantity=1)
    order = client.post(
        "/api/v1/checkout",
        json={"shipping_address": "Jl. Sudirman No. 1"},
        headers=headers,
    ).json()

    history = client.get("/api/v1/orders", headers=headers)
    assert history.status_code == 200
    assert history.json()["total"] == 1

    detail = client.get(f"/api/v1/orders/{order['id']}", headers=headers)
    assert detail.status_code == 200
    assert detail.json()["id"] == order["id"]


def test_admin_status_transition(client: TestClient, db_session: Session) -> None:
    _, customer_headers = _setup_customer_with_cart(
        client, db_session, stock=5, quantity=1
    )
    order = client.post(
        "/api/v1/checkout",
        json={"shipping_address": "Jl. Thamrin No. 2"},
        headers=customer_headers,
    ).json()

    make_user(
        db_session,
        email="admin2@example.com",
        password="Password123",
        role=UserRole.ADMIN,
    )
    admin_headers = auth_headers(client, "admin2@example.com", "Password123")

    resp = client.patch(
        f"/api/v1/admin/orders/{order['id']}/status",
        json={"status": "paid"},
        headers=admin_headers,
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "paid"

    invalid = client.patch(
        f"/api/v1/admin/orders/{order['id']}/status",
        json={"status": "delivered"},
        headers=admin_headers,
    )
    assert invalid.status_code == 409
    assert invalid.json()["error"]["code"] == "INVALID_STATUS_TRANSITION"


def test_checkout_insufficient_stock_409(client: TestClient, db_session: Session) -> None:
    make_user(db_session, email="low@example.com", password="Password123")
    product = make_product(db_session, stock=1)
    headers = auth_headers(client, "low@example.com", "Password123")
    client.post(
        "/api/v1/cart/items",
        json={"product_id": str(product.id), "quantity": 1},
        headers=headers,
    )
    # Stock drops after the item was added to the cart.
    product.stock_quantity = 0
    db_session.commit()

    resp = client.post(
        "/api/v1/checkout",
        json={"shipping_address": "Jl. Test No. 3"},
        headers=headers,
    )
    assert resp.status_code == 409
    assert resp.json()["error"]["code"] == "INSUFFICIENT_STOCK"


def test_concurrent_checkout_limited_stock(
    client: TestClient, db_session: Session
) -> None:
    """Two customers race for the last unit; exactly one checkout succeeds."""
    make_user(db_session, email="a@example.com", password="Password123")
    make_user(db_session, email="b@example.com", password="Password123")
    product = make_product(db_session, stock=1, name="Barang Langka")
    headers_a = auth_headers(client, "a@example.com", "Password123")
    headers_b = auth_headers(client, "b@example.com", "Password123")

    for headers in (headers_a, headers_b):
        add = client.post(
            "/api/v1/cart/items",
            json={"product_id": str(product.id), "quantity": 1},
            headers=headers,
        )
        assert add.status_code == 200, add.text

    def do_checkout(headers: dict[str, str]) -> int:
        return client.post(
            "/api/v1/checkout",
            json={"shipping_address": "Jl. Race No. 1"},
            headers=headers,
        ).status_code

    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(do_checkout, [headers_a, headers_b]))

    # Exactly one success and one stock-conflict.
    assert results.count(201) == 1
    assert 409 in results

    db_session.refresh(product)
    assert product.stock_quantity == 0
