"""Shopping cart API endpoints (authenticated customers)."""

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends

from app.core.dependencies import CurrentUser, DbSession
from app.repositories.cart_repository import CartRepository
from app.repositories.product_repository import ProductRepository
from app.schemas.cart import CartItemAdd, CartItemUpdate, CartResponse
from app.services.cart_service import CartService

router = APIRouter(prefix="/cart", tags=["Cart"])


def get_cart_service(db: DbSession) -> CartService:
    """Construct CartService with its repositories."""
    return CartService(
        cart_repository=CartRepository(db),
        product_repository=ProductRepository(db),
    )


CartServiceDep = Annotated[CartService, Depends(get_cart_service)]


@router.get("", response_model=CartResponse, summary="Lihat keranjang")
def get_cart(current_user: CurrentUser, service: CartServiceDep) -> CartResponse:
    return service.get_cart(current_user.id)


@router.post("/items", response_model=CartResponse, summary="Tambah item ke keranjang")
def add_item(
    payload: CartItemAdd,
    current_user: CurrentUser,
    service: CartServiceDep,
) -> CartResponse:
    return service.add_item(current_user.id, payload)


@router.patch("/items/{item_id}", response_model=CartResponse, summary="Ubah jumlah item")
def update_item(
    item_id: uuid.UUID,
    payload: CartItemUpdate,
    current_user: CurrentUser,
    service: CartServiceDep,
) -> CartResponse:
    return service.update_item(current_user.id, item_id, payload)


@router.delete("/items/{item_id}", response_model=CartResponse, summary="Hapus item dari keranjang")
def remove_item(
    item_id: uuid.UUID,
    current_user: CurrentUser,
    service: CartServiceDep,
) -> CartResponse:
    return service.remove_item(current_user.id, item_id)
