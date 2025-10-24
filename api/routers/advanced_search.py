# ABOUTME: Advanced search router with multi-criteria filtering
# ABOUTME: Endpoints for search, JD parsing, and autocomplete

from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Optional, List
import time
import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from api.models.advanced_search import (
    AdvancedSearchRequest,
    AdvancedSearchResponse,
    JobDescriptionParseRequest,
    JobDescriptionParseResponse,
    TechnologyListResponse,
    CompanyAutocompleteResponse
)
from api.dependencies import get_db
from api.services.advanced_search_service import AdvancedSearchService
from api.services.jd_parser_service import JobDescriptionParser
import psycopg2.extras

# Set up logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

router = APIRouter(prefix="/search", tags=["advanced_search"])

# Initialize services
search_service = AdvancedSearchService()
jd_parser = JobDescriptionParser()


@router.post("/advanced", response_model=AdvancedSearchResponse)
def advanced_search(
    request: AdvancedSearchRequest,
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=200),
    db=Depends(get_db)
):
    """
    Execute advanced multi-criteria candidate search
    
    Search by:
    - Technologies/programming languages
    - Current or past employers
    - Job title patterns
    - Keywords and skills
    - Location
    - Experience years
    - Email/GitHub availability
    
    Returns results with match explanations showing why each candidate was selected.
    """
    request_start = time.time()
    
    try:
        logger.info(f"Advanced search request received: offset={offset}, limit={limit}")
        
        # Execute search
        results, total_count, filters_applied = search_service.execute_search(
            db, request, offset, limit
        )
        
        # Calculate search time
        search_time_ms = (time.time() - request_start) * 1000
        
        # Build response
        response = AdvancedSearchResponse(
            success=True,
            results=results,
            pagination={
                "offset": offset,
                "limit": limit,
                "total": total_count
            },
            filters_applied=filters_applied,
            total_results=total_count,
            search_time_ms=round(search_time_ms, 2)
        )
        
        logger.info(f"✓ Search completed: {len(results)} results returned, {total_count} total matches, {search_time_ms:.2f}ms")
        
        return response
        
    except Exception as e:
        logger.error(f"Advanced search error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Search failed: {str(e)}"
        )


@router.post("/parse-jd", response_model=JobDescriptionParseResponse)
def parse_job_description(
    request: JobDescriptionParseRequest,
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=200),
    db=Depends(get_db)
):
    """
    Parse a job description and optionally execute search with extracted criteria
    
    Uses AI to extract:
    - Required technologies
    - Preferred companies
    - Job level/seniority
    - Domain expertise keywords
    - Minimum experience
    - Location
    
    If auto_search=true, automatically executes search with extracted criteria.
    """
    parse_start = time.time()
    
    try:
        logger.info(f"JD parse request received: auto_search={request.auto_search}, text_length={len(request.jd_text)}")
        
        # Parse JD
        parsed_jd = jd_parser.parse_job_description(request.jd_text)
        
        parse_time_ms = (time.time() - parse_start) * 1000
        
        # Convert to search request
        search_request = jd_parser.convert_to_search_request(parsed_jd)
        
        # Execute search if requested
        search_results = None
        if request.auto_search:
            logger.info("Auto-search enabled, executing search with parsed criteria...")
            search_start = time.time()
            
            results, total_count, filters_applied = search_service.execute_search(
                db, search_request, offset, limit
            )
            
            search_time_ms = (time.time() - search_start) * 1000
            
            search_results = AdvancedSearchResponse(
                success=True,
                results=results,
                pagination={
                    "offset": offset,
                    "limit": limit,
                    "total": total_count
                },
                filters_applied=filters_applied,
                total_results=total_count,
                search_time_ms=round(search_time_ms, 2)
            )
            
            logger.info(f"✓ Auto-search completed: {len(results)} results")
        
        # Build response
        response = JobDescriptionParseResponse(
            success=True,
            parsed_jd=parsed_jd,
            search_request=search_request,
            search_results=search_results,
            parse_time_ms=round(parse_time_ms, 2)
        )
        
        total_time_ms = (time.time() - parse_start) * 1000
        logger.info(f"✓ JD parsing completed in {total_time_ms:.2f}ms total")
        
        return response
        
    except Exception as e:
        logger.error(f"JD parsing error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"JD parsing failed: {str(e)}"
        )


@router.get("/technologies", response_model=TechnologyListResponse)
def get_available_technologies(
    limit: int = Query(default=100, ge=1, le=500),
    db=Depends(get_db)
):
    """
    Get list of available technologies/programming languages in database
    
    Returns technologies ordered by number of developers using them.
    Useful for populating technology filter dropdowns.
    """
    try:
        logger.info(f"Fetching available technologies (limit={limit})...")
        
        cursor = db.cursor(cursor_factory=psycopg2.extras.DictCursor)
        
        # Get technologies with developer counts
        cursor.execute("""
            SELECT
                gr.language as name,
                COUNT(DISTINCT gp.person_id) as developer_count,
                COUNT(DISTINCT gc.repo_id) as repo_count,
                SUM(gr.stars) as total_stars
            FROM github_contribution gc
            JOIN github_profile gp ON gc.github_profile_id = gp.github_profile_id
            JOIN github_repository gr ON gc.repo_id = gr.repo_id
            WHERE gr.language IS NOT NULL
            AND gr.language != ''
            GROUP BY gr.language
            ORDER BY developer_count DESC
            LIMIT %s
        """, (limit,))
        
        technologies = []
        for row in cursor.fetchall():
            technologies.append({
                "name": row['name'],
                "developer_count": row['developer_count'],
                "repo_count": row['repo_count'],
                "total_stars": int(row['total_stars'] or 0)
            })
        
        logger.info(f"✓ Retrieved {len(technologies)} technologies")
        
        return TechnologyListResponse(
            success=True,
            technologies=technologies,
            total_technologies=len(technologies)
        )
        
    except Exception as e:
        logger.error(f"Error fetching technologies: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch technologies: {str(e)}"
        )


@router.get("/companies/autocomplete", response_model=CompanyAutocompleteResponse)
def autocomplete_companies(
    q: str = Query(..., min_length=1, description="Search query"),
    limit: int = Query(default=20, ge=1, le=100),
    db=Depends(get_db)
):
    """
    Autocomplete company names for search filters
    
    Returns companies matching the query, ordered by employee count.
    """
    try:
        logger.info(f"Company autocomplete: query='{q}', limit={limit}")
        
        cursor = db.cursor(cursor_factory=psycopg2.extras.DictCursor)
        
        # Search companies with fuzzy matching
        cursor.execute("""
            SELECT
                c.company_id::text,
                c.company_name,
                COUNT(DISTINCT e.person_id) as employee_count
            FROM company c
            LEFT JOIN employment e ON c.company_id = e.company_id
            WHERE LOWER(c.company_name) LIKE LOWER(%s)
            GROUP BY c.company_id, c.company_name
            HAVING COUNT(DISTINCT e.person_id) > 0
            ORDER BY employee_count DESC
            LIMIT %s
        """, (f"%{q}%", limit))
        
        companies = []
        for row in cursor.fetchall():
            companies.append({
                "company_id": row['company_id'],
                "company_name": row['company_name'],
                "employee_count": row['employee_count']
            })
        
        logger.info(f"✓ Found {len(companies)} matching companies")
        
        return CompanyAutocompleteResponse(
            success=True,
            companies=companies,
            total_matches=len(companies)
        )
        
    except Exception as e:
        logger.error(f"Company autocomplete error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Autocomplete failed: {str(e)}"
        )

