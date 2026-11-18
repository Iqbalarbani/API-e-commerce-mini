"""Repository for Cart and CartItem persistence."""

import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models.cart import Cart, CartItem


class CartRepository:
    """Encapsulates database access for shopping carts."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def get_or_create_cart(self, user_id: uuid.UUID) -> Cart:
        """Return the user's cart, creating it when missing."""
        cart = self._get_cart_by_user(user_id)
        if cart is not None:
            return cart
        cart = Cart(user_id=user_id)
        self.db.add(cart)
        self.db.commit()
        self.db.refresh(cart)
        return self._get_cart_by_user(user_id) or cart

    def _get_cart_by_user(self, user_id: uuid.UUID) -> Cart | None:
        stmt = (
            select(Cart)
            .where(Cart.user_id == user_id)
            .options(selectinload(Cart.items).selectinload(CartItem.product))
        )
        return self.db.scalar(stmt)

    def get_item(self, cart_id: uuid.UUID, product_id: uuid.UUID) -> CartItem | None:
        return self.db.scalar(
            select(CartItem).where(
                CartItem.cart_id == cart_id,
                CartItem.product_id == product_id,
            )
        )

    def get_item_by_id(self, cart_id: uuid.UUID, item_id: uuid.UUID) -> CartItem | None:
        return self.db.scalar(
            select(CartItem).where(
                CartItem.cart_id == cart_id,
                CartItem.id == item_id,
            )
        )

    def add_item(self, cart_id: uuid.UUID, product_id: uuid.UUID, quantity: int) -> CartItem:
        item = CartItem(cart_id=cart_id, product_id=product_id, quantity=quantity)
        self.db.add(item)
        self.db.commit()
        self.db.refresh(item)
        return item

    def update_item(self, item: CartItem, quantity: int) -> CartItem:
        item.quantity = quantity
        self.db.commit()
        self.db.refresh(item)
        return item

    def delete_item(self, item: CartItem) -> None:
        self.db.delete(item)
        self.db.commit()

    def clear_items(self, cart_id: uuid.UUID) -> None:
        for item in list(self.db.scalars(select(CartItem).where(CartItem.cart_id == cart_id))):
            self.db.delete(item)
        self.db.commit()
