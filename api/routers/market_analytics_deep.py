# ABOUTME: Deep market analytics API endpoints for comprehensive talent intelligence
# ABOUTME: Provides ecosystem trends, skills analysis, and deep company insights

from fastapi import APIRouter, Depends, Query, HTTPException
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
import logging
from psycopg2.extras import RealDictCursor

from api.dependencies import get_db

router = APIRouter(prefix="/market/deep", tags=["market_analytics_deep"])
logger = logging.getLogger(__name__)

# ============================================================================
# HIGH-LEVEL MARKET INSIGHTS
# ============================================================================

@router.get("/ecosystem-trends")
async def get_ecosystem_trends(
    months: int = Query(12, ge=3, le=36, description="Time period in months"),
    limit: int = Query(10, ge=5, le=50, description="Number of ecosystems to return"),
    db=Depends(get_db)
):
    """
    Analyze ecosystem growth trends - which ecosystems are hot
    
    Returns:
    - Developer count per ecosystem
    - Growth rate (new developers joining)
    - Repo activity
    - Average importance score
    """
    try:
        cursor = db.cursor(cursor_factory=RealDictCursor)
        
        cursor.execute("""
            SELECT 
                ce.ecosystem_name,
                COUNT(DISTINCT pea.person_id) as developer_count,
                (SELECT AVG(importance_score) 
                 FROM github_profile gp 
                 WHERE gp.person_id IN (SELECT person_id FROM person_ecosystem_activity WHERE ecosystem_id = ce.ecosystem_id)
                ) as avg_importance,
                0 as repo_count,
                0 as recent_developers
            FROM crypto_ecosystem ce
            JOIN person_ecosystem_activity pea ON ce.ecosystem_id = pea.ecosystem_id
            WHERE ce.parent_ecosystem_id IS NULL  -- Top-level ecosystems only
            GROUP BY ce.ecosystem_id, ce.ecosystem_name
            HAVING COUNT(DISTINCT pea.person_id) > 5  -- Only ecosystems with meaningful activity
            ORDER BY developer_count DESC
            LIMIT %s
        """, (limit,))
        
        ecosystems = [dict(row) for row in cursor.fetchall()]
        
        # Calculate growth rate
        for eco in ecosystems:
            if eco['developer_count'] > 0:
                eco['growth_rate'] = (eco['recent_developers'] / eco['developer_count']) * 100
            else:
                eco['growth_rate'] = 0
        
        cursor.close()
        
        return {
            'success': True,
            'data': {
                'ecosystems': ecosystems,
                'analysis_period_months': months,
                'total_ecosystems_analyzed': len(ecosystems)
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting ecosystem trends: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/skills-demand")
async def get_skills_demand(
    months: int = Query(6, ge=3, le=24, description="Time period for trend analysis"),
    limit: int = Query(20, ge=10, le=50),
    db=Depends(get_db)
):
    """
    Analyze skills demand across the talent market
    
    Returns:
    - Most in-demand skills
    - Skill rarity (supply/demand)
    - Average importance of developers with each skill
    - Growth trends
    """
    try:
        cursor = db.cursor(cursor_factory=RealDictCursor)
        
        cursor.execute("""
            SELECT 
                s.skill_name,
                s.category,
                COUNT(DISTINCT ps.person_id) as developer_count,
                AVG(gp.importance_score) as avg_developer_importance,
                -- Skill rarity: fewer people = more rare
                (100.0 / NULLIF(COUNT(DISTINCT ps.person_id), 0)) as rarity_score,
                -- Recent adoption
                COUNT(DISTINCT CASE 
                    WHEN ps.created_at >= NOW() - INTERVAL '%s months'
                    THEN ps.person_id 
                END) as recent_adopters,
                -- GitHub activity with this skill
                SUM(CASE WHEN ps.source = 'repository' THEN 1 ELSE 0 END) as from_github_repos,
                SUM(CASE WHEN ps.source = 'title' THEN 1 ELSE 0 END) as from_titles
            FROM skills s
            JOIN person_skills ps ON s.skill_id = ps.skill_id
            LEFT JOIN github_profile gp ON ps.person_id = gp.person_id
            GROUP BY s.skill_id, s.skill_name, s.category
            HAVING COUNT(DISTINCT ps.person_id) >= 10  -- Filter noise
            ORDER BY developer_count DESC
            LIMIT %s
        """, (months, limit))
        
        skills = [dict(row) for row in cursor.fetchall()]
        
        # Calculate demand score (combination of count and importance)
        for skill in skills:
            demand_score = (
                (skill['developer_count'] / 1000) * 50 +  # Volume component
                (skill['avg_developer_importance'] or 0) * 0.5  # Quality component
            )
            skill['demand_score'] = min(demand_score, 100)  # Cap at 100
        
        # Re-sort by demand score
        skills.sort(key=lambda x: x['demand_score'], reverse=True)
        
        cursor.close()
        
        return {
            'success': True,
            'data': {
                'skills': skills,
                'analysis_period_months': months
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting skills demand: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/developer-quality-distribution")
async def get_developer_quality_distribution(db=Depends(get_db)):
    """
    Analyze distribution of developer quality (importance scores)
    
    Shows market-wide quality distribution
    """
    try:
        cursor = db.cursor(cursor_factory=RealDictCursor)
        
        cursor.execute("""
            SELECT 
                CASE 
                    WHEN importance_score >= 40 THEN 'Elite (40-100)'
                    WHEN importance_score >= 20 THEN 'Strong (20-39)'
                    WHEN importance_score >= 10 THEN 'Solid (10-19)'
                    WHEN importance_score > 0 THEN 'Standard (1-9)'
                    ELSE 'Unscored'
                END as quality_tier,
                COUNT(*) as developer_count,
                AVG(followers) as avg_followers,
                AVG(public_repos) as avg_public_repos,
                AVG(total_merged_prs) as avg_merged_prs,
                SUM(total_merged_prs) as total_merged_prs
            FROM github_profile
            GROUP BY quality_tier
            ORDER BY 
                CASE quality_tier
                    WHEN 'Elite (40-100)' THEN 1
                    WHEN 'Strong (20-39)' THEN 2
                    WHEN 'Solid (10-19)' THEN 3
                    WHEN 'Standard (1-9)' THEN 4
                    ELSE 5
                END
        """)
        
        distribution = [dict(row) for row in cursor.fetchall()]
        
        # Calculate percentages
        total = sum(d['developer_count'] for d in distribution)
        for d in distribution:
            d['percentage'] = (d['developer_count'] / total * 100) if total > 0 else 0
        
        cursor.close()
        
        return {
            'success': True,
            'data': {
                'distribution': distribution,
                'total_developers': total
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting quality distribution: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/network-density")
async def get_network_density(db=Depends(get_db)):
    """
    Analyze network connectivity and collaboration patterns
    
    Returns:
    - Total network size
    - Average connections per person
    - Network density
    - Top collaboration hubs
    """
    try:
        cursor = db.cursor(cursor_factory=RealDictCursor)
        
        # Overall network stats
        cursor.execute("""
            SELECT 
                COUNT(DISTINCT src_person_id) + COUNT(DISTINCT dst_person_id) as total_connected_people,
                COUNT(*) as total_edges,
                AVG(shared_repos) as avg_shared_repos,
                AVG(collaboration_strength) as avg_collaboration_strength
            FROM edge_github_collaboration
        """)
        
        network_stats = dict(cursor.fetchone())
        
        # Calculate avg connections per person
        if network_stats['total_connected_people'] > 0:
            network_stats['avg_connections_per_person'] = (
                network_stats['total_edges'] * 2 / network_stats['total_connected_people']
            )
        else:
            network_stats['avg_connections_per_person'] = 0
        
        # Top collaboration hubs
        cursor.execute("""
            SELECT 
                p.person_id,
                p.full_name,
                gp.github_username,
                gp.importance_score,
                COUNT(*) as connection_count,
                AVG(egc.collaboration_strength) as avg_strength
            FROM (
                SELECT src_person_id as person_id, collaboration_strength
                FROM edge_github_collaboration
                UNION ALL
                SELECT dst_person_id, collaboration_strength
                FROM edge_github_collaboration
            ) egc
            JOIN person p ON egc.person_id = p.person_id
            LEFT JOIN github_profile gp ON p.person_id = gp.person_id
            GROUP BY p.person_id, p.full_name, gp.github_username, gp.importance_score
            ORDER BY connection_count DESC
            LIMIT 20
        """)
        
        top_hubs = [dict(row) for row in cursor.fetchall()]
        
        cursor.close()
        
        return {
            'success': True,
            'data': {
                'network_stats': network_stats,
                'top_collaboration_hubs': top_hubs
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting network density: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# DEEP COMPANY ANALYTICS
# ============================================================================

@router.get("/company/{company_id}/team-composition")
async def get_company_team_composition(
    company_id: str,
    include_former: bool = Query(False, description="Include former employees"),
    db=Depends(get_db)
):
    """
    Deep analysis of company team composition
    
    Returns:
    - Current headcount
    - Skills distribution
    - Seniority levels
    - GitHub activity distribution
    - Quality tier breakdown
    """
    try:
        cursor = db.cursor(cursor_factory=RealDictCursor)
        
        # Build employment filter
        employment_filter = "AND e.end_date IS NULL" if not include_former else ""
        
        # Team size and basics
        cursor.execute(f"""
            SELECT 
                COUNT(DISTINCT e.person_id) as total_employees,
                COUNT(DISTINCT CASE WHEN e.end_date IS NULL THEN e.person_id END) as current_employees,
                COUNT(DISTINCT CASE WHEN e.end_date IS NOT NULL THEN e.person_id END) as former_employees,
                COUNT(DISTINCT gp.github_profile_id) as with_github,
                AVG(gp.importance_score) as avg_importance,
                SUM(gp.total_merged_prs) as total_merged_prs,
                COUNT(DISTINCT pe.email) as email_count
            FROM employment e
            LEFT JOIN github_profile gp ON e.person_id = gp.person_id
            LEFT JOIN person_email pe ON e.person_id = pe.person_id
            WHERE e.company_id = %s::uuid
            {employment_filter}
        """, (company_id,))
        
        team_stats = dict(cursor.fetchone())
        
        # Skills distribution
        cursor.execute(f"""
            SELECT 
                s.skill_name,
                s.category,
                COUNT(DISTINCT ps.person_id) as employee_count,
                AVG(gp.importance_score) as avg_importance
            FROM employment e
            JOIN person_skills ps ON e.person_id = ps.person_id
            JOIN skills s ON ps.skill_id = s.skill_id
            LEFT JOIN github_profile gp ON e.person_id = gp.person_id
            WHERE e.company_id = %s::uuid
            {employment_filter}
            GROUP BY s.skill_id, s.skill_name, s.category
            ORDER BY employee_count DESC
            LIMIT 20
        """, (company_id,))
        
        skills = [dict(row) for row in cursor.fetchall()]
        
        # Quality tier breakdown
        cursor.execute(f"""
            SELECT 
                CASE 
                    WHEN gp.importance_score >= 40 THEN 'Elite'
                    WHEN gp.importance_score >= 20 THEN 'Strong'
                    WHEN gp.importance_score >= 10 THEN 'Solid'
                    WHEN gp.importance_score > 0 THEN 'Standard'
                    ELSE 'No GitHub'
                END as quality_tier,
                COUNT(*) as employee_count
            FROM employment e
            LEFT JOIN github_profile gp ON e.person_id = gp.person_id
            WHERE e.company_id = %s::uuid
            {employment_filter}
            GROUP BY quality_tier
        """, (company_id,))
        
        quality_tiers = [dict(row) for row in cursor.fetchall()]
        
        # Seniority analysis (from titles)
        cursor.execute(f"""
            SELECT 
                CASE 
                    WHEN LOWER(e.title) LIKE '%vp%' OR LOWER(e.title) LIKE '%vice president%' THEN 'VP/Executive'
                    WHEN LOWER(e.title) LIKE '%director%' OR LOWER(e.title) LIKE '%head of%' THEN 'Director'
                    WHEN LOWER(e.title) LIKE '%lead%' OR LOWER(e.title) LIKE '%principal%' OR LOWER(e.title) LIKE '%staff%' THEN 'Lead/Principal'
                    WHEN LOWER(e.title) LIKE '%senior%' OR LOWER(e.title) LIKE '%sr%' THEN 'Senior'
                    WHEN LOWER(e.title) LIKE '%junior%' OR LOWER(e.title) LIKE '%jr%' THEN 'Junior'
                    ELSE 'Mid-level'
                END as seniority_level,
                COUNT(*) as employee_count,
                AVG(gp.importance_score) as avg_importance
            FROM employment e
            LEFT JOIN github_profile gp ON e.person_id = gp.person_id
            WHERE e.company_id = %s::uuid
            AND e.title IS NOT NULL
            {employment_filter}
            GROUP BY seniority_level
            ORDER BY employee_count DESC
        """, (company_id,))
        
        seniority = [dict(row) for row in cursor.fetchall()]
        
        cursor.close()
        
        return {
            'success': True,
            'data': {
                'team_stats': team_stats,
                'skills_distribution': skills,
                'quality_tiers': quality_tiers,
                'seniority_levels': seniority
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting team composition: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/company/{company_id}/github-productivity")
async def get_company_github_productivity(
    company_id: str,
    db=Depends(get_db)
):
    """
    Analyze company's GitHub productivity and code quality
    
    Returns:
    - Total contributions across all employees
    - PR merge rates
    - Repository diversity
    - Code quality indicators
    """
    try:
        cursor = db.cursor(cursor_factory=RealDictCursor)
        
        # Overall GitHub metrics
        cursor.execute("""
            SELECT 
                COUNT(DISTINCT e.person_id) as total_developers,
                COUNT(DISTINCT gp.github_profile_id) as developers_with_github,
                SUM(gp.total_merged_prs) as total_merged_prs,
                AVG(gp.total_merged_prs) as avg_merged_prs_per_dev,
                SUM(gp.total_stars_earned) as total_stars_earned,
                SUM(gp.total_contributions) as total_contributions,
                COUNT(DISTINCT gc.repo_id) as unique_repos_contributed,
                AVG(gc.contribution_quality_score) as avg_contribution_quality
            FROM employment e
            LEFT JOIN github_profile gp ON e.person_id = gp.person_id
            LEFT JOIN github_contribution gc ON gp.github_profile_id = gc.github_profile_id
            WHERE e.company_id = %s::uuid
            AND e.end_date IS NULL
        """, (company_id,))
        
        github_stats = dict(cursor.fetchone())
        
        # Top contributors from company
        cursor.execute("""
            SELECT 
                p.person_id,
                p.full_name,
                gp.github_username,
                gp.importance_score,
                gp.total_merged_prs,
                gp.total_stars_earned,
                COUNT(DISTINCT gc.repo_id) as repos_contributed
            FROM employment e
            JOIN person p ON e.person_id = p.person_id
            JOIN github_profile gp ON p.person_id = gp.person_id
            LEFT JOIN github_contribution gc ON gp.github_profile_id = gc.github_profile_id
            WHERE e.company_id = %s::uuid
            AND e.end_date IS NULL
            AND gp.total_merged_prs > 0
            GROUP BY p.person_id, p.full_name, gp.github_username, gp.importance_score, gp.total_merged_prs, gp.total_stars_earned
            ORDER BY gp.importance_score DESC NULLS LAST, gp.total_merged_prs DESC
            LIMIT 10
        """, (company_id,))
        
        top_contributors = [dict(row) for row in cursor.fetchall()]
        
        # Repository activity
        cursor.execute("""
            SELECT 
                gr.full_name,
                gr.language,
                gr.stars,
                COUNT(DISTINCT gc.github_profile_id) as company_contributors,
                SUM(gc.contribution_count) as total_contributions,
                SUM(gc.merged_pr_count) as total_merged_prs
            FROM employment e
            JOIN github_profile gp ON e.person_id = gp.person_id
            JOIN github_contribution gc ON gp.github_profile_id = gc.github_profile_id
            JOIN github_repository gr ON gc.repo_id = gr.repo_id
            WHERE e.company_id = %s::uuid
            AND e.end_date IS NULL
            GROUP BY gr.repo_id, gr.full_name, gr.language, gr.stars
            HAVING COUNT(DISTINCT gc.github_profile_id) >= 2  -- At least 2 company members
            ORDER BY company_contributors DESC, total_merged_prs DESC
            LIMIT 20
        """, (company_id,))
        
        team_repos = [dict(row) for row in cursor.fetchall()]
        
        cursor.close()
        
        return {
            'success': True,
            'data': {
                'github_stats': github_stats,
                'top_contributors': top_contributors,
                'team_repositories': team_repos
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting GitHub productivity: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/company/{company_id}/talent-flow-analysis")
async def get_company_talent_flow_analysis(
    company_id: str,
    months: int = Query(24, ge=6, le=60),
    db=Depends(get_db)
):
    """
    Deep analysis of talent acquisition and attrition patterns
    
    Returns:
    - Hiring velocity (people/month)
    - Attrition patterns
    - Source companies (where they hire from)
    - Destination companies (where people go)
    - Retention indicators
    """
    try:
        cursor = db.cursor(cursor_factory=RealDictCursor)
        
        cutoff_date = datetime.now() - timedelta(days=30*months)
        
        # Hiring trends
        cursor.execute("""
            SELECT 
                DATE_TRUNC('month', e.start_date) as month,
                COUNT(*) as hires,
                AVG(gp.importance_score) as avg_importance_of_hires
            FROM employment e
            LEFT JOIN github_profile gp ON e.person_id = gp.person_id
            WHERE e.company_id = %s::uuid
            AND e.start_date >= %s
            AND e.start_date IS NOT NULL
            GROUP BY DATE_TRUNC('month', e.start_date)
            ORDER BY month DESC
        """, (company_id, cutoff_date))
        
        hiring_trend = [dict(row) for row in cursor.fetchall()]
        
        # Attrition trends
        cursor.execute("""
            SELECT 
                DATE_TRUNC('month', e.end_date) as month,
                COUNT(*) as departures,
                AVG(gp.importance_score) as avg_importance_lost
            FROM employment e
            LEFT JOIN github_profile gp ON e.person_id = gp.person_id
            WHERE e.company_id = %s::uuid
            AND e.end_date >= %s
            AND e.end_date IS NOT NULL
            GROUP BY DATE_TRUNC('month', e.end_date)
            ORDER BY month DESC
        """, (company_id, cutoff_date))
        
        attrition_trend = [dict(row) for row in cursor.fetchall()]
        
        # Source companies (where they hire from)
        cursor.execute("""
            WITH company_hires AS (
                SELECT e1.person_id, e1.start_date
                FROM employment e1
                WHERE e1.company_id = %s::uuid
                AND e1.start_date >= %s
            )
            SELECT 
                c.company_name as source_company,
                COUNT(DISTINCT ch.person_id) as people_hired,
                AVG(gp.importance_score) as avg_importance
            FROM company_hires ch
            JOIN employment e2 ON ch.person_id = e2.person_id 
                AND e2.end_date < ch.start_date
                AND e2.end_date >= ch.start_date - INTERVAL '6 months'
            JOIN company c ON e2.company_id = c.company_id
            LEFT JOIN github_profile gp ON ch.person_id = gp.person_id
            WHERE c.company_id != %s::uuid
            GROUP BY c.company_id, c.company_name
            ORDER BY people_hired DESC
            LIMIT 15
        """, (company_id, cutoff_date, company_id))
        
        source_companies = [dict(row) for row in cursor.fetchall()]
        
        # Destination companies (where people go)
        cursor.execute("""
            WITH company_departures AS (
                SELECT e1.person_id, e1.end_date
                FROM employment e1
                WHERE e1.company_id = %s::uuid
                AND e1.end_date >= %s
                AND e1.end_date IS NOT NULL
            )
            SELECT 
                c.company_name as destination_company,
                COUNT(DISTINCT cd.person_id) as people_lost,
                AVG(gp.importance_score) as avg_importance
            FROM company_departures cd
            JOIN employment e2 ON cd.person_id = e2.person_id 
                AND e2.start_date > cd.end_date
                AND e2.start_date <= cd.end_date + INTERVAL '6 months'
            JOIN company c ON e2.company_id = c.company_id
            LEFT JOIN github_profile gp ON cd.person_id = gp.person_id
            WHERE c.company_id != %s::uuid
            GROUP BY c.company_id, c.company_name
            ORDER BY people_lost DESC
            LIMIT 15
        """, (company_id, cutoff_date, company_id))
        
        destination_companies = [dict(row) for row in cursor.fetchall()]
        
        cursor.close()
        
        # Calculate net hiring and avg tenure
        total_hires = sum(h['hires'] for h in hiring_trend)
        total_departures = sum(d['departures'] for d in attrition_trend)
        net_hiring = total_hires - total_departures
        
        return {
            'success': True,
            'data': {
                'hiring_trend': hiring_trend,
                'attrition_trend': attrition_trend,
                'source_companies': source_companies,
                'destination_companies': destination_companies,
                'summary': {
                    'total_hires': total_hires,
                    'total_departures': total_departures,
                    'net_hiring': net_hiring,
                    'analysis_period_months': months
                }
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting talent flow analysis: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/company/{company_id}/network-analysis")
async def get_company_network_analysis(
    company_id: str,
    db=Depends(get_db)
):
    """
    Analyze company's network effects and connectivity
    
    Returns:
    - Internal collaboration density
    - External connections
    - Key connectors within team
    - Network reach
    """
    try:
        cursor = db.cursor(cursor_factory=RealDictCursor)
        
        # Get current employees
        cursor.execute("""
            SELECT ARRAY_AGG(DISTINCT person_id) as employee_ids
            FROM employment
            WHERE company_id = %s::uuid
            AND end_date IS NULL
        """, (company_id,))
        
        result = cursor.fetchone()
        employee_ids = result['employee_ids'] if result and result['employee_ids'] else []
        
        if not employee_ids:
            return {
                'success': True,
                'data': {
                    'message': 'No current employees found',
                    'internal_connections': 0,
                    'external_connections': 0
                }
            }
        
        # Internal connections (within company)
        cursor.execute("""
            SELECT COUNT(*) as internal_connections
            FROM edge_github_collaboration
            WHERE src_person_id = ANY(%s::uuid[])
            AND dst_person_id = ANY(%s::uuid[])
        """, (employee_ids, employee_ids))
        
        internal = dict(cursor.fetchone())
        
        # External connections
        cursor.execute("""
            SELECT COUNT(*) as external_connections
            FROM edge_github_collaboration
            WHERE src_person_id = ANY(%s::uuid[])
            AND dst_person_id != ALL(%s::uuid[])
        """, (employee_ids, employee_ids))
        
        external = dict(cursor.fetchone())
        
        # Key connectors (employees with most connections)
        cursor.execute("""
            WITH employee_connections AS (
                SELECT src_person_id as person_id
                FROM edge_github_collaboration
                WHERE src_person_id = ANY(%s::uuid[])
                UNION ALL
                SELECT dst_person_id
                FROM edge_github_collaboration
                WHERE dst_person_id = ANY(%s::uuid[])
            )
            SELECT 
                p.person_id,
                p.full_name,
                gp.github_username,
                gp.importance_score,
                COUNT(*) as total_connections
            FROM employee_connections ec
            JOIN person p ON ec.person_id = p.person_id
            LEFT JOIN github_profile gp ON p.person_id = gp.person_id
            GROUP BY p.person_id, p.full_name, gp.github_username, gp.importance_score
            ORDER BY total_connections DESC
            LIMIT 10
        """, (employee_ids, employee_ids))
        
        key_connectors = [dict(row) for row in cursor.fetchall()]
        
        cursor.close()
        
        return {
            'success': True,
            'data': {
                'internal_connections': internal['internal_connections'],
                'external_connections': external['external_connections'],
                'key_connectors': key_connectors,
                'team_size': len(employee_ids)
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting network analysis: {e}")
        raise HTTPException(status_code=500, detail=str(e))

