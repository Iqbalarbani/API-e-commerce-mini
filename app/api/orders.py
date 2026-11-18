"""Checkout and order management API endpoints."""

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Query, status

from app.core.dependencies import AdminUser, CurrentUser, DbSession
from app.models.order import OrderStatus
from app.repositories.cart_repository import CartRepository
from app.repositories.order_repository import OrderRepository
from app.schemas.order import (
    CheckoutRequest,
    OrderDetailResponse,
    OrderListResponse,
    OrderStatusUpdate,
)
from app.services.order_service import OrderService

router = APIRouter(tags=["Orders"])


def get_order_service(db: DbSession) -> OrderService:
    """Construct OrderService with its repositories."""
    return OrderService(
        order_repository=OrderRepository(db),
        cart_repository=CartRepository(db),
    )


OrderServiceDep = Annotated[OrderService, Depends(get_order_service)]


@router.post(
    "/checkout",
    response_model=OrderDetailResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Checkout keranjang menjadi order",
)
def checkout(
    payload: CheckoutRequest,
    current_user: CurrentUser,
    service: OrderServiceDep,
) -> OrderDetailResponse:
    return service.checkout(current_user.id, payload)


@router.get("/orders", response_model=OrderListResponse, summary="Riwayat order saya")
def list_my_orders(
    current_user: CurrentUser,
    service: OrderServiceDep,
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=10, ge=1, le=100),
) -> OrderListResponse:
    return service.list_my_orders(current_user.id, page=page, limit=limit)


@router.get(
    "/orders/{order_id}",
    response_model=OrderDetailResponse,
    summary="Detail order saya",
)
def get_my_order(
    order_id: uuid.UUID,
    current_user: CurrentUser,
    service: OrderServiceDep,
) -> OrderDetailResponse:
    return service.get_order_detail(order_id, owner_id=current_user.id)


@router.get(
    "/admin/orders",
    response_model=OrderListResponse,
    summary="Semua order (admin)",
)
def list_all_orders(
    _admin: AdminUser,
    service: OrderServiceDep,
    order_status: OrderStatus | None = Query(default=None, alias="status"),
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=10, ge=1, le=100),
) -> OrderListResponse:
    return service.list_all_orders(page=page, limit=limit, order_status=order_status)


@router.get(
    "/admin/orders/{order_id}",
    response_model=OrderDetailResponse,
    summary="Detail order (admin)",
)
def get_order_admin(
    order_id: uuid.UUID,
    _admin: AdminUser,
    service: OrderServiceDep,
) -> OrderDetailResponse:
    return service.get_order_detail(order_id, owner_id=None)


@router.patch(
    "/admin/orders/{order_id}/status",
    response_model=OrderDetailResponse,
    summary="Update status order (admin)",
)
def update_order_status(
    order_id: uuid.UUID,
    payload: OrderStatusUpdate,
    _admin: AdminUser,
    service: OrderServiceDep,
) -> OrderDetailResponse:
    return service.update_status(order_id, payload.status)
