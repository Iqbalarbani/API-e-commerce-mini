"""Unit tests for CartService using fake repositories."""

import uuid
from datetime import UTC, datetime
from decimal import Decimal

import pytest

from app.core.exceptions import AppException
from app.models.cart import Cart, CartItem
from app.models.product import Product
from app.schemas.cart import CartItemAdd, CartItemUpdate
from app.services.cart_service import CartService


class FakeProductRepository:
    def __init__(self, products: list[Product]) -> None:
        self.products = {p.id: p for p in products}

    def get_product(self, product_id: uuid.UUID) -> Product | None:
        return self.products.get(product_id)


class FakeCartRepository:
    """In-memory cart store keyed by user id."""

    def __init__(self, products: list[Product] | None = None) -> None:
        self.carts: dict[uuid.UUID, Cart] = {}
        self._products = {p.id: p for p in (products or [])}

    def get_or_create_cart(self, user_id: uuid.UUID) -> Cart:
        cart = self.carts.get(user_id)
        if cart is None:
            cart = Cart(id=uuid.uuid4(), user_id=user_id)
            cart.items = []
            self.carts[user_id] = cart
        return cart

    def get_item(self, cart_id: uuid.UUID, product_id: uuid.UUID) -> CartItem | None:
        for cart in self.carts.values():
            if cart.id == cart_id:
                return next((i for i in cart.items if i.product_id == product_id), None)
        return None

    def get_item_by_id(self, cart_id: uuid.UUID, item_id: uuid.UUID) -> CartItem | None:
        for cart in self.carts.values():
            if cart.id == cart_id:
                return next((i for i in cart.items if i.id == item_id), None)
        return None

    def add_item(self, cart_id: uuid.UUID, product_id: uuid.UUID, quantity: int) -> CartItem:
        cart = next(c for c in self.carts.values() if c.id == cart_id)
        item = CartItem(
            id=uuid.uuid4(),
            cart_id=cart_id,
            product_id=product_id,
            quantity=quantity,
        )
        item.product = self._products.get(product_id)
        cart.items.append(item)
        return item

    def update_item(self, item: CartItem, quantity: int) -> CartItem:
        item.quantity = quantity
        return item

    def delete_item(self, item: CartItem) -> None:
        for cart in self.carts.values():
            if item in cart.items:
                cart.items.remove(item)

    def clear_items(self, cart_id: uuid.UUID) -> None:
        for cart in self.carts.values():
            if cart.id == cart_id:
                cart.items = []


def _product(*, stock: int = 10, price: str = "5000.00", active: bool = True) -> Product:
    return Product(
        id=uuid.uuid4(),
        sku=f"SKU-{uuid.uuid4().hex[:6]}",
        name="Produk",
        price=Decimal(price),
        stock_quantity=stock,
        is_active=active,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )


def _make_service(
    products: list[Product],
) -> tuple[CartService, FakeCartRepository, FakeProductRepository]:
    cart_repo = FakeCartRepository(products)
    product_repo = FakeProductRepository(products)
    service = CartService(cart_repository=cart_repo, product_repository=product_repo)
    return service, cart_repo, product_repo


def test_add_item_computes_totals() -> None:
    product = _product(stock=10, price="5000.00")
    service, _, _ = _make_service([product])

    cart = service.add_item(uuid.uuid4(), CartItemAdd(product_id=product.id, quantity=2))

    assert cart.total_items == 2
    assert cart.total_price == Decimal("10000.00")
    assert cart.items[0].subtotal == Decimal("10000.00")


def test_add_item_accumulates_quantity() -> None:
    product = _product(stock=10)
    service, _, _ = _make_service([product])
    user_id = uuid.uuid4()

    service.add_item(user_id, CartItemAdd(product_id=product.id, quantity=2))
    cart = service.add_item(user_id, CartItemAdd(product_id=product.id, quantity=3))

    assert cart.total_items == 5


def test_add_item_exceeds_stock_fails() -> None:
    product = _product(stock=3)
    service, _, _ = _make_service([product])

    with pytest.raises(AppException) as exc:
        service.add_item(uuid.uuid4(), CartItemAdd(product_id=product.id, quantity=5))

    assert exc.value.code == "INSUFFICIENT_STOCK"


def test_add_inactive_product_fails() -> None:
    product = _product(active=False)
    service, _, _ = _make_service([product])

    with pytest.raises(AppException) as exc:
        service.add_item(uuid.uuid4(), CartItemAdd(product_id=product.id, quantity=1))

    assert exc.value.code == "PRODUCT_NOT_FOUND"


def test_update_item_respects_stock() -> None:
    product = _product(stock=5)
    service, _, _ = _make_service([product])
    user_id = uuid.uuid4()
    cart = service.add_item(user_id, CartItemAdd(product_id=product.id, quantity=1))
    item_id = cart.items[0].id

    with pytest.raises(AppException) as exc:
        service.update_item(user_id, item_id, CartItemUpdate(quantity=9))

    assert exc.value.code == "INSUFFICIENT_STOCK"


def test_remove_item() -> None:
    product = _product(stock=5)
    service, _, _ = _make_service([product])
    user_id = uuid.uuid4()
    cart = service.add_item(user_id, CartItemAdd(product_id=product.id, quantity=2))

    result = service.remove_item(user_id, cart.items[0].id)

    assert result.items == []
