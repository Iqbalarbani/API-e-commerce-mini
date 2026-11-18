"""Service layer for checkout and order lifecycle."""

import uuid
from decimal import Decimal

from fastapi import status

from app.core.exceptions import AppException
from app.models.cart import CartItem
from app.models.order import Order, OrderItem, OrderStatus
from app.repositories.cart_repository import CartRepository
from app.repositories.order_repository import OrderRepository
from app.schemas.order import (
    CheckoutRequest,
    OrderDetailResponse,
    OrderItemResponse,
    OrderListResponse,
    OrderResponse,
)

ALLOWED_TRANSITIONS: dict[OrderStatus, set[OrderStatus]] = {
    OrderStatus.PENDING: {OrderStatus.PAID, OrderStatus.CANCELLED},
    OrderStatus.PAID: {OrderStatus.SHIPPED, OrderStatus.CANCELLED},
    OrderStatus.SHIPPED: {OrderStatus.DELIVERED},
    OrderStatus.DELIVERED: set(),
    OrderStatus.CANCELLED: set(),
}


class OrderService:
    """Business rules for checkout and order management."""

    def __init__(self, order_repository: OrderRepository, cart_repository: CartRepository) -> None:
        self.order_repository = order_repository
        self.cart_repository = cart_repository

    @property
    def _db(self):
        return self.order_repository.db

    def checkout(self, user_id: uuid.UUID, payload: CheckoutRequest) -> OrderDetailResponse:
        """Convert the user's cart into an order inside a single transaction.

        Race-condition safety: every referenced product row is locked with
        ``SELECT ... FOR UPDATE`` before stock is inspected or mutated. A
        concurrent checkout on the same product blocks until the first
        transaction commits, then re-reads the already-decremented stock and
        fails cleanly instead of allowing stock to go negative.
        """
        cart = self.cart_repository.get_or_create_cart(user_id)
        if not cart.items:
            raise AppException(
                code="CART_EMPTY",
                message="Keranjang kosong, tidak ada yang bisa di-checkout.",
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        product_ids = [item.product_id for item in cart.items]
        try:
            locked = self.order_repository.lock_products_for_update(product_ids)

            order_items: list[OrderItem] = []
            total_amount = Decimal("0.00")

            for cart_item in cart.items:
                product = locked.get(cart_item.product_id)
                self._validate_line(product, cart_item)
                subtotal = (product.price * cart_item.quantity).quantize(Decimal("0.01"))
                order_items.append(
                    OrderItem(
                        product_id=product.id,
                        product_name_snapshot=product.name,
                        unit_price=product.price,
                        quantity=cart_item.quantity,
                        subtotal=subtotal,
                    )
                )
                product.stock_quantity -= cart_item.quantity
                total_amount += subtotal

            order = self.order_repository.create_order(
                user_id=user_id,
                status=OrderStatus.PENDING,
                total_amount=total_amount.quantize(Decimal("0.01")),
                shipping_address=payload.shipping_address.strip(),
                notes=payload.notes,
                items=order_items,
            )

            for cart_item in list(cart.items):
                self._db.delete(cart_item)

            self._db.commit()
        except Exception:
            self._db.rollback()
            raise

        self._db.refresh(order)
        return self._to_detail(order)

    def list_my_orders(
        self, user_id: uuid.UUID, *, page: int, limit: int
    ) -> OrderListResponse:
        items, total = self.order_repository.list_orders(
            user_id=user_id, page=page, limit=limit
        )
        return OrderListResponse(
            items=[OrderResponse.model_validate(o) for o in items],
            total=total,
            page=page,
            limit=limit,
        )

    def list_all_orders(
        self, *, page: int, limit: int, order_status: OrderStatus | None = None
    ) -> OrderListResponse:
        items, total = self.order_repository.list_orders(
            user_id=None, page=page, limit=limit, status=order_status
        )
        return OrderListResponse(
            items=[OrderResponse.model_validate(o) for o in items],
            total=total,
            page=page,
            limit=limit,
        )

    def get_order_detail(
        self, order_id: uuid.UUID, *, owner_id: uuid.UUID | None
    ) -> OrderDetailResponse:
        order = self.order_repository.get_order(order_id)
        if order is None or (owner_id is not None and order.user_id != owner_id):
            raise self._not_found()
        return self._to_detail(order)

    def update_status(self, order_id: uuid.UUID, new_status: OrderStatus) -> OrderDetailResponse:
        order = self.order_repository.get_order(order_id)
        if order is None:
            raise self._not_found()

        if new_status not in ALLOWED_TRANSITIONS.get(order.status, set()):
            raise AppException(
                code="INVALID_STATUS_TRANSITION",
                message=(
                    f"Transisi status dari '{order.status.value}' ke "
                    f"'{new_status.value}' tidak diizinkan."
                ),
                status_code=status.HTTP_409_CONFLICT,
            )

        try:
            if new_status is OrderStatus.CANCELLED:
                product_ids = [item.product_id for item in order.items]
                locked = self.order_repository.lock_products_for_update(product_ids)
                for item in order.items:
                    product = locked.get(item.product_id)
                    if product is not None:
                        product.stock_quantity += item.quantity

            self.order_repository.update_status(order, new_status)
            self._db.commit()
        except Exception:
            self._db.rollback()
            raise

        self._db.refresh(order)
        return self._to_detail(order)

    # ----- helpers -----
    @staticmethod
    def _validate_line(product, cart_item: CartItem) -> None:
        if product is None or not product.is_active:
            raise AppException(
                code="PRODUCT_NOT_FOUND",
                message="Produk pada keranjang tidak ditemukan atau tidak aktif.",
                status_code=status.HTTP_409_CONFLICT,
            )
        if product.stock_quantity < cart_item.quantity:
            raise AppException(
                code="INSUFFICIENT_STOCK",
                message=(
                    f"Stok tidak mencukupi untuk '{product.name}'. "
                    f"Tersedia {product.stock_quantity}, diminta {cart_item.quantity}."
                ),
                status_code=status.HTTP_409_CONFLICT,
            )

    @staticmethod
    def _not_found() -> AppException:
        return AppException(
            code="ORDER_NOT_FOUND",
            message="Order tidak ditemukan.",
            status_code=status.HTTP_404_NOT_FOUND,
        )

    @staticmethod
    def _to_detail(order: Order) -> OrderDetailResponse:
        return OrderDetailResponse(
            id=order.id,
            status=order.status,
            total_amount=order.total_amount,
            shipping_address=order.shipping_address,
            notes=order.notes,
            created_at=order.created_at,
            items=[OrderItemResponse.model_validate(i) for i in order.items],
        )
