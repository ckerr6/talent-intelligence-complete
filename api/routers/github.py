# ABOUTME: GitHub discovery API endpoints
# ABOUTME: Query GitHub profiles, repos, and ecosystem data

from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Optional, List, Dict, Any
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from api.dependencies import get_db, get_pagination_params, PaginationParams
from api.models.common import PaginatedResponse


router = APIRouter(prefix="/github", tags=["github"])


@router.get("/profile/{username}")
def get_github_profile(username: str, db=Depends(get_db)):
    """Get GitHub profile by username with contributions"""
    cursor = db.cursor()
    
    cursor.execute("""
        SELECT 
            github_profile_id::text,
            github_username,
            github_name,
            github_company,
            bio,
            location as github_location,
            github_email,
            blog,
            twitter_username,
            followers,
            following,
            public_repos,
            avatar_url,
            ecosystem_tags,
            importance_score,
            person_id::text,
            created_at::text as discovered_at,
            last_enriched::text
        FROM github_profile
        WHERE github_username = %s
    """, (username,))
    
    profile = cursor.fetchone()
    if not profile:
        raise HTTPException(status_code=404, detail=f"GitHub profile '{username}' not found")
    
    profile_data = dict(profile)
    
    # Get contributions
    cursor.execute("""
        SELECT 
            r.repo_id::text,
            r.full_name as repo_name,
            r.stars,
            r.language,
            r.description,
            r.ecosystem_ids,
            gc.contribution_count,
            gc.created_at::text as first_contributed
        FROM github_contribution gc
        JOIN github_repository r ON gc.repo_id = r.repo_id
        WHERE gc.github_profile_id = %s::uuid
        ORDER BY gc.contribution_count DESC
        LIMIT 100
    """, (profile_data['github_profile_id'],))
    
    profile_data['contributions'] = [dict(row) for row in cursor.fetchall()]
    
    return {
        'success': True,
        'data': profile_data
    }


@router.get("/profiles/by-ecosystem/{ecosystem}")
def get_profiles_by_ecosystem(
    ecosystem: str,
    min_followers: Optional[int] = Query(None, description="Minimum followers"),
    pagination: PaginationParams = Depends(get_pagination_params),
    db=Depends(get_db)
):
    """Get GitHub profiles tagged with a specific ecosystem"""
    cursor = db.cursor()
    
    # Build WHERE clause
    where_clauses = ["%s = ANY(ecosystem_tags)"]
    params = [ecosystem]
    
    if min_followers:
        where_clauses.append("followers >= %s")
        params.append(min_followers)
    
    where_sql = " AND ".join(where_clauses)
    
    # Count total
    cursor.execute(f"""
        SELECT COUNT(*) 
        FROM github_profile 
        WHERE {where_sql}
    """, params)
    total = cursor.fetchone()[0]
    
    # Get profiles
    cursor.execute(f"""
        SELECT 
            github_profile_id::text,
            github_username,
            github_name,
            bio,
            location,
            followers,
            public_repos,
            avatar_url,
            ecosystem_tags,
            importance_score,
            person_id::text
        FROM github_profile
        WHERE {where_sql}
        ORDER BY followers DESC NULLS LAST, importance_score DESC NULLS LAST
        LIMIT %s OFFSET %s
    """, params + [pagination.limit, pagination.offset])
    
    profiles = [dict(row) for row in cursor.fetchall()]
    
    return {
        'data': profiles,
        'pagination': {
            'offset': pagination.offset,
            'limit': pagination.limit,
            'total': total
        }
    }


