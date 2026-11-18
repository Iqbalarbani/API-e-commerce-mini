"""Category and product API endpoints."""

import uuid
from decimal import Decimal
from typing import Annotated

from fastapi import APIRouter, Depends, Query, status

from app.core.dependencies import AdminUser, DbSession
from app.repositories.product_repository import ProductRepository
from app.schemas.product import (
    CategoryCreate,
    CategoryResponse,
    ProductCreate,
    ProductListResponse,
    ProductResponse,
    ProductSort,
    ProductUpdate,
)
from app.services.product_service import ProductService

router = APIRouter(tags=["Catalog"])


def get_product_service(db: DbSession) -> ProductService:
    """Construct ProductService with its repository."""
    return ProductService(repository=ProductRepository(db))


ProductServiceDep = Annotated[ProductService, Depends(get_product_service)]


# ----- categories -----
@router.get("/categories", response_model=list[CategoryResponse], summary="Daftar kategori")
def list_categories(service: ProductServiceDep) -> list[CategoryResponse]:
    return [CategoryResponse.model_validate(c) for c in service.list_categories()]


@router.post(
    "/categories",
    response_model=CategoryResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Buat kategori (admin)",
)
def create_category(
    payload: CategoryCreate,
    _admin: AdminUser,
    service: ProductServiceDep,
) -> CategoryResponse:
    return CategoryResponse.model_validate(service.create_category(payload))


# ----- products -----
@router.get("/products", response_model=ProductListResponse, summary="Daftar produk")
def list_products(
    service: ProductServiceDep,
    search: str | None = Query(default=None, max_length=100),
    category_id: uuid.UUID | None = None,
    min_price: Decimal | None = Query(default=None, ge=0),
    max_price: Decimal | None = Query(default=None, ge=0),
    sort: ProductSort = ProductSort.NEWEST,
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=10, ge=1, le=100),
) -> ProductListResponse:
    return service.list_products(
        search=search,
        category_id=category_id,
        min_price=min_price,
        max_price=max_price,
        sort=sort,
        page=page,
        limit=limit,
    )


@router.get("/products/{product_id}", response_model=ProductResponse, summary="Detail produk")
def get_product(product_id: uuid.UUID, service: ProductServiceDep) -> ProductResponse:
    return ProductResponse.model_validate(service.get_product(product_id))


@router.post(
    "/products",
    response_model=ProductResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Buat produk (admin)",
)
def create_product(
    payload: ProductCreate,
    _admin: AdminUser,
    service: ProductServiceDep,
) -> ProductResponse:
    return ProductResponse.model_validate(service.create_product(payload))


@router.patch(
    "/products/{product_id}", response_model=ProductResponse, summary="Ubah produk (admin)"
)
def update_product(
    product_id: uuid.UUID,
    payload: ProductUpdate,
    _admin: AdminUser,
    service: ProductServiceDep,
) -> ProductResponse:
    return ProductResponse.model_validate(service.update_product(product_id, payload))
