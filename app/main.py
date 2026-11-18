"""FastAPI application factory and entry point for Mini Shop API."""

from fastapi import FastAPI

from app.api.health import router as health_router
from app.core.config import get_settings
from app.core.exceptions import register_exception_handlers

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

    register_exception_handlers(application)
    application.include_router(health_router)

    return application


app = create_application()
