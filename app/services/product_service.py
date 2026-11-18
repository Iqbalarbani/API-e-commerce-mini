"""Service layer for categories and products."""

import re
import uuid
from decimal import Decimal

from fastapi import status

from app.core.exceptions import AppException
from app.models.product import Category, Product
from app.repositories.product_repository import ProductRepository
from app.schemas.product import (
    CategoryCreate,
    ProductCreate,
    ProductListResponse,
    ProductResponse,
    ProductSort,
    ProductUpdate,
)


def slugify(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return slug or "kategori"


class ProductService:
    """Business rules for the catalog."""

    def __init__(self, repository: ProductRepository) -> None:
        self.repository = repository

    # ----- categories -----
    def list_categories(self) -> list[Category]:
        return self.repository.list_categories()

    def create_category(self, payload: CategoryCreate) -> Category:
        name = payload.name.strip()
        slug = slugify(payload.slug or name)
        if self.repository.get_category_by_name(name) or self.repository.get_category_by_slug(slug):
            raise AppException(
                code="CATEGORY_ALREADY_EXISTS",
                message="Kategori dengan nama atau slug tersebut sudah ada.",
                status_code=status.HTTP_409_CONFLICT,
            )
        return self.repository.create_category(
            name=name, slug=slug, description=payload.description
        )

    # ----- products -----
    def list_products(
        self,
        *,
        search: str | None,
        category_id: uuid.UUID | None,
        min_price: Decimal | None,
        max_price: Decimal | None,
        sort: ProductSort,
        page: int,
        limit: int,
    ) -> ProductListResponse:
        if min_price is not None and max_price is not None and min_price > max_price:
            raise AppException(
                code="INVALID_PRICE_RANGE",
                message="min_price tidak boleh lebih besar dari max_price.",
                status_code=status.HTTP_400_BAD_REQUEST,
            )
        items, total = self.repository.list_products(
            search=search.strip() if search else None,
            category_id=category_id,
            min_price=min_price,
            max_price=max_price,
            sort=sort,
            page=page,
            limit=limit,
        )
        return ProductListResponse(
            items=[ProductResponse.model_validate(p) for p in items],
            total=total,
            page=page,
            limit=limit,
        )

    def get_product(self, product_id: uuid.UUID) -> Product:
        product = self.repository.get_product(product_id)
        if product is None or not product.is_active:
            raise self._not_found()
        return product

    def create_product(self, payload: ProductCreate) -> Product:
        if self.repository.get_product_by_sku(payload.sku):
            raise AppException(
                code="SKU_ALREADY_EXISTS",
                message="SKU sudah digunakan.",
                status_code=status.HTTP_409_CONFLICT,
            )
        self._ensure_category(payload.category_id)
        return self.repository.create_product(**payload.model_dump())

    def update_product(self, product_id: uuid.UUID, payload: ProductUpdate) -> Product:
        product = self.repository.get_product(product_id)
        if product is None:
            raise self._not_found()
        fields = payload.model_dump(exclude_unset=True)
        if fields.get("category_id") is not None:
            self._ensure_category(fields["category_id"])
        return self.repository.update_product(product, **fields)

    # ----- helpers -----
    def _ensure_category(self, category_id: uuid.UUID | None) -> None:
        if category_id is not None and self.repository.get_category(category_id) is None:
            raise AppException(
                code="CATEGORY_NOT_FOUND",
                message="Kategori tidak ditemukan.",
                status_code=status.HTTP_404_NOT_FOUND,
            )

    @staticmethod
    def _not_found() -> AppException:
        return AppException(
            code="PRODUCT_NOT_FOUND",
            message="Produk tidak ditemukan.",
            status_code=status.HTTP_404_NOT_FOUND,
        )
