"""Pydantic schemas for checkout and order management."""

import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

from app.models.order import OrderStatus


class CheckoutRequest(BaseModel):
    """Payload to convert the current cart into an order."""

    shipping_address: str = Field(..., min_length=5, max_length=500)
    notes: str | None = Field(default=None, max_length=500)


class OrderItemResponse(BaseModel):
    """Price-snapshotted line item on an order."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    product_id: uuid.UUID
    product_name_snapshot: str
    unit_price: Decimal
    quantity: int
    subtotal: Decimal


class OrderResponse(BaseModel):
    """Order summary returned in list endpoints."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    status: OrderStatus
    total_amount: Decimal
    shipping_address: str
    notes: str | None = None
    created_at: datetime


class OrderDetailResponse(OrderResponse):
    """Order with its line items."""

    items: list[OrderItemResponse]


class OrderListResponse(BaseModel):
    """Paginated order list."""

    items: list[OrderResponse]
    total: int
    page: int
    limit: int


class OrderStatusUpdate(BaseModel):
    """Admin payload to transition an order status."""

    status: OrderStatus
