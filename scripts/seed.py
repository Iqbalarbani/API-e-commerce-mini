"""Idempotent database seeder.

Safe to run many times: each record is looked up by its unique key
(email / slug / sku) and only created when it does not exist yet.

Usage (from project root):
    python -m scripts.seed
"""

import os
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.core.security import hash_password
from app.models import Category, Product, User, UserRole

ADMIN_EMAIL = os.getenv("SEED_ADMIN_EMAIL", "admin@example.com")
ADMIN_PASSWORD = os.getenv("SEED_ADMIN_PASSWORD", "Admin12345")
CUSTOMER_EMAIL = os.getenv("SEED_CUSTOMER_EMAIL", "customer@example.com")
CUSTOMER_PASSWORD = os.getenv("SEED_CUSTOMER_PASSWORD", "Customer12345")

CATEGORIES = [
    {"name": "Elektronik", "slug": "elektronik", "description": "Gadget dan perangkat elektronik"},
    {"name": "Fashion", "slug": "fashion", "description": "Pakaian dan aksesori"},
    {"name": "Buku", "slug": "buku", "description": "Buku bacaan dan referensi"},
    {"name": "Rumah Tangga", "slug": "rumah-tangga", "description": "Perlengkapan rumah"},
]

PRODUCTS = [
    {"sku": "ELK-001", "category": "elektronik", "name": "Headphone Nirkabel",
     "description": "Headphone bluetooth dengan noise cancelling",
     "price": "750000.00", "stock": 50},
    {"sku": "ELK-002", "category": "elektronik", "name": "Power Bank 20000mAh",
     "description": "Power bank fast charging", "price": "299000.00", "stock": 120},
    {"sku": "ELK-003", "category": "elektronik", "name": "Keyboard Mekanikal",
     "description": "Keyboard mekanikal layout 75%", "price": "650000.00", "stock": 30},
    {"sku": "FSH-001", "category": "fashion", "name": "Kaos Polos Katun",
     "description": "Kaos polos bahan katun combed 30s", "price": "89000.00", "stock": 200},
    {"sku": "FSH-002", "category": "fashion", "name": "Jaket Hoodie",
     "description": "Hoodie fleece tebal", "price": "225000.00", "stock": 75},
    {"sku": "BUK-001", "category": "buku", "name": "Pemrograman Python Dasar",
     "description": "Panduan belajar Python untuk pemula", "price": "110000.00", "stock": 60},
    {"sku": "BUK-002", "category": "buku", "name": "Desain Basis Data",
     "description": "Konsep dan praktik desain database relasional",
     "price": "135000.00", "stock": 40},
    {"sku": "RMH-001", "category": "rumah-tangga", "name": "Botol Minum Stainless",
     "description": "Botol tahan panas dan dingin 750ml", "price": "95000.00", "stock": 150},
    {"sku": "RMH-002", "category": "rumah-tangga", "name": "Lampu Meja LED",
     "description": "Lampu belajar dengan 3 mode cahaya", "price": "145000.00", "stock": 5},
]


def get_or_create_user(
    db: Session, *, email: str, password: str, full_name: str, role: UserRole
) -> tuple[User, bool]:
    user = db.scalar(select(User).where(User.email == email))
    if user is not None:
        return user, False
    user = User(
        email=email,
        hashed_password=hash_password(password),
        full_name=full_name,
        role=role,
        is_active=True,
    )
    db.add(user)
    db.flush()
    return user, True


def get_or_create_category(db: Session, data: dict) -> tuple[Category, bool]:
    category = db.scalar(select(Category).where(Category.slug == data["slug"]))
    if category is not None:
        return category, False
    category = Category(**data)
    db.add(category)
    db.flush()
    return category, True


def get_or_create_product(
    db: Session, data: dict, categories: dict[str, Category]
) -> tuple[Product, bool]:
    product = db.scalar(select(Product).where(Product.sku == data["sku"]))
    if product is not None:
        return product, False
    product = Product(
        sku=data["sku"],
        category_id=categories[data["category"]].id,
        name=data["name"],
        description=data["description"],
        price=Decimal(data["price"]),
        stock_quantity=data["stock"],
        is_active=True,
    )
    db.add(product)
    db.flush()
    return product, True


def seed(db: Session) -> dict[str, int]:
    """Insert missing seed data and return how many rows were created per entity."""
    created = {"users": 0, "categories": 0, "products": 0}

    for kwargs in (
        {"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD,
         "full_name": "Administrator", "role": UserRole.ADMIN},
        {"email": CUSTOMER_EMAIL, "password": CUSTOMER_PASSWORD,
         "full_name": "Customer Demo", "role": UserRole.CUSTOMER},
    ):
        _, was_created = get_or_create_user(db, **kwargs)
        created["users"] += int(was_created)

    categories: dict[str, Category] = {}
    for data in CATEGORIES:
        category, was_created = get_or_create_category(db, data)
        categories[data["slug"]] = category
        created["categories"] += int(was_created)

    for data in PRODUCTS:
        _, was_created = get_or_create_product(db, data, categories)
        created["products"] += int(was_created)

    db.commit()
    return created


def main() -> None:
    with SessionLocal() as db:
        created = seed(db)
    print(
        "Seed selesai. Baru dibuat -> "
        f"users: {created['users']}, categories: {created['categories']}, "
        f"products: {created['products']}"
    )


if __name__ == "__main__":
    main()