@router.get("/repositories/by-ecosystem/{ecosystem}")
def get_repositories_by_ecosystem(
    ecosystem: str,
    pagination: PaginationParams = Depends(get_pagination_params),
    db=Depends(get_db)
):
    """Get repositories associated with an ecosystem
    
    Note: Currently looks for repos from contributors tagged with the ecosystem,
    since ecosystem_ids is a UUID array and ecosystem tags are text-based.
    """
    cursor = db.cursor()
    
    # Find repos contributed to by profiles in this ecosystem
    cursor.execute("""
        SELECT COUNT(DISTINCT r.repo_id)
        FROM github_repository r
        JOIN github_contribution gc ON r.repo_id = gc.repo_id
        JOIN github_profile gp ON gc.github_profile_id = gp.github_profile_id
        WHERE %s = ANY(gp.ecosystem_tags)
    """, (ecosystem,))
    total = cursor.fetchone()[0]
    
    # Get repositories
    cursor.execute("""
        SELECT 
            r.repo_id::text,
            r.full_name,
            r.description,
            r.stars,
            r.forks,
            r.language,
            r.importance_score,
            r.contributor_count,
            r.last_contributor_sync::text,
            r.created_at::text,
            r.last_updated::text,
            COUNT(DISTINCT gc.github_profile_id) as ecosystem_contributors
        FROM github_repository r
        JOIN github_contribution gc ON r.repo_id = gc.repo_id
        JOIN github_profile gp ON gc.github_profile_id = gp.github_profile_id
        WHERE %s = ANY(gp.ecosystem_tags)
        GROUP BY r.repo_id, r.full_name, r.description, r.stars, r.forks, 
                 r.language, r.importance_score, r.contributor_count, 
                 r.last_contributor_sync, r.created_at, r.last_updated
        ORDER BY r.stars DESC NULLS LAST, r.importance_score DESC NULLS LAST
        LIMIT %s OFFSET %s
    """, (ecosystem, pagination.limit, pagination.offset))
    
    repos = [dict(row) for row in cursor.fetchall()]
    
    return {
        'data': repos,
        'pagination': {
            'offset': pagination.offset,
            'limit': pagination.limit,
            'total': total
        }
    }


@router.get("/ecosystems")
def list_ecosystems(db=Depends(get_db)):
    """List all ecosystems with profile and repo counts"""
    cursor = db.cursor()
    
    # Get ecosystems from GitHub profile tags (text array)
    cursor.execute("""
        SELECT 
            unnest(ecosystem_tags) as ecosystem,
            COUNT(*) as profile_count,
            0 as repo_count
        FROM github_profile
        WHERE ecosystem_tags IS NOT NULL AND array_length(ecosystem_tags, 1) > 0
        GROUP BY unnest(ecosystem_tags)
        ORDER BY COUNT(*) DESC
    """)
    
    ecosystems = [dict(row) for row in cursor.fetchall()]
    
    return {
        'success': True,
        'data': ecosystems,
        'total': len(ecosystems)
    }


@router.get("/search")
def search_github_profiles(
    q: str = Query(..., description="Search query"),
    ecosystem: Optional[str] = Query(None, description="Filter by ecosystem"),
    min_followers: Optional[int] = Query(None, description="Minimum followers"),
    pagination: PaginationParams = Depends(get_pagination_params),
    db=Depends(get_db)
):
    """Search GitHub profiles"""
    cursor = db.cursor()
    
    # Build WHERE clause
    where_clauses = ["""(
        github_username ILIKE %s OR 
        github_name ILIKE %s OR 
        bio ILIKE %s OR 
        github_company ILIKE %s
    )"""]
    search_pattern = f"%{q}%"
    params = [search_pattern, search_pattern, search_pattern, search_pattern]
    
    if ecosystem:
        where_clauses.append("%s = ANY(ecosystem_tags)")
        params.append(ecosystem)
    
    if min_followers:
        where_clauses.append("followers >= %s")
        params.append(min_followers)
    
    where_sql = " AND ".join(where_clauses)
    
    # Count total
    cursor.execute(f"""
        SELECT COUNT(*) 
        FROM github_profile 
        WHERE {where_sql}
    """, params)
    total = cursor.fetchone()[0]
    
    # Get profiles
    cursor.execute(f"""
        SELECT 
            github_profile_id::text,
            github_username,
            github_name,
            bio,
            location,
            github_company,
            followers,
            public_repos,
            avatar_url,
            ecosystem_tags,
            importance_score,
            person_id::text
        FROM github_profile
        WHERE {where_sql}
        ORDER BY followers DESC NULLS LAST
        LIMIT %s OFFSET %s
    """, params + [pagination.limit, pagination.offset])
    
    profiles = [dict(row) for row in cursor.fetchall()]
    
    return {
        'data': profiles,
        'pagination': {
            'offset': pagination.offset,
            'limit': pagination.limit,
            'total': total
        }
    }

