"""Common pagination and envelope schemas for AgentBreaker API."""

from typing import Generic, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


class PaginatedResponse(BaseModel, Generic[T]):
    """Standardized paginated list wrapper."""

    items: list[T]
    total: int = Field(..., description="Total available records matching query filters.")
    page: int = Field(default=1, ge=1, description="Current 1-based page number.")
    page_size: int = Field(default=50, ge=1, le=500, description="Page size limit.")


class StatusMessageResponse(BaseModel):
    """Generic operation acknowledgement response."""

    success: bool = True
    message: str
