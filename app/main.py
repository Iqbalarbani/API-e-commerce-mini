"""FastAPI application factory and entry point for Mini Shop API."""

from fastapi import FastAPI
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from app.api.auth import router as auth_router
from app.api.cart import router as cart_router
from app.api.health import router as health_router
from app.api.orders import router as orders_router
from app.api.products import router as products_router
from app.core.config import get_settings
from app.core.exceptions import register_exception_handlers
from app.core.rate_limit import limiter

settings = get_settings()


def create_application() -> FastAPI:
    """Initialize and configure the FastAPI application instance."""
    application = FastAPI(
        title=settings.APP_NAME,
        version="0.1.0",
        description="Mini Shop API - E-Commerce REST API portfolio project.",
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
    )

    application.state.limiter = limiter
    application.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

    register_exception_handlers(application)
    application.include_router(health_router)
    application.include_router(auth_router, prefix=settings.API_V1_PREFIX)
    application.include_router(products_router, prefix=settings.API_V1_PREFIX)
    application.include_router(cart_router, prefix=settings.API_V1_PREFIX)
    application.include_router(orders_router, prefix=settings.API_V1_PREFIX)

    return application


app = create_application()
