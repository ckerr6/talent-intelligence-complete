"""
ABOUTME: FastAPI router for GitHub intelligence endpoints.
ABOUTME: Provides REST API for accessing enriched GitHub developer intelligence.
"""

from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional, Dict, Any
from pydantic import BaseModel
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from config import get_db_context
from scripts.github_intelligence.intelligence_orchestrator import IntelligenceOrchestrator


router = APIRouter(prefix="/api/github-intelligence", tags=["github-intelligence"])


# Pydantic models
class ProfileResponse(BaseModel):
    username: str
    seniority: str
    seniority_confidence: float
    primary_languages: Dict[str, Any]
    frameworks: List[str]
    domains: List[str]
    influence_score: int
    reachability_score: int
    activity_trend: str
    organizations: List[str]


class SearchRequest(BaseModel):
    seniority_levels: Optional[List[str]] = None
    languages: Optional[List[str]] = None
    domains: Optional[List[str]] = None
    min_influence: Optional[int] = None
    min_reachability: Optional[int] = None
    limit: int = 50


@router.get("/profile/{username}", response_model=ProfileResponse)
async def get_profile(username: str):
    """
    Get enriched GitHub profile intelligence.
    """
    with get_db_context() as conn:
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT 
                gp.github_username,
                gi.inferred_seniority,
                gi.seniority_confidence,
                gi.primary_languages,
                gi.frameworks,
                gi.domains,
                gi.influence_score,
                gi.reachability_score,
                gi.activity_trend,
                gi.organization_memberships
            FROM github_profile gp
            INNER JOIN github_intelligence gi ON gp.github_profile_id = gi.github_profile_id
            WHERE gp.github_username = %s
        """, (username,))
        
        result = cursor.fetchone()
        
        if not result:
            raise HTTPException(status_code=404, detail=f"Profile not found for {username}")
        
        # Handle both dict and tuple
        if isinstance(result, dict):
            return ProfileResponse(
                username=result['github_username'],
                seniority=result['inferred_seniority'],
                seniority_confidence=result['seniority_confidence'] or 0,
                primary_languages=result['primary_languages'] or {},
                frameworks=result['frameworks'] or [],
                domains=list(result['domains'].keys()) if result['domains'] else [],
                influence_score=result['influence_score'] or 0,
                reachability_score=result['reachability_score'] or 0,
                activity_trend=result['activity_trend'] or 'Unknown',
                organizations=result['organization_memberships'] or []
            )
        else:
            return ProfileResponse(
                username=result[0],
                seniority=result[1] or 'Unknown',
                seniority_confidence=result[2] or 0,
                primary_languages=result[3] or {},
                frameworks=result[4] or [],
                domains=list(result[5].keys()) if result[5] else [],
                influence_score=result[6] or 0,
                reachability_score=result[7] or 0,
                activity_trend=result[8] or 'Unknown',
                organizations=result[9] or []
            )


@router.post("/analyze/{username}")
async def analyze_profile(username: str):
    """
    Trigger deep analysis of a GitHub profile (if not already analyzed).
    """
    orchestrator = IntelligenceOrchestrator()
    
    # Check if already enriched
    with get_db_context() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT gi.github_profile_id 
            FROM github_profile gp
            LEFT JOIN github_intelligence gi ON gp.github_profile_id = gi.github_profile_id
            WHERE gp.github_username = %s
        """, (username,))
        
        result = cursor.fetchone()
        
        if result and (result[0] if not isinstance(result, dict) else result.get('github_profile_id')):
            return {"status": "already_enriched", "username": username}
    
    # Enrich
    success = orchestrator.enrich_and_store(username)
    
    if success:
        return {"status": "success", "username": username}
    else:
        raise HTTPException(status_code=500, detail=f"Failed to analyze {username}")


@router.post("/search")
async def search_profiles(request: SearchRequest):
    """
    Advanced search for GitHub profiles.
    """
    with get_db_context() as conn:
        cursor = conn.cursor()
        
        # Build dynamic query
        conditions = []
        params = []
        
        if request.seniority_levels:
            placeholders = ','.join(['%s'] * len(request.seniority_levels))
            conditions.append(f"gi.inferred_seniority IN ({placeholders})")
            params.extend(request.seniority_levels)
        
        if request.min_influence:
            conditions.append("gi.influence_score >= %s")
            params.append(request.min_influence)
        
        if request.min_reachability:
            conditions.append("gi.reachability_score >= %s")
            params.append(request.min_reachability)
        
        if request.languages:
            for lang in request.languages:
                conditions.append("gi.primary_languages ? %s")
                params.append(lang)
        
        where_clause = " AND ".join(conditions) if conditions else "1=1"
        
        query = f"""
            SELECT 
                gp.github_username,
                gi.inferred_seniority,
                gi.influence_score,
                gi.reachability_score,
                gi.primary_languages
            FROM github_profile gp
            INNER JOIN github_intelligence gi ON gp.github_profile_id = gi.github_profile_id
            WHERE {where_clause}
            ORDER BY gi.influence_score DESC
            LIMIT %s
        """
        params.append(request.limit)
        
        cursor.execute(query, params)
        results = cursor.fetchall()
        
        profiles = []
        for row in results:
            if isinstance(row, dict):
                profiles.append({
                    'username': row['github_username'],
                    'seniority': row['inferred_seniority'],
                    'influence_score': row['influence_score'],
                    'reachability_score': row['reachability_score']
                })
            else:
                profiles.append({
                    'username': row[0],
                    'seniority': row[1],
                    'influence_score': row[2],
                    'reachability_score': row[3]
                })
        
        return {
            "total": len(profiles),
            "profiles": profiles
        }


@router.get("/stats")
async def get_stats():
    """
    Get overall statistics about enriched profiles.
    """
    with get_db_context() as conn:
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT 
                COUNT(*) as total,
                COUNT(CASE WHEN inferred_seniority = 'Principal' THEN 1 END) as principal,
                COUNT(CASE WHEN inferred_seniority = 'Staff' THEN 1 END) as staff,
                COUNT(CASE WHEN inferred_seniority = 'Senior' THEN 1 END) as senior,
                COUNT(CASE WHEN inferred_seniority = 'Mid-Level' THEN 1 END) as mid,
                COUNT(CASE WHEN inferred_seniority = 'Junior' THEN 1 END) as junior,
                AVG(influence_score) as avg_influence,
                AVG(reachability_score) as avg_reachability
            FROM github_intelligence
        """)
        
        result = cursor.fetchone()
        
        if isinstance(result, dict):
            return {
                "total_enriched": result['total'],
                "by_seniority": {
                    "Principal": result['principal'],
                    "Staff": result['staff'],
                    "Senior": result['senior'],
                    "Mid-Level": result['mid'],
                    "Junior": result['junior']
                },
                "averages": {
                    "influence_score": round(result['avg_influence'] or 0, 1),
                    "reachability_score": round(result['avg_reachability'] or 0, 1)
                }
            }
        else:
            return {
                "total_enriched": result[0],
                "by_seniority": {
                    "Principal": result[1],
                    "Staff": result[2],
                    "Senior": result[3],
                    "Mid-Level": result[4],
                    "Junior": result[5]
                },
                "averages": {
                    "influence_score": round(result[6] or 0, 1),
                    "reachability_score": round(result[7] or 0, 1)
                }
            }

