"""Pydantic schemas for shopping cart endpoints."""

import uuid
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class CartItemAdd(BaseModel):
    """Payload to add a product to the cart."""

    product_id: uuid.UUID
    quantity: int = Field(..., ge=1, description="Minimal 1")


class CartItemUpdate(BaseModel):
    """Payload to change the quantity of an existing cart item."""

    quantity: int = Field(..., ge=1, description="Minimal 1")


class CartItemResponse(BaseModel):
    """A single product line inside the cart."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    product_id: uuid.UUID
    product_name: str
    unit_price: Decimal
    quantity: int
    stock_quantity: int
    subtotal: Decimal


class CartResponse(BaseModel):
    """The full cart for the current user."""

    id: uuid.UUID
    items: list[CartItemResponse]
    total_items: int
    total_price: Decimal
