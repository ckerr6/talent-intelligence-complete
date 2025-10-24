"""
Profile Enrichment API
Triggers on-demand enrichment for GitHub profiles when viewed
"""

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from typing import Optional
import logging
from datetime import datetime, timedelta

from api.dependencies import get_db

router = APIRouter(prefix="/api/profile", tags=["profile-enrichment"])
logger = logging.getLogger(__name__)


@router.post("/{person_id}/enrich-github")
async def trigger_github_enrichment(
    person_id: str,
    background_tasks: BackgroundTasks,
    force: bool = False,
    db=Depends(get_db)
):
    """
    Trigger GitHub enrichment for a person's profile
    
    This will fetch enhanced stats (merged PRs, lines of code) from GitHub API
    Runs in background so the user doesn't wait
    
    Args:
        person_id: Person UUID
        force: Force re-enrichment even if recently enriched
    """
    try:
        cursor = db.cursor()
        
        # Get GitHub username and last enrichment time
        cursor.execute("""
            SELECT 
                gp.github_username,
                gp.enriched_at,
                gp.total_merged_prs
            FROM github_profile gp
            WHERE gp.person_id = %s::uuid
            LIMIT 1
        """, (person_id,))
        
        profile = cursor.fetchone()
        
        if not profile:
            raise HTTPException(status_code=404, detail="No GitHub profile found")
        
        github_username = profile[0]
        last_enriched = profile[1]
        
        # Check if recently enriched (within last 7 days) unless forced
        if not force and last_enriched:
            days_since_enriched = (datetime.now() - last_enriched).days
            if days_since_enriched < 7:
                return {
                    'status': 'skipped',
                    'message': f'Profile enriched {days_since_enriched} days ago',
                    'last_enriched': last_enriched.isoformat()
                }
        
        # Trigger enrichment in background
        background_tasks.add_task(
            _enrich_profile_background,
            github_username,
            person_id
        )
        
        return {
            'status': 'queued',
            'message': f'Enrichment queued for {github_username}',
            'estimated_time': '10-30 seconds'
        }
        
    except Exception as e:
        logger.error(f"Error triggering enrichment for {person_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


def _enrich_profile_background(github_username: str, person_id: str):
    """
    Background task to enrich a single profile
    """
    import os
    import psycopg2
    from api.services.github_enhanced_stats_service import GitHubStatsEnricher
    
    try:
        # Create new DB connection for background task
        conn = psycopg2.connect(
            dbname=os.environ.get('PGDATABASE', 'talent'),
            user=os.environ.get('PGUSER', 'postgres'),
            password=os.environ.get('PGPASSWORD', ''),
            host=os.environ.get('PGHOST', 'localhost'),
            port=os.environ.get('PGPORT', '5432')
        )
        
        enricher = GitHubStatsEnricher(conn)
        
        # Get profile data
        cursor = conn.cursor()
        cursor.execute("""
            SELECT 
                gp.github_profile_id,
                gp.github_username,
                gp.person_id,
                gp.total_merged_prs,
                gp.total_lines_contributed,
                p.full_name
            FROM github_profile gp
            JOIN person p ON gp.person_id = p.person_id
            WHERE gp.github_username = %s
        """, (github_username,))
        
        profile = cursor.fetchone()
        if profile:
            profile_dict = {
                'github_profile_id': profile[0],
                'github_username': profile[1],
                'person_id': profile[2],
                'total_merged_prs': profile[3],
                'total_lines_contributed': profile[4],
                'full_name': profile[5]
            }
            
            result = enricher.enrich_profile(profile_dict)
            conn.commit()
            
            logger.info(f"✅ Background enrichment completed for {github_username}: {result}")
        else:
            logger.error(f"Profile not found for {github_username}")
        
        conn.close()
        
    except Exception as e:
        logger.error(f"Background enrichment failed for {github_username}: {str(e)}")


@router.get("/{person_id}/enrichment-status")
async def get_enrichment_status(
    person_id: str,
    db=Depends(get_db)
):
    """
    Check if a profile has enhanced GitHub stats
    """
    try:
        cursor = db.cursor()
        
        cursor.execute("""
            SELECT 
                gp.github_username,
                gp.total_merged_prs,
                gp.total_lines_contributed,
                gp.total_stars_earned,
                gp.enriched_at,
                CASE 
                    WHEN gp.total_merged_prs IS NOT NULL AND gp.total_merged_prs > 0 THEN true
                    WHEN gp.enriched_at IS NOT NULL THEN true
                    ELSE false
                END as is_enriched
            FROM github_profile gp
            WHERE gp.person_id = %s::uuid
        """, (person_id,))
        
        result = cursor.fetchone()
        
        if not result:
            return {
                'has_github': False,
                'is_enriched': False
            }
        
        return {
            'has_github': True,
            'github_username': result[0],
            'is_enriched': result[5],
            'stats': {
                'merged_prs': result[1] or 0,
                'lines_contributed': result[2] or 0,
                'stars_earned': result[3] or 0
            },
            'last_enriched': result[4].isoformat() if result[4] else None
        }
        
    except Exception as e:
        logger.error(f"Error checking enrichment status: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

