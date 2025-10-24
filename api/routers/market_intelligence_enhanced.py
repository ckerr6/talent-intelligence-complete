"""
Enhanced Market Intelligence API
Interactive features: clickable technologies, 10x engineers, detailed company insights
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Optional
from psycopg2.extras import RealDictCursor
import logging

from api.dependencies import get_db

router = APIRouter(prefix="/api/market/enhanced", tags=["market-intelligence-enhanced"])
logger = logging.getLogger(__name__)


@router.get("/technology/{technology}/technologists")
async def get_technologists_by_technology(
    technology: str,
    limit: int = Query(50, ge=1, le=200),
    min_repos: int = Query(1, ge=1),
    sort_by: str = Query("quality", regex="^(quality|repos|stars|recent)$"),
    db=Depends(get_db)
):
    """
    Get top technologists for a specific technology
    
    Returns people ranked by:
    - quality: Multi-factor quality score (10x engineer algorithm)
    - repos: Number of repositories
    - stars: Total stars across repositories
    - recent: Most recent activity
    """
    
    try:
        cursor = db.cursor(cursor_factory=RealDictCursor)
        
        # Build sort clause
        if sort_by == "quality":
            sort_clause = "quality_score DESC, total_stars DESC"
        elif sort_by == "repos":
            sort_clause = "repo_count DESC, total_stars DESC"
        elif sort_by == "stars":
            sort_clause = "total_stars DESC, repo_count DESC"
        else:  # recent
            sort_clause = "most_recent_contribution DESC"
        
        query = f"""
            WITH tech_contributors AS (
                SELECT 
                    p.person_id,
                    p.full_name,
                    p.headline,
                    p.location,
                    gp.github_username,
                    COUNT(DISTINCT gr.repo_id) as repo_count,
                    SUM(gr.stars) as total_stars,
                    MAX(gc.contribution_count) as max_contributions,
                    MAX(gr.updated_at) as most_recent_contribution,
                    array_agg(gr.full_name ORDER BY gr.stars DESC) FILTER (WHERE gr.stars > 0) as top_repos
                FROM person p
                JOIN github_profile gp ON p.person_id = gp.person_id
                JOIN github_contribution gc ON gp.github_profile_id = gc.github_profile_id
                JOIN github_repository gr ON gc.repo_id = gr.repo_id
                WHERE LOWER(gr.language) = LOWER(%s)
                GROUP BY p.person_id, p.full_name, p.headline, p.location, gp.github_username
                HAVING COUNT(DISTINCT gr.repo_id) >= %s
            ),
            scored_contributors AS (
                SELECT 
                    *,
                    -- Quality score algorithm (10x engineer identification)
                    (
                        -- Repository diversity (up to 30 points)
                        LEAST(repo_count * 3, 30) +
                        -- Star impact (up to 40 points, logarithmic scale)
                        LEAST(LOG(GREATEST(total_stars, 1)) * 5, 40) +
                        -- Contribution intensity (up to 20 points)
                        LEAST(max_contributions / 10, 20) +
                        -- Recency bonus (up to 10 points)
                        CASE 
                            WHEN most_recent_contribution > CURRENT_DATE - INTERVAL '3 months' THEN 10
                            WHEN most_recent_contribution > CURRENT_DATE - INTERVAL '6 months' THEN 7
                            WHEN most_recent_contribution > CURRENT_DATE - INTERVAL '12 months' THEN 5
                            ELSE 2
                        END
                    ) as quality_score,
                    CASE
                        WHEN (
                            repo_count >= 10 AND 
                            total_stars >= 500 AND
                            most_recent_contribution > CURRENT_DATE - INTERVAL '6 months'
                        ) THEN '10x'
                        WHEN (
                            repo_count >= 5 AND 
                            total_stars >= 100 AND
                            most_recent_contribution > CURRENT_DATE - INTERVAL '12 months'
                        ) THEN '5x'
                        ELSE 'standard'
                    END as engineer_tier
                FROM tech_contributors
            )
            SELECT 
                person_id::text,
                full_name,
                headline,
                location,
                github_username,
                repo_count,
                total_stars,
                max_contributions,
                most_recent_contribution,
                top_repos,
                ROUND(quality_score::numeric, 1) as quality_score,
                engineer_tier
            FROM scored_contributors
            ORDER BY {sort_clause}
            LIMIT %s
        """
        
        cursor.execute(query, (technology, min_repos, limit))
        technologists = cursor.fetchall()
        
        # Get current employment for each person
        if technologists:
            person_ids = [t['person_id'] for t in technologists]
            cursor.execute("""
                SELECT DISTINCT ON (e.person_id)
                    e.person_id::text,
                    c.company_name,
                    e.title,
                    e.start_date
                FROM employment e
                JOIN company c ON e.company_id = c.company_id
                WHERE e.person_id = ANY(%s::uuid[])
                AND e.end_date IS NULL
                ORDER BY e.person_id, e.start_date DESC
            """, (person_ids,))
            employment_map = {row['person_id']: row for row in cursor.fetchall()}
            
            # Enrich technologists with employment data
            for tech in technologists:
                emp = employment_map.get(tech['person_id'])
                if emp:
                    tech['current_company'] = emp['company_name']
                    tech['current_title'] = emp['title']
                else:
                    tech['current_company'] = None
                    tech['current_title'] = None
        
        cursor.close()
        
        # Calculate tier distribution
        tier_counts = {'10x': 0, '5x': 0, 'standard': 0}
        for tech in technologists:
            tier_counts[tech['engineer_tier']] += 1
        
        return {
            'technology': technology,
            'total_count': len(technologists),
            'tier_distribution': tier_counts,
            'sort_by': sort_by,
            'technologists': [
                {
                    'person_id': t['person_id'],
                    'name': t['full_name'],
                    'title': t['headline'],
                    'location': t['location'],
                    'github_username': t['github_username'],
                    'current_company': t.get('current_company'),
                    'current_title': t.get('current_title'),
                    'stats': {
                        'repo_count': t['repo_count'],
                        'total_stars': t['total_stars'] or 0,
                        'max_contributions': t['max_contributions'],
                        'quality_score': float(t['quality_score']),
                    },
                    'engineer_tier': t['engineer_tier'],
                    'top_repos': (t['top_repos'] or [])[:5],
                    'most_recent_contribution': t['most_recent_contribution'].isoformat() if t['most_recent_contribution'] else None
                }
                for t in technologists
            ]
        }
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error fetching technologists: {str(e)}")


@router.get("/company/{company_id}/employees")
async def get_company_employees(
    company_id: str,
    employment_status: str = Query("all", regex="^(all|current|former)$"),
    limit: int = Query(100, ge=1, le=500),
    include_stats: bool = Query(True),
    db=Depends(get_db)
):
    """
    Get employees for a specific company with detailed information
    
    Returns:
    - Employee list with titles, tenure, GitHub activity
    - Employment dates and likelihood to move predictions
    - Average tenure calculations
    """
    
    try:
        cursor = db.cursor(cursor_factory=RealDictCursor)
        
        # Build employment filter
        if employment_status == "current":
            status_filter = "AND e.end_date IS NULL"
        elif employment_status == "former":
            status_filter = "AND e.end_date IS NOT NULL"
        else:
            status_filter = ""
        
        query = f"""
            WITH employee_data AS (
                SELECT 
                    p.person_id,
                    p.full_name,
                    p.headline,
                    p.location,
                    e.title,
                    e.start_date,
                    e.end_date,
                    EXTRACT(YEAR FROM AGE(COALESCE(e.end_date, CURRENT_DATE), e.start_date)) * 12 + 
                    EXTRACT(MONTH FROM AGE(COALESCE(e.end_date, CURRENT_DATE), e.start_date)) as tenure_months,
                    CASE WHEN e.end_date IS NULL THEN 'current' ELSE 'former' END as status,
                    gp.github_username,
                    COALESCE(github_stats.repo_count, 0) as github_repos,
                    COALESCE(github_stats.total_stars, 0) as github_stars
                FROM person p
                JOIN employment e ON p.person_id = e.person_id
                LEFT JOIN github_profile gp ON p.person_id = gp.person_id
                LEFT JOIN (
                    SELECT 
                        gp2.person_id,
                        COUNT(DISTINCT gr.repo_id) as repo_count,
                        SUM(gr.stars) as total_stars
                    FROM github_profile gp2
                    JOIN github_contribution gc ON gp2.github_profile_id = gc.github_profile_id
                    JOIN github_repository gr ON gc.repo_id = gr.repo_id
                    GROUP BY gp2.person_id
                ) github_stats ON p.person_id = github_stats.person_id
                WHERE e.company_id = %s
                {status_filter}
            ),
            employees_with_predictions AS (
                SELECT 
                    *,
                    -- Likelihood to move prediction
                    CASE
                        WHEN status = 'current' AND tenure_months >= 36 THEN 'high'
                        WHEN status = 'current' AND tenure_months >= 18 THEN 'medium'
                        WHEN status = 'current' THEN 'low'
                        ELSE NULL
                    END as move_likelihood
                FROM employee_data
            )
            SELECT *
            FROM employees_with_predictions
            ORDER BY 
                CASE WHEN status = 'current' THEN 0 ELSE 1 END,
                start_date DESC
            LIMIT %s
        """
        
        cursor.execute(query, (company_id, limit))
        employees = cursor.fetchall()
        
        # Calculate aggregate stats if requested
        stats = None
        if include_stats:
            cursor.execute("""
                SELECT 
                    COUNT(*) FILTER (WHERE end_date IS NULL) as current_count,
                    COUNT(*) FILTER (WHERE end_date IS NOT NULL) as former_count,
                    AVG(
                        EXTRACT(YEAR FROM AGE(COALESCE(end_date, CURRENT_DATE), start_date)) * 12 + 
                        EXTRACT(MONTH FROM AGE(COALESCE(end_date, CURRENT_DATE), start_date))
                    ) FILTER (WHERE end_date IS NULL) as avg_current_tenure_months,
                    AVG(
                        EXTRACT(YEAR FROM AGE(end_date, start_date)) * 12 + 
                        EXTRACT(MONTH FROM AGE(end_date, start_date))
                    ) FILTER (WHERE end_date IS NOT NULL) as avg_former_tenure_months,
                    MIN(start_date) as earliest_hire,
                    MAX(start_date) FILTER (WHERE end_date IS NULL) as most_recent_hire
                FROM employment
                WHERE company_id = %s
            """, (company_id,))
            stats = cursor.fetchone()
        
        cursor.close()
        
        return {
            'company_id': company_id,
            'employment_status': employment_status,
            'total_employees': len(employees),
            'statistics': {
                'current_employees': stats['current_count'] if stats else None,
                'former_employees': stats['former_count'] if stats else None,
                'avg_current_tenure_months': int(stats['avg_current_tenure_months']) if stats and stats['avg_current_tenure_months'] else None,
                'avg_former_tenure_months': int(stats['avg_former_tenure_months']) if stats and stats['avg_former_tenure_months'] else None,
                'earliest_hire': stats['earliest_hire'].isoformat() if stats and stats['earliest_hire'] else None,
                'most_recent_hire': stats['most_recent_hire'].isoformat() if stats and stats['most_recent_hire'] else None,
            } if stats else None,
            'employees': [
                {
                    'person_id': str(e['person_id']),
                    'name': e['full_name'],
                    'headline': e['headline'],
                    'location': e['location'],
                    'title': e['title'],
                    'start_date': e['start_date'].isoformat() if e['start_date'] else None,
                    'end_date': e['end_date'].isoformat() if e['end_date'] else None,
                    'tenure_months': int(e['tenure_months']) if e['tenure_months'] else 0,
                    'status': e['status'],
                    'move_likelihood': e['move_likelihood'],
                    'github_username': e['github_username'],
                    'github_stats': {
                        'repos': e['github_repos'],
                        'stars': e['github_stars']
                    } if e['github_username'] else None
                }
                for e in employees
            ]
        }
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error fetching company employees: {str(e)}")


@router.get("/top-engineers")
async def get_top_engineers(
    technology: Optional[str] = Query(None, description="Filter by technology"),
    tier: Optional[str] = Query(None, regex="^(10x|5x)$", description="Filter by engineer tier"),
    limit: int = Query(50, ge=1, le=200),
    db=Depends(get_db)
):
    """
    Get top engineers across the platform
    
    10x Engineers criteria:
    - 10+ repos in technology
    - 500+ total stars
    - Active in last 6 months
    
    5x Engineers criteria:
    - 5+ repos in technology
    - 100+ total stars
    - Active in last 12 months
    """
    
    try:
        cursor = db.cursor(cursor_factory=RealDictCursor)
        
        tech_filter = "WHERE LOWER(gr.language) = LOWER(%s)" if technology else ""
        params = [technology] if technology else []
        
        query = f"""
            WITH engineer_stats AS (
                SELECT 
                    p.person_id,
                    p.full_name,
                    p.headline,
                    p.location,
                    gp.github_username,
                    array_agg(DISTINCT gr.language) as technologies,
                    COUNT(DISTINCT gr.repo_id) as repo_count,
                    SUM(gr.stars) as total_stars,
                    MAX(gr.updated_at) as most_recent_activity
                FROM person p
                JOIN github_profile gp ON p.person_id = gp.person_id
                JOIN github_contribution gc ON gp.github_profile_id = gc.github_profile_id
                JOIN github_repository gr ON gc.repo_id = gr.repo_id
                {tech_filter}
                GROUP BY p.person_id, p.full_name, p.headline, p.location, gp.github_username
            ),
            classified_engineers AS (
                SELECT 
                    *,
                    CASE
                        WHEN repo_count >= 10 AND total_stars >= 500 AND 
                             most_recent_activity > CURRENT_DATE - INTERVAL '6 months' THEN '10x'
                        WHEN repo_count >= 5 AND total_stars >= 100 AND 
                             most_recent_activity > CURRENT_DATE - INTERVAL '12 months' THEN '5x'
                        ELSE 'standard'
                    END as engineer_tier
                FROM engineer_stats
            )
            SELECT 
                person_id::text,
                full_name,
                headline,
                location,
                github_username,
                technologies,
                repo_count,
                total_stars,
                most_recent_activity,
                engineer_tier
            FROM classified_engineers
            WHERE engineer_tier IN ('10x', '5x')
        """
        
        if tier:
            query += " AND engineer_tier = %s"
            params.append(tier)
        
        query += " ORDER BY total_stars DESC, repo_count DESC LIMIT %s"
        params.append(limit)
        
        cursor.execute(query, params)
        engineers = cursor.fetchall()
        
        cursor.close()
        
        return {
            'technology': technology,
            'tier_filter': tier,
            'total_count': len(engineers),
            'engineers': [
                {
                    'person_id': e['person_id'],
                    'name': e['full_name'],
                    'title': e['headline'],
                    'location': e['location'],
                    'github_username': e['github_username'],
                    'technologies': e['technologies'] or [],
                    'repo_count': e['repo_count'],
                    'total_stars': e['total_stars'] or 0,
                    'most_recent_activity': e['most_recent_activity'].isoformat() if e['most_recent_activity'] else None,
                    'engineer_tier': e['engineer_tier']
                }
                for e in engineers
            ]
        }
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error fetching top engineers: {str(e)}")

