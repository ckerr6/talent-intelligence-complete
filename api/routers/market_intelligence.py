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
    Get hiring patterns for a company.
    
    Returns:
    - Hiring volume over time (monthly breakdown)
    - Most common roles hired
    - Total hires in period
    - Average tenure
    
    Example: /api/market/hiring-patterns?company_name=Uniswap&time_period_months=24
    """
    try:
        service = MarketIntelligenceService(db)
        patterns = service.get_hiring_patterns(
            company_id=company_id,
            company_name=company_name,
            time_period_months=time_period_months
        )
        
        if "error" in patterns:
            raise HTTPException(status_code=404, detail=patterns["error"])
        
        return {
            "success": True,
            "data": patterns
        }
        
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

