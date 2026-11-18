"""Repository for Category and Product persistence."""

import uuid
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.product import Category, Product
from app.schemas.product import ProductSort


class ProductRepository:
    """Encapsulates database access for categories and products."""

    def __init__(self, db: Session) -> None:
        self.db = db

    # ----- categories -----
    def list_categories(self) -> list[Category]:
        return list(self.db.scalars(select(Category).order_by(Category.name)))

    def get_category(self, category_id: uuid.UUID) -> Category | None:
        return self.db.get(Category, category_id)

    def get_category_by_slug(self, slug: str) -> Category | None:
        return self.db.scalar(select(Category).where(Category.slug == slug))

    def get_category_by_name(self, name: str) -> Category | None:
        return self.db.scalar(select(Category).where(Category.name == name))

    def create_category(self, *, name: str, slug: str, description: str | None) -> Category:
        category = Category(name=name, slug=slug, description=description)
        self.db.add(category)
        self.db.commit()
        self.db.refresh(category)
        return category

    # ----- products -----
    def get_product(self, product_id: uuid.UUID) -> Product | None:
        return self.db.get(Product, product_id)

    def get_product_by_sku(self, sku: str) -> Product | None:
        return self.db.scalar(select(Product).where(Product.sku == sku))

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
        only_active: bool = True,
    ) -> tuple[list[Product], int]:
        conditions = []
        if only_active:
            conditions.append(Product.is_active.is_(True))
        if search:
            conditions.append(Product.name.ilike(f"%{search}%"))
        if category_id is not None:
            conditions.append(Product.category_id == category_id)
        if min_price is not None:
            conditions.append(Product.price >= min_price)
        if max_price is not None:
            conditions.append(Product.price <= max_price)

        total = self.db.scalar(select(func.count()).select_from(Product).where(*conditions)) or 0

        order_by = {
            ProductSort.PRICE_ASC: (Product.price.asc(), Product.id.asc()),
            ProductSort.PRICE_DESC: (Product.price.desc(), Product.id.asc()),
            ProductSort.NEWEST: (Product.created_at.desc(), Product.id.asc()),
        }[sort]

        stmt = (
            select(Product)
            .where(*conditions)
            .order_by(*order_by)
            .offset((page - 1) * limit)
            .limit(limit)
        )
        return list(self.db.scalars(stmt)), total

    def create_product(self, **fields) -> Product:
        product = Product(**fields)
        self.db.add(product)
        self.db.commit()
        self.db.refresh(product)
        return product

    def update_product(self, product: Product, **fields) -> Product:
        for key, value in fields.items():
            setattr(product, key, value)
        self.db.commit()
        self.db.refresh(product)
        return product
