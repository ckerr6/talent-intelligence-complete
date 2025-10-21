# ABOUTME: Graph and network relationship API endpoints
# ABOUTME: Co-employment networks, social connections, and graph analytics

from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Optional
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from api.models.common import PaginatedResponse
from api.dependencies import get_db, get_pagination_params, PaginationParams, validate_uuid
from api.crud import graph as graph_crud


router = APIRouter(prefix="/graph", tags=["graph"])


@router.get("/coworkers/{person_id}")
def get_person_coworkers(
    person_id: str,
    pagination: PaginationParams = Depends(get_pagination_params),
    db=Depends(get_db)
):
    """Get all people who worked with this person at any company"""
    try:
        validate_uuid(person_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    coworkers, total = graph_crud.get_coworkers(
        db,
        person_id,
        limit=pagination.limit,
        offset=pagination.offset
    )
    
    return {
        'data': coworkers,
        'pagination': {
            'offset': pagination.offset,
            'limit': pagination.limit,
            'total': total
        }
    }


@router.get("/company/{company_id}/network")
def get_company_coemployment_network(
    company_id: str,
    start_date: Optional[str] = Query(None, description="Filter by start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="Filter by end date (YYYY-MM-DD)"),
    limit: int = Query(500, ge=1, le=2000, description="Max nodes to return"),
    db=Depends(get_db)
):
    """
    Get the co-employment network for a specific company.
    Returns nodes (people) and edges (co-employment relationships).
    Optionally filter by date range.
    """
    try:
        validate_uuid(company_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    network = graph_crud.get_company_network(
        db,
        company_id,
        start_date=start_date,
        end_date=end_date,
        limit=limit
    )
    
    return {
        'success': True,
        'company_id': company_id,
        'filters': {
            'start_date': start_date,
            'end_date': end_date
        },
        **network
    }


@router.get("/stats")
def get_graph_statistics(db=Depends(get_db)):
    """Get overall graph statistics"""
    stats = graph_crud.get_graph_stats(db)
    
    return {
        'success': True,
        'statistics': stats
    }


@router.get("/top-connected")
def get_most_connected_people(
    limit: int = Query(10, ge=1, le=100, description="Number of people to return"),
    db=Depends(get_db)
):
    """Get the most connected people in the network"""
    people = graph_crud.get_top_connected_people(db, limit=limit)
    
    return {
        'success': True,
        'count': len(people),
        'data': people
    }

