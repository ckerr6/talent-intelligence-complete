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
    """Get database overview statistics"""
    cursor = db.cursor()
    
    # Get counts
    cursor.execute("SELECT COUNT(*) FROM person")
    people_count = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM company")
    companies_count = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM employment")
    employment_count = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM person_email")
    emails_count = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM github_profile")
    github_count = cursor.fetchone()[0]
    
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
    cursor.execute("SELECT COUNT(*) FROM person")
    total_people = cursor.fetchone()[0]
    
    if total_people == 0:
        return {'error': 'No people in database'}
    
    # LinkedIn coverage
    cursor.execute("""
        SELECT COUNT(*) FROM person
        WHERE normalized_linkedin_url IS NOT NULL
        AND normalized_linkedin_url != ''
    """)
    with_linkedin = cursor.fetchone()[0]
    
    # Email coverage
    cursor.execute("SELECT COUNT(DISTINCT person_id) FROM person_email")
    with_email = cursor.fetchone()[0]
    
    # GitHub coverage
    cursor.execute("SELECT COUNT(DISTINCT person_id) FROM github_profile")
    with_github = cursor.fetchone()[0]
    
    # Location coverage
    cursor.execute("""
        SELECT COUNT(*) FROM person
        WHERE location IS NOT NULL AND location != ''
    """)
    with_location = cursor.fetchone()[0]
    
    # Headline coverage
    cursor.execute("""
        SELECT COUNT(*) FROM person
        WHERE headline IS NOT NULL AND headline != ''
    """)
    with_headline = cursor.fetchone()[0]
    
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
    cursor.execute("SELECT COUNT(*) FROM person")
    total_people = cursor.fetchone()[0]
    
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
                'count': result[0],
                'percentage': round((result[0] / total_people) * 100, 2)
            },
            'github': {
                'count': result[1],
                'percentage': round((result[1] / total_people) * 100, 2)
            },
            'employment': {
                'count': result[2],
                'percentage': round((result[2] / total_people) * 100, 2)
            },
            'education': {
                'count': result[3],
                'percentage': round((result[3] / total_people) * 100, 2)
            }
        }
    }

