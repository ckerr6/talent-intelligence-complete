"""
ABOUTME: Market intelligence API endpoints for ecosystem-level metrics
ABOUTME: Language leaderboards, project comparisons, trend analysis
"""

from fastapi import APIRouter, Query
from typing import Optional, List
from config import get_db_context
import json

router = APIRouter(prefix="/api/market", tags=["market"])


@router.get("/languages")
async def get_language_leaderboard(
    limit: int = Query(20, le=100),
    min_developers: int = Query(0, ge=0)
):
    """
    Get language ecosystem leaderboard.
    Shows top languages by developer count with aggregate metrics.
    """
    with get_db_context() as conn:
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT 
                language,
                developer_count,
                avg_influence,
                seniority_distribution,
                top_developers,
                last_updated
            FROM language_ecosystem_metrics
            WHERE developer_count >= %s
            ORDER BY developer_count DESC
            LIMIT %s
        """, (min_developers, limit))
        
        results = cursor.fetchall()
        
        languages = []
        for row in results:
            if isinstance(row, dict):
                languages.append({
                    'language': row['language'],
                    'developer_count': row['developer_count'],
                    'avg_influence': row['avg_influence'],
                    'seniority_distribution': row['seniority_distribution'],
                    'top_developers': row['top_developers'][:5],  # Top 5 only for API
                    'last_updated': str(row['last_updated'])
                })
            else:
                languages.append({
                    'language': row[0],
                    'developer_count': row[1],
                    'avg_influence': row[2],
                    'seniority_distribution': row[3],
                    'top_developers': row[4][:5] if row[4] else [],
                    'last_updated': str(row[5])
                })
        
        return {
            'total_languages': len(languages),
            'languages': languages
        }


@router.get("/languages/{language}")
async def get_language_details(language: str):
    """
    Get detailed information about a specific language ecosystem.
    """
    with get_db_context() as conn:
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT 
                language,
                developer_count,
                avg_influence,
                seniority_distribution,
                top_developers,
                last_updated
            FROM language_ecosystem_metrics
            WHERE LOWER(language) = LOWER(%s)
        """, (language,))
        
        result = cursor.fetchone()
        
        if not result:
            return {'error': 'Language not found'}
        
        if isinstance(result, dict):
            return {
                'language': result['language'],
                'developer_count': result['developer_count'],
                'avg_influence': result['avg_influence'],
                'seniority_distribution': result['seniority_distribution'],
                'top_developers': result['top_developers'],
                'last_updated': str(result['last_updated'])
            }
        else:
            return {
                'language': result[0],
                'developer_count': result[1],
                'avg_influence': result[2],
                'seniority_distribution': result[3],
                'top_developers': result[4],
                'last_updated': str(result[5])
            }


@router.get("/overview")
async def get_market_overview():
    """
    Get high-level market overview statistics.
    """
    with get_db_context() as conn:
        cursor = conn.cursor()
        
        # Total profiles
        cursor.execute("SELECT COUNT(*) FROM github_profile WHERE github_username IS NOT NULL")
        result = cursor.fetchone()
        total_profiles = result[0] if isinstance(result, tuple) else (result['count'] if result else 0)
        
        # Total enriched developers
        cursor.execute("SELECT COUNT(*) FROM github_intelligence")
        result = cursor.fetchone()
        total_enriched = result[0] if isinstance(result, tuple) else (result['count'] if result else 0)
        
        # Languages tracked
        cursor.execute("SELECT COUNT(*) FROM language_ecosystem_metrics")
        result = cursor.fetchone()
        languages_tracked = result[0] if isinstance(result, tuple) else (result['count'] if result else 0)
        
        # Top 5 languages
        cursor.execute("""
            SELECT language, developer_count 
            FROM language_ecosystem_metrics 
            ORDER BY developer_count DESC 
            LIMIT 5
        """)
        top_languages = cursor.fetchall()
        
        # Seniority distribution
        cursor.execute("""
            SELECT inferred_seniority, COUNT(*) 
            FROM github_intelligence 
            WHERE inferred_seniority IS NOT NULL
            GROUP BY inferred_seniority
        """)
        seniority_dist = cursor.fetchall()
        
        return {
            'total_profiles': total_profiles,
            'total_enriched': total_enriched,
            'languages_tracked': languages_tracked,
            'top_languages': [
                {'language': row[0] if isinstance(row, tuple) else row['language'], 
                 'developers': row[1] if isinstance(row, tuple) else row['developer_count']} 
                for row in top_languages
            ],
            'seniority_distribution': {
                (row[0] if isinstance(row, tuple) else row['inferred_seniority']): 
                (row[1] if isinstance(row, tuple) else row['count'])
                for row in seniority_dist
            }
        }


@router.get("/trending")
async def get_trending_languages(days: int = Query(30, le=90)):
    """
    Get trending languages (placeholder for now - will track growth over time).
    """
    # For now, return top languages by avg influence as a proxy for "hot"
    with get_db_context() as conn:
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT 
                language,
                developer_count,
                avg_influence
            FROM language_ecosystem_metrics
            WHERE developer_count > 0
            ORDER BY avg_influence DESC, developer_count DESC
            LIMIT 10
        """)
        
        results = cursor.fetchall()
        
        return {
            'trending_languages': [
                {
                    'language': row[0],
                    'developer_count': row[1],
                    'avg_influence': row[2],
                    'trend': 'hot'  # Placeholder
                }
                for row in results
            ],
            'note': 'Growth tracking will be enabled as more historical data accumulates'
        }
