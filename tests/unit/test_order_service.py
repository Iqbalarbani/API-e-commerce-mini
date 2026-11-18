"""Unit tests for OrderService checkout and status transitions."""

import uuid
from datetime import UTC, datetime
from decimal import Decimal

import pytest

from app.core.exceptions import AppException
from app.models.cart import Cart, CartItem
from app.models.order import Order, OrderStatus
from app.models.product import Product
from app.schemas.order import CheckoutRequest
from app.services.order_service import OrderService


class FakeDb:
    def __init__(self) -> None:
        self.committed = False
        self.rolled_back = False

    def delete(self, obj) -> None:  # noqa: ANN001 - cart items
        pass

    def commit(self) -> None:
        self.committed = True

    def rollback(self) -> None:
        self.rolled_back = True

    def refresh(self, obj) -> None:  # noqa: ANN001
        pass


class FakeCartRepository:
    def __init__(self, cart: Cart) -> None:
        self.cart = cart
        self.db = FakeDb()

    def get_or_create_cart(self, user_id: uuid.UUID) -> Cart:
        return self.cart


class FakeOrderRepository:
    def __init__(self, cart: Cart) -> None:
        self.cart = cart
        self.db = FakeDb()
        self.orders: dict[uuid.UUID, Order] = {}
        self.last_order: Order | None = None

    def lock_products_for_update(self, product_ids):
        return {i.product_id: i.product for i in self.cart.items}

    def create_order(self, *, user_id, status, total_amount, shipping_address, notes, items):
        order = Order(
            id=uuid.uuid4(),
            user_id=user_id,
            status=status,
            total_amount=total_amount,
            shipping_address=shipping_address,
            notes=notes,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )
        for item in items:
            if item.id is None:
                item.id = uuid.uuid4()
            item.created_at = item.created_at or datetime.now(UTC)
            item.updated_at = item.updated_at or datetime.now(UTC)
        order.items = items
        self.orders[order.id] = order
        self.last_order = order
        return order

    def get_order(self, order_id):
        return self.orders.get(order_id)

    def update_status(self, order, status):
        order.status = status
        return order


def _make_cart(quantity: int = 2, stock: int = 10, active: bool = True) -> Cart:
    product = Product(
        id=uuid.uuid4(),
        sku="SKU-1",
        name="Produk",
        price=Decimal("7500.00"),
        stock_quantity=stock,
        is_active=active,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )
    item = CartItem(id=uuid.uuid4(), cart_id=uuid.uuid4(), product_id=product.id, quantity=quantity)
    item.product = product
    cart = Cart(id=uuid.uuid4(), user_id=uuid.uuid4())
    cart.items = [item]
    return cart


def _make_service(cart: Cart) -> tuple[OrderService, FakeOrderRepository]:
    cart_repo = FakeCartRepository(cart)
    order_repo = FakeOrderRepository(cart)
    return OrderService(order_repository=order_repo, cart_repository=cart_repo), order_repo


def test_checkout_success_creates_snapshot_and_decrements_stock() -> None:
    cart = _make_cart(quantity=2, stock=10)
    service, order_repo = _make_service(cart)

    result = service.checkout(
        cart.user_id, CheckoutRequest(shipping_address="Jl. Contoh No. 1")
    )

    assert result.total_amount == Decimal("15000.00")
    assert result.items[0].product_name_snapshot == "Produk"
    assert result.items[0].unit_price == Decimal("7500.00")
    product = cart.items[0].product
    assert product.stock_quantity == 8


def test_checkout_empty_cart_fails() -> None:
    cart = _make_cart()
    cart.items = []
    service, _ = _make_service(cart)

    with pytest.raises(AppException) as exc:
        service.checkout(cart.user_id, CheckoutRequest(shipping_address="Jl. Contoh"))

    assert exc.value.code == "CART_EMPTY"


def test_checkout_insufficient_stock_fails() -> None:
    cart = _make_cart(quantity=5, stock=2)
    service, order_repo = _make_service(cart)

    with pytest.raises(AppException) as exc:
        service.checkout(cart.user_id, CheckoutRequest(shipping_address="Jl. Contoh"))

    assert exc.value.code == "INSUFFICIENT_STOCK"


def test_checkout_inactive_product_fails() -> None:
    cart = _make_cart(active=False)
    service, _ = _make_service(cart)

    with pytest.raises(AppException) as exc:
        service.checkout(cart.user_id, CheckoutRequest(shipping_address="Jl. Contoh"))

    assert exc.value.code == "PRODUCT_NOT_FOUND"


def test_status_transition_pending_to_paid_allowed() -> None:
    cart = _make_cart()
    service, order_repo = _make_service(cart)
    detail = service.checkout(cart.user_id, CheckoutRequest(shipping_address="Jl. Contoh"))

    result = service.update_status(detail.id, OrderStatus.PAID)

    assert result.status == OrderStatus.PAID


def test_status_transition_invalid_fails() -> None:
    cart = _make_cart()
    service, _ = _make_service(cart)
    detail = service.checkout(cart.user_id, CheckoutRequest(shipping_address="Jl. Contoh"))

    with pytest.raises(AppException) as exc:
        service.update_status(detail.id, OrderStatus.DELIVERED)

    assert exc.value.code == "INVALID_STATUS_TRANSITION"
