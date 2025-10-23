"""
Market Intelligence API endpoints

Provides insights about hiring patterns, talent flow, and market trends.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from typing import Optional
import logging

from api.dependencies import get_db
from api.services.market_intelligence import MarketIntelligenceService
from api.services.cache_service import get_cache

router = APIRouter(prefix="/api/market", tags=["market-intelligence"])
logger = logging.getLogger(__name__)


# Request/Response Models
class MarketQuestionRequest(BaseModel):
    """Request for natural language market intelligence questions."""
    question: str = Field(..., description="Natural language question about market intelligence")
    company_id: Optional[str] = Field(None, description="Optional company ID for context")
    company_name: Optional[str] = Field(None, description="Optional company name for context")
    provider: str = Field("openai", description="AI provider: 'openai' or 'anthropic'")


@router.get("/hiring-patterns")
async def get_hiring_patterns(
    company_id: Optional[str] = Query(None, description="Company UUID"),
    company_name: Optional[str] = Query(None, description="Company name (fuzzy match)"),
    time_period_months: int = Query(24, ge=1, le=120, description="Time period in months"),
    db=Depends(get_db)
):
    """
    Get hiring patterns for a company - CACHED
    
    Returns:
    - Hiring volume over time (monthly breakdown)
    - Most common roles hired
    - Total hires in period
    - Average tenure
    
    Results cached for 30 minutes
    Example: /api/market/hiring-patterns?company_name=Uniswap&time_period_months=24
    """
    # Build cache key
    cache = get_cache()
    cache_key = f"hiring_patterns:{company_id or company_name}:{time_period_months}"
    
    # Try cache first
    cached_result = cache.get(cache_key)
    if cached_result:
        logger.info(f"✨ Cache hit: hiring_patterns for {company_id or company_name}")
        return cached_result
    
    logger.info(f"🔄 Cache miss: hiring_patterns for {company_id or company_name}")
    
    try:
        service = MarketIntelligenceService(db)
        patterns = service.get_hiring_patterns(
            company_id=company_id,
            company_name=company_name,
            time_period_months=time_period_months
        )
        
        if "error" in patterns:
            raise HTTPException(status_code=404, detail=patterns["error"])
        
        result = {
            "success": True,
            "data": patterns
        }
        
        # Cache for 30 minutes (1800 seconds)
        cache.set(cache_key, result, ttl=1800)
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting hiring patterns: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/talent-flow")
async def get_talent_flow(
    company_id: Optional[str] = Query(None, description="Company UUID"),
    company_name: Optional[str] = Query(None, description="Company name (fuzzy match)"),
    direction: str = Query("both", description="Flow direction: 'inbound', 'outbound', or 'both'"),
    db=Depends(get_db)
):
    """
    Get talent flow analysis for a company.
    
    Returns:
    - Feeder companies (where hires come from) if inbound/both
    - Destination companies (where people go) if outbound/both
    - Person counts for each flow
    
    Example: /api/market/talent-flow?company_name=Coinbase&direction=inbound
    """
    try:
        if direction not in ["inbound", "outbound", "both"]:
            raise HTTPException(
                status_code=400,
                detail="direction must be 'inbound', 'outbound', or 'both'"
            )
        
        service = MarketIntelligenceService(db)
        flow = service.get_talent_flow(
            company_id=company_id,
            company_name=company_name,
            direction=direction
        )
        
        if "error" in flow:
            raise HTTPException(status_code=404, detail=flow["error"])
        
        return {
            "success": True,
            "data": flow
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting talent flow: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/technology-distribution")
async def get_technology_distribution(
    company_id: Optional[str] = Query(None, description="Company UUID"),
    company_name: Optional[str] = Query(None, description="Company name (fuzzy match)"),
    limit: int = Query(20, ge=1, le=50, description="Max number of technologies to return"),
    db=Depends(get_db)
):
    """
    Get technology/language distribution at a company.
    
    Based on GitHub activity of employees.
    
    Returns:
    - Languages used
    - Number of developers using each
    - Total contributions
    - Repository count
    
    Example: /api/market/technology-distribution?company_name=Uniswap&limit=10
    """
    try:
        service = MarketIntelligenceService(db)
        tech_dist = service.get_technology_distribution(
            company_id=company_id,
            company_name=company_name,
            limit=limit
        )
        
        if "error" in tech_dist:
            raise HTTPException(status_code=404, detail=tech_dist["error"])
        
        return {
            "success": True,
            "data": tech_dist
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting technology distribution: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/ask")
async def ask_market_question(
    request: MarketQuestionRequest,
    db=Depends(get_db)
):
    """
    Ask a natural language question about market intelligence.
    
    Uses AI to analyze data and provide strategic insights.
    
    Example questions:
    - "What are the hiring trends at Uniswap?"
    - "Where does Coinbase get most of its engineers from?"
    - "What technologies are popular at DeFi companies?"
    - "How does talent flow between Uniswap and Coinbase?"
    - "What roles is Paradigm hiring for?"
    
    The AI will analyze hiring patterns, talent flow, and technology data
    to provide strategic insights for recruiting.
    """
    try:
        service = MarketIntelligenceService(db)
        result = service.ask_market_intelligence(
            question=request.question,
            company_id=request.company_id,
            company_name=request.company_name,
            provider=request.provider
        )
        
        return {
            "success": True,
            **result
        }
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error answering market question: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/companies/search")
async def search_companies(
    query: str = Query(..., min_length=1, description="Company name search query"),
    limit: int = Query(20, ge=1, le=100, description="Max number of results"),
    db=Depends(get_db)
):
    """
    Search for companies by name.
    
    Helper endpoint for autocomplete/search in market intelligence queries.
    """
    try:
        from psycopg2.extras import RealDictCursor
        cursor = db.cursor(cursor_factory=RealDictCursor)
        
        cursor.execute(
            """
            SELECT 
                company_id,
                company_name,
                (SELECT COUNT(*) FROM employment WHERE company_id = c.company_id) as employee_count
            FROM company c
            WHERE company_name ILIKE %s
            ORDER BY employee_count DESC, company_name
            LIMIT %s
            """,
            (f"%{query}%", limit)
        )
        
        companies = cursor.fetchall()
        cursor.close()
        
        return {
            "success": True,
            "companies": [
                {
                    "company_id": str(c['company_id']),
                    "company_name": c['company_name'],
                    "employee_count": c['employee_count']
                }
                for c in companies
            ]
        }
        
    except Exception as e:
        logger.error(f"Error searching companies: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/overall/statistics")
async def get_overall_statistics(db=Depends(get_db)):
    """
    Get overall dataset statistics - CACHED
    
    Returns comprehensive metrics about the entire talent pool:
    - Total people, companies, repositories
    - GitHub and email coverage
    - Overall dataset health
    
    Results cached for 1 hour
    """
    cache = get_cache()
    cache_key = "overall_statistics"
    
    cached_result = cache.get(cache_key)
    if cached_result:
        logger.info("✨ Cache hit: overall_statistics")
        return cached_result
    
    logger.info("🔄 Cache miss: overall_statistics")
    
    try:
        service = MarketIntelligenceService(db)
        stats = service.get_overall_statistics()
        
        result = {
            "success": True,
            "data": stats.get("data", {})
        }
        
        # Cache for 1 hour (3600 seconds)
        cache.set(cache_key, result, ttl=3600)
        
        return result
        
    except Exception as e:
        logger.error(f"Error getting overall statistics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/overall/hiring-trends")
async def get_overall_hiring_trends(
    months: int = Query(24, ge=1, le=60, description="Time period in months"),
    db=Depends(get_db)
):
    """
    Get overall hiring trends across all companies - CACHED
    
    Returns monthly hiring volume for the entire market.
    Results cached for 30 minutes.
    """
    cache = get_cache()
    cache_key = f"overall_hiring_trends:{months}"
    
    cached_result = cache.get(cache_key)
    if cached_result:
        logger.info(f"✨ Cache hit: overall_hiring_trends:{months}")
        return cached_result
    
    logger.info(f"🔄 Cache miss: overall_hiring_trends:{months}")
    
    try:
        service = MarketIntelligenceService(db)
        trends = service.get_overall_hiring_trends(months=months)
        
        result = {
            "success": True,
            "data": trends
        }
        
        # Cache for 30 minutes (1800 seconds)
        cache.set(cache_key, result, ttl=1800)
        
        return result
        
    except Exception as e:
        logger.error(f"Error getting overall hiring trends: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/overall/technology-distribution")
async def get_overall_technology_distribution(
    limit: int = Query(20, ge=5, le=50, description="Number of languages to return"),
    db=Depends(get_db)
):
    """
    Get overall technology distribution - CACHED
    
    Returns most popular languages across entire dataset.
    Results cached for 1 hour.
    """
    cache = get_cache()
    cache_key = f"overall_tech_distribution:{limit}"
    
    cached_result = cache.get(cache_key)
    if cached_result:
        logger.info(f"✨ Cache hit: overall_tech_distribution:{limit}")
        return cached_result
    
    logger.info(f"🔄 Cache miss: overall_tech_distribution:{limit}")
    
    try:
        service = MarketIntelligenceService(db)
        tech = service.get_overall_technology_distribution(limit=limit)
        
        result = {
            "success": True,
            "data": tech
        }
        
        # Cache for 1 hour (3600 seconds)
        cache.set(cache_key, result, ttl=3600)
        
        return result
        
    except Exception as e:
        logger.error(f"Error getting technology distribution: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/overall/top-companies")
async def get_top_companies(
    limit: int = Query(20, ge=5, le=100, description="Number of companies to return"),
    db=Depends(get_db)
):
    """
    Get top companies by headcount - CACHED
    
    Returns companies ranked by number of people in dataset.
    Results cached for 1 hour.
    """
    cache = get_cache()
    cache_key = f"top_companies:{limit}"
    
    cached_result = cache.get(cache_key)
    if cached_result:
        logger.info(f"✨ Cache hit: top_companies:{limit}")
        return cached_result
    
    logger.info(f"🔄 Cache miss: top_companies:{limit}")
    
    try:
        service = MarketIntelligenceService(db)
        companies = service.get_top_companies(limit=limit)
        
        result = {
            "success": True,
            "data": companies
        }
        
        # Cache for 1 hour (3600 seconds)
        cache.set(cache_key, result, ttl=3600)
        
        return result
        
    except Exception as e:
        logger.error(f"Error getting top companies: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/overall/location-distribution")
async def get_location_distribution(
    limit: int = Query(15, ge=5, le=50, description="Number of locations to return"),
    db=Depends(get_db)
):
    """
    Get geographic distribution of talent - CACHED
    
    Returns top locations by talent concentration.
    Results cached for 1 hour.
    """
    cache = get_cache()
    cache_key = f"location_distribution:{limit}"
    
    cached_result = cache.get(cache_key)
    if cached_result:
        logger.info(f"✨ Cache hit: location_distribution:{limit}")
        return cached_result
    
    logger.info(f"🔄 Cache miss: location_distribution:{limit}")
    
    try:
        service = MarketIntelligenceService(db)
        locations = service.get_location_distribution(limit=limit)
        
        result = {
            "success": True,
            "data": locations
        }
        
        # Cache for 1 hour (3600 seconds)
        cache.set(cache_key, result, ttl=3600)
        
        return result
        
    except Exception as e:
        logger.error(f"Error getting location distribution: {e}")
        raise HTTPException(status_code=500, detail=str(e))

