# ABOUTME: Analytics API endpoints
# ABOUTME: Data visualization and analytics queries

from fastapi import APIRouter, Depends, Query
from typing import Optional
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from api.dependencies import get_db, validate_uuid
from api.crud import analytics as analytics_crud


router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/top-repositories")
def get_top_repositories(
    company_id: Optional[str] = Query(None, description="Filter by company ID"),
    limit: int = Query(20, ge=1, le=100, description="Number of repositories to return"),
    db=Depends(get_db)
):
    """Get top repositories by contribution count"""
    if company_id:
        try:
            validate_uuid(company_id)
        except ValueError as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    repos = analytics_crud.get_top_repositories(db, company_id=company_id, limit=limit)
    
    return {
        'success': True,
        'data': repos,
        'count': len(repos)
    }


@router.get("/top-contributors")
def get_top_contributors(
    company_id: Optional[str] = Query(None, description="Filter by company ID"),
    repo_id: Optional[str] = Query(None, description="Filter by repository ID"),
    limit: int = Query(50, ge=1, le=200, description="Number of contributors to return"),
    db=Depends(get_db)
):
    """Get top contributors by commit count"""
    if company_id:
        try:
            validate_uuid(company_id)
        except ValueError as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    if repo_id:
        try:
            validate_uuid(repo_id)
        except ValueError as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    contributors = analytics_crud.get_top_contributors(
        db, 
        company_id=company_id,
        repo_id=repo_id,
        limit=limit
    )
    
    return {
        'success': True,
        'data': contributors,
        'count': len(contributors)
    }


@router.get("/technology-distribution")
def get_technology_distribution(
    company_id: Optional[str] = Query(None, description="Filter by company ID"),
    db=Depends(get_db)
):
    """Get technology/language distribution across repositories"""
    if company_id:
        try:
            validate_uuid(company_id)
        except ValueError as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    tech_dist = analytics_crud.get_technology_distribution(db, company_id=company_id)
    
    return {
        'success': True,
        'data': tech_dist,
        'count': len(tech_dist)
    }


@router.get("/developer-activity-summary")
def get_developer_activity_summary(
    company_id: Optional[str] = Query(None, description="Filter by company ID"),
    person_id: Optional[str] = Query(None, description="Filter by person ID"),
    db=Depends(get_db)
):
    """Get aggregated developer activity statistics"""
    if company_id:
        try:
            validate_uuid(company_id)
        except ValueError as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    if person_id:
        try:
            validate_uuid(person_id)
        except ValueError as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    summary = analytics_crud.get_developer_activity_summary(
        db,
        company_id=company_id,
        person_id=person_id
    )
    
    return {
        'success': True,
        'data': summary
    }


@router.get("/companies")
def get_companies_for_filter(
    limit: int = Query(100, ge=1, le=500, description="Number of companies to return"),
    db=Depends(get_db)
):
    """Get list of companies for filter dropdowns"""
    companies = analytics_crud.get_company_list(db, limit=limit)
    
    return {
        'success': True,
        'data': companies,
        'count': len(companies)
    }

