# ABOUTME: Common Pydantic models used across the API
# ABOUTME: Generic response types, pagination, and error models

from pydantic import BaseModel, Field
from typing import Optional, List, Any, Generic, TypeVar
from datetime import datetime


T = TypeVar('T')


class PaginationMeta(BaseModel):
    """Pagination metadata"""
    offset: int
    limit: int
    total: Optional[int] = None


class PaginatedResponse(BaseModel, Generic[T]):
    """Generic paginated response"""
    data: List[T]
    pagination: PaginationMeta


class SuccessResponse(BaseModel):
    """Generic success response"""
    success: bool = True
    message: str
    data: Optional[Any] = None


class ErrorResponse(BaseModel):
    """Error response"""
    success: bool = False
    error: str
    detail: Optional[str] = None
    status_code: int


class HealthResponse(BaseModel):
    """Health check response"""
    status: str
    database: str
    timestamp: datetime
    pool_health: Optional[dict] = None

