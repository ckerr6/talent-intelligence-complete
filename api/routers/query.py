# ABOUTME: Complex query API endpoints
# ABOUTME: Multi-criteria search and advanced filtering

from fastapi import APIRouter, Depends, Query
from typing import Optional
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from api.models.common import PaginatedResponse
from api.dependencies import get_db, get_pagination_params, PaginationParams
from api.crud import graph as graph_crud


router = APIRouter(prefix="/query", tags=["query"])


@router.get("/search")
def complex_search(
    company: Optional[str] = Query(None, description="Company name (partial match)"),
    location: Optional[str] = Query(None, description="Location (partial match)"),
    headline_keyword: Optional[str] = Query(None, description="Keyword in headline"),
    has_email: Optional[bool] = Query(None, description="Filter by email presence"),
    has_github: Optional[bool] = Query(None, description="Filter by GitHub profile presence"),
    start_date: Optional[str] = Query(None, description="Employment start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="Employment end date (YYYY-MM-DD)"),
    pagination: PaginationParams = Depends(get_pagination_params),
    db=Depends(get_db)
):
    """
    Complex search across multiple criteria.
    All filters are optional and combined with AND logic.
    """
    results, total = graph_crud.search_by_multiple_criteria(
        db,
        company=company,
        location=location,
        has_email=has_email,
        has_github=has_github,
        headline_keyword=headline_keyword,
        start_date=start_date,
        end_date=end_date,
        limit=pagination.limit,
        offset=pagination.offset
    )
    
    return {
        'success': True,
        'filters': {
            'company': company,
            'location': location,
            'headline_keyword': headline_keyword,
            'has_email': has_email,
            'has_github': has_github,
            'start_date': start_date,
            'end_date': end_date
        },
        'data': results,
        'pagination': {
            'offset': pagination.offset,
            'limit': pagination.limit,
            'total': total
        }
    }

