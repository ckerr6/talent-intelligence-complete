# ABOUTME: Statistics API endpoints
# ABOUTME: Database overview, quality metrics, and coverage statistics

from fastapi import APIRouter, Depends
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from api.dependencies import get_db


router = APIRouter(prefix="/stats", tags=["statistics"])


@router.get("/overview")
def get_overview(db=Depends(get_db)):
    """Get database overview statistics (using fast table stats for demo)"""
    cursor = db.cursor()
    
    # Use PostgreSQL table statistics for instant results (good enough for demo)
    cursor.execute("""
        SELECT 
            schemaname,
            relname,
            n_live_tup as count
        FROM pg_stat_user_tables
        WHERE relname IN ('person', 'company', 'employment', 'person_email', 'github_profile')
    """)
    
    stats = {row['relname']: row['count'] for row in cursor.fetchall()}
    
    people_count = stats.get('person', 0)
    companies_count = stats.get('company', 0)
    employment_count = stats.get('employment', 0)
    emails_count = stats.get('person_email', 0)
    github_count = stats.get('github_profile', 0)
    
    return {
        'totals': {
            'people': people_count,
            'companies': companies_count,
            'employment_records': employment_count,
            'emails': emails_count,
            'github_profiles': github_count
        }
    }


@router.get("/quality")
def get_quality_metrics(db=Depends(get_db)):
    """Get data quality metrics"""
    cursor = db.cursor()
    
    # Get total people
    cursor.execute("SELECT COUNT(*) as count FROM person")
    total_people = cursor.fetchone()['count']
    
    if total_people == 0:
        return {'error': 'No people in database'}
    
    # LinkedIn coverage
    cursor.execute("""
        SELECT COUNT(*) as count FROM person
        WHERE normalized_linkedin_url IS NOT NULL
        AND normalized_linkedin_url != ''
    """)
    with_linkedin = cursor.fetchone()['count']
    
    # Email coverage
    cursor.execute("SELECT COUNT(DISTINCT person_id) as count FROM person_email")
    with_email = cursor.fetchone()['count']
    
    # GitHub coverage
    cursor.execute("SELECT COUNT(DISTINCT person_id) as count FROM github_profile")
    with_github = cursor.fetchone()['count']
    
    # Location coverage
    cursor.execute("""
        SELECT COUNT(*) as count FROM person
        WHERE location IS NOT NULL AND location != ''
    """)
    with_location = cursor.fetchone()['count']
    
    # Headline coverage
    cursor.execute("""
        SELECT COUNT(*) as count FROM person
        WHERE headline IS NOT NULL AND headline != ''
    """)
    with_headline = cursor.fetchone()['count']
    
    return {
        'total_people': total_people,
        'completeness': {
            'linkedin': {
                'count': with_linkedin,
                'percentage': round((with_linkedin / total_people) * 100, 2)
            },
            'email': {
                'count': with_email,
                'percentage': round((with_email / total_people) * 100, 2)
            },
            'github': {
                'count': with_github,
                'percentage': round((with_github / total_people) * 100, 2)
            },
            'location': {
                'count': with_location,
                'percentage': round((with_location / total_people) * 100, 2)
            },
            'headline': {
                'count': with_headline,
                'percentage': round((with_headline / total_people) * 100, 2)
            }
        }
    }


@router.get("/coverage")
def get_coverage_stats(db=Depends(get_db)):
    """Get coverage percentages"""
    cursor = db.cursor()
    
    # Get total people
    cursor.execute("SELECT COUNT(*) as count FROM person")
    total_people = cursor.fetchone()['count']
    
    if total_people == 0:
        return {'error': 'No people in database'}
    
    # Various coverage metrics
    cursor.execute("""
        SELECT 
            COUNT(DISTINCT pe.person_id) as with_email,
            COUNT(DISTINCT gp.person_id) as with_github,
            COUNT(DISTINCT e.person_id) as with_employment,
            COUNT(DISTINCT ed.person_id) as with_education
        FROM person p
        LEFT JOIN person_email pe ON p.person_id = pe.person_id
        LEFT JOIN github_profile gp ON p.person_id = gp.person_id
        LEFT JOIN employment e ON p.person_id = e.person_id
        LEFT JOIN education ed ON p.person_id = ed.person_id
    """)
    
    result = cursor.fetchone()
    
    return {
        'total_people': total_people,
        'coverage': {
            'email': {
                'count': result['with_email'],
                'percentage': round((result['with_email'] / total_people) * 100, 2)
            },
            'github': {
                'count': result['with_github'],
                'percentage': round((result['with_github'] / total_people) * 100, 2)
            },
            'employment': {
                'count': result['with_employment'],
                'percentage': round((result['with_employment'] / total_people) * 100, 2)
            },
            'education': {
                'count': result['with_education'],
                'percentage': round((result['with_education'] / total_people) * 100, 2)
            }
        }
    }

