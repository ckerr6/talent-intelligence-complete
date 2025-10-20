# ABOUTME: FastAPI dependencies for database connections and common parameters
# ABOUTME: Provides reusable dependency injection for routes

from fastapi import Query, Depends
from typing import Optional
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))
from config import Config, get_db_context
from api.config import settings


def get_db():
    """
    Database connection dependency with automatic cleanup
    
    Usage in routes:
        @router.get("/")
        def my_route(db=Depends(get_db)):
            cursor = db.cursor()
            ...
    """
    with get_db_context() as conn:
        yield conn


class PaginationParams:
    """Pagination parameters dependency"""
    
    def __init__(
        self,
        offset: int = Query(0, ge=0, description="Number of records to skip"),
        limit: int = Query(
            settings.DEFAULT_PAGE_SIZE,
            ge=1,
            le=settings.MAX_PAGE_SIZE,
            description="Maximum number of records to return"
        )
    ):
        self.offset = offset
        self.limit = limit


def get_pagination_params(
    offset: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(
        settings.DEFAULT_PAGE_SIZE,
        ge=1,
        le=settings.MAX_PAGE_SIZE,
        description="Maximum number of records to return"
    )
) -> PaginationParams:
    """Get pagination parameters"""
    return PaginationParams(offset=offset, limit=limit)


class SearchParams:
    """Common search parameters"""
    
    def __init__(
        self,
        q: Optional[str] = Query(None, description="Search query"),
        sort_by: Optional[str] = Query(None, description="Field to sort by"),
        sort_order: str = Query("asc", regex="^(asc|desc)$", description="Sort order")
    ):
        self.q = q
        self.sort_by = sort_by
        self.sort_order = sort_order


def validate_uuid(value: str) -> str:
    """Validate UUID format"""
    import uuid
    try:
        uuid.UUID(value)
        return value
    except ValueError:
        raise ValueError(f"Invalid UUID format: {value}")

