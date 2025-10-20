# ABOUTME: People API endpoints
# ABOUTME: CRUD and search operations for people

from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Optional
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from api.models.person import (
    PersonResponse, PersonListResponse, PersonCreate, PersonUpdate,
    PersonSearchFilters
)
from api.models.common import PaginatedResponse, PaginationMeta, SuccessResponse
from api.dependencies import get_db, get_pagination_params, PaginationParams, validate_uuid
from api.crud import person as person_crud


router = APIRouter(prefix="/people", tags=["people"])


@router.get("/", response_model=PaginatedResponse[PersonListResponse])
def list_people(
    company: Optional[str] = Query(None, description="Filter by company name"),
    location: Optional[str] = Query(None, description="Filter by location"),
    headline: Optional[str] = Query(None, description="Filter by headline"),
    has_email: Optional[bool] = Query(None, description="Filter by email presence"),
    has_github: Optional[bool] = Query(None, description="Filter by GitHub presence"),
    pagination: PaginationParams = Depends(get_pagination_params),
    db=Depends(get_db)
):
    """List people with optional filters"""
    filters = {
        'company': company,
        'location': location,
        'headline': headline,
        'has_email': has_email,
        'has_github': has_github
    }
    
    people, total = person_crud.get_people(
        db, 
        filters, 
        offset=pagination.offset, 
        limit=pagination.limit
    )
    
    return {
        'data': people,
        'pagination': {
            'offset': pagination.offset,
            'limit': pagination.limit,
            'total': total
        }
    }


@router.get("/{person_id}", response_model=PersonResponse)
def get_person(person_id: str, db=Depends(get_db)):
    """Get a person by ID"""
    try:
        validate_uuid(person_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    person = person_crud.get_person(db, person_id)
    
    if not person:
        raise HTTPException(status_code=404, detail="Person not found")
    
    return person


@router.post("/", response_model=PersonResponse, status_code=201)
def create_person(person_data: PersonCreate, db=Depends(get_db)):
    """Create a new person"""
    try:
        person_id = person_crud.create_person(db, person_data.model_dump())
        created_person = person_crud.get_person(db, person_id)
        return created_person
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to create person: {str(e)}")


@router.put("/{person_id}", response_model=PersonResponse)
def update_person(person_id: str, person_data: PersonUpdate, db=Depends(get_db)):
    """Update a person"""
    try:
        validate_uuid(person_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    # Check if person exists
    existing = person_crud.get_person(db, person_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Person not found")
    
    # Update
    updated = person_crud.update_person(db, person_id, person_data.model_dump(exclude_unset=True))
    
    if not updated:
        raise HTTPException(status_code=400, detail="No fields to update")
    
    # Return updated person
    return person_crud.get_person(db, person_id)


@router.delete("/{person_id}", response_model=SuccessResponse)
def delete_person(person_id: str, db=Depends(get_db)):
    """Delete a person"""
    try:
        validate_uuid(person_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    deleted = person_crud.delete_person(db, person_id)
    
    if not deleted:
        raise HTTPException(status_code=404, detail="Person not found")
    
    return {
        'success': True,
        'message': f'Person {person_id} deleted successfully'
    }


@router.get("/search/company", response_model=PaginatedResponse[PersonListResponse])
def search_by_company(
    company_name: str = Query(..., description="Company name to search for"),
    pagination: PaginationParams = Depends(get_pagination_params),
    db=Depends(get_db)
):
    """Search people by company name"""
    people, total = person_crud.search_people_by_company(
        db,
        company_name,
        offset=pagination.offset,
        limit=pagination.limit
    )
    
    return {
        'data': people,
        'pagination': {
            'offset': pagination.offset,
            'limit': pagination.limit,
            'total': total
        }
    }


@router.get("/search/location", response_model=PaginatedResponse[PersonListResponse])
def search_by_location(
    location: str = Query(..., description="Location to search for"),
    pagination: PaginationParams = Depends(get_pagination_params),
    db=Depends(get_db)
):
    """Search people by location"""
    people, total = person_crud.search_people_by_location(
        db,
        location,
        offset=pagination.offset,
        limit=pagination.limit
    )
    
    return {
        'data': people,
        'pagination': {
            'offset': pagination.offset,
            'limit': pagination.limit,
            'total': total
        }
    }

