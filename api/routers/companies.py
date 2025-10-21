# ABOUTME: Company API endpoints
# ABOUTME: CRUD and search operations for companies

from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Optional
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from api.models.company import (
    CompanyResponse, CompanyListResponse, CompanyCreate, CompanyUpdate
)
from api.models.common import PaginatedResponse, PaginationMeta, SuccessResponse
from api.dependencies import get_db, get_pagination_params, PaginationParams, validate_uuid
from api.crud import company as company_crud


router = APIRouter(prefix="/companies", tags=["companies"])


@router.get("/", response_model=PaginatedResponse[CompanyListResponse])
def list_companies(
    industry: Optional[str] = Query(None, description="Filter by industry"),
    has_website: Optional[bool] = Query(None, description="Filter by website presence"),
    min_employees: Optional[int] = Query(None, ge=0, description="Minimum employee count"),
    pagination: PaginationParams = Depends(get_pagination_params),
    db=Depends(get_db)
):
    """List companies with optional filters"""
    filters = {
        'industry': industry,
        'has_website': has_website,
        'min_employees': min_employees
    }
    
    companies, total = company_crud.get_companies(
        db,
        filters,
        offset=pagination.offset,
        limit=pagination.limit
    )
    
    return {
        'data': companies,
        'pagination': {
            'offset': pagination.offset,
            'limit': pagination.limit,
            'total': total
        }
    }


@router.get("/{company_id}", response_model=CompanyResponse)
def get_company(company_id: str, db=Depends(get_db)):
    """Get a company by ID"""
    try:
        validate_uuid(company_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    company = company_crud.get_company(db, company_id)
    
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    
    return company


@router.post("/", response_model=CompanyResponse, status_code=201)
def create_company(company_data: CompanyCreate, db=Depends(get_db)):
    """Create a new company"""
    try:
        company_id = company_crud.create_company(db, company_data.model_dump())
        created_company = company_crud.get_company(db, company_id)
        return created_company
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to create company: {str(e)}")


@router.put("/{company_id}", response_model=CompanyResponse)
def update_company(company_id: str, company_data: CompanyUpdate, db=Depends(get_db)):
    """Update a company"""
    try:
        validate_uuid(company_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    # Check if company exists
    existing = company_crud.get_company(db, company_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Company not found")
    
    # Update
    updated = company_crud.update_company(db, company_id, company_data.model_dump(exclude_unset=True))
    
    if not updated:
        raise HTTPException(status_code=400, detail="No fields to update")
    
    # Return updated company
    return company_crud.get_company(db, company_id)


@router.delete("/{company_id}", response_model=SuccessResponse)
def delete_company(company_id: str, db=Depends(get_db)):
    """Delete a company"""
    try:
        validate_uuid(company_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    try:
        deleted = company_crud.delete_company(db, company_id)
        
        if not deleted:
            raise HTTPException(status_code=404, detail="Company not found")
        
        return {
            'success': True,
            'message': f'Company {company_id} deleted successfully'
        }
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot delete company (may have associated employment records): {str(e)}"
        )


@router.get("/{company_id}/employees", response_model=PaginatedResponse[dict])
def get_company_employees(
    company_id: str,
    pagination: PaginationParams = Depends(get_pagination_params),
    db=Depends(get_db)
):
    """Get employees of a company"""
    try:
        validate_uuid(company_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    # Check if company exists
    company = company_crud.get_company(db, company_id)
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    
    employees, total = company_crud.get_company_employees(
        db,
        company_id,
        offset=pagination.offset,
        limit=pagination.limit
    )
    
    return {
        'data': employees,
        'pagination': {
            'offset': pagination.offset,
            'limit': pagination.limit,
            'total': total
        }
    }


@router.get("/{company_id}/timeline")
def get_company_hiring_timeline(company_id: str, db=Depends(get_db)):
    """Get hiring timeline for a company (employees by start date)"""
    try:
        validate_uuid(company_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    # Check if company exists
    company = company_crud.get_company(db, company_id)
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    
    timeline = company_crud.get_company_hiring_timeline(db, company_id)
    
    return {
        'success': True,
        'company_id': company_id,
        'company_name': company['company_name'],
        'timeline': timeline
    }


@router.get("/{company_id}/github/contributors")
def get_company_github_contributors(
    company_id: str,
    pagination: PaginationParams = Depends(get_pagination_params),
    db=Depends(get_db)
):
    """Get external GitHub contributors (not employees) for company repositories"""
    try:
        validate_uuid(company_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    # Check if company exists
    company = company_crud.get_company(db, company_id)
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    
    contributors, total = company_crud.get_github_contributors(
        db,
        company_id,
        limit=pagination.limit,
        offset=pagination.offset
    )
    
    return {
        'success': True,
        'company_id': company_id,
        'company_name': company['company_name'],
        'data': contributors,
        'pagination': {
            'offset': pagination.offset,
            'limit': pagination.limit,
            'total': total
        }
    }

