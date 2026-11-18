"""Pydantic schemas for the health check endpoint."""

from typing import Literal

from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    """Health check response payload."""

    status: Literal["ok"] = Field(default="ok", description="Overall service status")
    database: Literal["connected"] = Field(
        default="connected",
        description="Database connectivity status",
    )
    app_name: str = Field(..., description="Configured application name")
    environment: str = Field(..., description="Current runtime environment")
