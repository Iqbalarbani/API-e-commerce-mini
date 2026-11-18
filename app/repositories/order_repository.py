"""Repository for Order and OrderItem persistence, including row locks."""

import uuid
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.models.order import Order, OrderItem, OrderStatus
from app.models.product import Product


class OrderRepository:
    """Encapsulates database access for orders."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def lock_products_for_update(self, product_ids: list[uuid.UUID]) -> dict[uuid.UUID, Product]:
        """Acquire PostgreSQL row-level locks on products.

        ``SELECT ... FOR UPDATE`` blocks concurrent transactions touching the
        same rows, preventing two checkouts from reading the same stock and
        both decrementing it into the negatives. Locks are held until the
        surrounding transaction commits or rolls back.
        """
        if not product_ids:
            return {}
        ordered_ids = sorted(set(product_ids))
        stmt = (
            select(Product)
            .where(Product.id.in_(ordered_ids))
            .order_by(Product.id)
            .with_for_update()
        )
        products = list(self.db.scalars(stmt))
        return {product.id: product for product in products}

    def create_order(
        self,
        *,
        user_id: uuid.UUID,
        status: OrderStatus,
        total_amount: Decimal,
        shipping_address: str,
        notes: str | None,
        items: list[OrderItem],
    ) -> Order:
        order = Order(
            user_id=user_id,
            status=status,
            total_amount=total_amount,
            shipping_address=shipping_address,
            notes=notes,
        )
        order.items = items
        self.db.add(order)
        self.db.flush()
        return order

    def get_order(self, order_id: uuid.UUID) -> Order | None:
        stmt = (
            select(Order)
            .where(Order.id == order_id)
            .options(selectinload(Order.items))
        )
        return self.db.scalar(stmt)

    def list_orders(
        self,
        *,
        user_id: uuid.UUID | None,
        page: int,
        limit: int,
        status: OrderStatus | None = None,
    ) -> tuple[list[Order], int]:
        conditions = []
        if user_id is not None:
            conditions.append(Order.user_id == user_id)
        if status is not None:
            conditions.append(Order.status == status)

        total = self.db.scalar(select(func.count()).select_from(Order).where(*conditions)) or 0
        stmt = (
            select(Order)
            .where(*conditions)
            .order_by(Order.created_at.desc(), Order.id.desc())
            .offset((page - 1) * limit)
            .limit(limit)
        )
        return list(self.db.scalars(stmt)), total

    def update_status(self, order: Order, status: OrderStatus) -> Order:
        order.status = status
        self.db.flush()
        return order
