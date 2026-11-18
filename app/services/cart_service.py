"""Service layer for shopping cart business rules."""

import uuid
from decimal import Decimal

from fastapi import status

from app.core.exceptions import AppException
from app.models.cart import Cart
from app.models.product import Product
from app.repositories.cart_repository import CartRepository
from app.repositories.product_repository import ProductRepository
from app.schemas.cart import (
    CartItemAdd,
    CartItemResponse,
    CartItemUpdate,
    CartResponse,
)


class CartService:
    """Business rules for managing the customer cart."""

    def __init__(
        self, cart_repository: CartRepository, product_repository: ProductRepository
    ) -> None:
        self.cart_repository = cart_repository
        self.product_repository = product_repository

    def get_cart(self, user_id: uuid.UUID) -> CartResponse:
        cart = self.cart_repository.get_or_create_cart(user_id)
        return self._to_response(cart)

    def add_item(self, user_id: uuid.UUID, payload: CartItemAdd) -> CartResponse:
        product = self._get_active_product(payload.product_id)
        cart = self.cart_repository.get_or_create_cart(user_id)

        existing = self.cart_repository.get_item(cart.id, product.id)
        new_quantity = payload.quantity + (existing.quantity if existing else 0)
        self._ensure_stock(product, new_quantity)

        if existing is not None:
            self.cart_repository.update_item(existing, new_quantity)
        else:
            self.cart_repository.add_item(cart.id, product.id, payload.quantity)

        return self.get_cart(user_id)

    def update_item(
        self, user_id: uuid.UUID, item_id: uuid.UUID, payload: CartItemUpdate
    ) -> CartResponse:
        cart = self.cart_repository.get_or_create_cart(user_id)
        item = self.cart_repository.get_item_by_id(cart.id, item_id)
        if item is None:
            raise self._item_not_found()

        product = self._get_active_product(item.product_id)
        self._ensure_stock(product, payload.quantity)
        self.cart_repository.update_item(item, payload.quantity)
        return self.get_cart(user_id)

    def remove_item(self, user_id: uuid.UUID, item_id: uuid.UUID) -> CartResponse:
        cart = self.cart_repository.get_or_create_cart(user_id)
        item = self.cart_repository.get_item_by_id(cart.id, item_id)
        if item is None:
            raise self._item_not_found()
        self.cart_repository.delete_item(item)
        return self.get_cart(user_id)

    # ----- helpers -----
    def _get_active_product(self, product_id: uuid.UUID) -> Product:
        product = self.product_repository.get_product(product_id)
        if product is None or not product.is_active:
            raise AppException(
                code="PRODUCT_NOT_FOUND",
                message="Produk tidak ditemukan atau tidak aktif.",
                status_code=status.HTTP_404_NOT_FOUND,
            )
        return product

    @staticmethod
    def _ensure_stock(product: Product, quantity: int) -> None:
        if quantity > product.stock_quantity:
            raise AppException(
                code="INSUFFICIENT_STOCK",
                message=(
                    f"Stok tidak mencukupi untuk '{product.name}'. "
                    f"Tersedia {product.stock_quantity}."
                ),
                status_code=status.HTTP_409_CONFLICT,
            )

    @staticmethod
    def _item_not_found() -> AppException:
        return AppException(
            code="CART_ITEM_NOT_FOUND",
            message="Item keranjang tidak ditemukan.",
            status_code=status.HTTP_404_NOT_FOUND,
        )

    def _to_response(self, cart: Cart) -> CartResponse:
        items: list[CartItemResponse] = []
        total_items = 0
        total_price = Decimal("0.00")
        for item in cart.items:
            product = item.product
            subtotal = (product.price * item.quantity).quantize(Decimal("0.01"))
            items.append(
                CartItemResponse(
                    id=item.id,
                    product_id=product.id,
                    product_name=product.name,
                    unit_price=product.price,
                    quantity=item.quantity,
                    stock_quantity=product.stock_quantity,
                    subtotal=subtotal,
                )
            )
            total_items += item.quantity
            total_price += subtotal
        return CartResponse(
            id=cart.id,
            items=items,
            total_items=total_items,
            total_price=total_price.quantize(Decimal("0.01")),
        )
