# ABOUTME: Discovery system API endpoints
# ABOUTME: Track discovery sources, recent discoveries, and entity lineage

from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Optional, List
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from api.dependencies import get_db, get_pagination_params, PaginationParams


router = APIRouter(prefix="/discovery", tags=["discovery"])


@router.get("/recent")
def get_recent_discoveries(
    entity_type: Optional[str] = Query(None, description="Filter by entity type (person/repository/company)"),
    pagination: PaginationParams = Depends(get_pagination_params),
    db=Depends(get_db)
):
    """Get recently discovered entities"""
    cursor = db.cursor()
    
    # For now, show recently discovered GitHub profiles
    # In future, this could join with entity_discovery table
    where_clause = ""
    params = []
    
    if entity_type == "person":
        # Get recent GitHub profiles linked to people
        cursor.execute("""
            SELECT COUNT(*) 
            FROM github_profile 
            WHERE person_id IS NOT NULL
        """)
        total = cursor.fetchone()[0]
        
        cursor.execute("""
            SELECT 
                gp.github_profile_id::text as entity_id,
                'person' as entity_type,
                gp.github_username,
                gp.github_name as name,
                gp.bio,
                gp.ecosystem_tags,
                gp.created_at::text as discovered_at,
                p.full_name as linked_person_name,
                p.person_id::text as linked_person_id
            FROM github_profile gp
            LEFT JOIN person p ON gp.person_id = p.person_id
            WHERE gp.person_id IS NOT NULL
            ORDER BY gp.created_at DESC NULLS LAST
            LIMIT %s OFFSET %s
        """, (pagination.limit, pagination.offset))
        
        discoveries = [dict(row) for row in cursor.fetchall()]
        
    elif entity_type == "repository":
        # Get recent repositories
        cursor.execute("""
            SELECT COUNT(*) 
            FROM github_repository
        """)
        total = cursor.fetchone()[0]
        
        cursor.execute("""
            SELECT 
                repo_id::text as entity_id,
                'repository' as entity_type,
                full_name as name,
                description,
                stars,
                language,
                ecosystem_ids as ecosystem_tags,
                created_at::text as discovered_at,
                contributor_count
            FROM github_repository
            ORDER BY created_at DESC NULLS LAST
            LIMIT %s OFFSET %s
        """, (pagination.limit, pagination.offset))
        
        discoveries = [dict(row) for row in cursor.fetchall()]
        
    else:
        # Get all recent discoveries (mixed)
        cursor.execute("""
            SELECT 
                github_profile_id::text as entity_id,
                'person' as entity_type,
                github_username as name,
                bio as description,
                ecosystem_tags,
                created_at::text as discovered_at
            FROM github_profile
            ORDER BY created_at DESC NULLS LAST
            LIMIT %s
        """, (pagination.limit + pagination.offset,))
        
        all_discoveries = [dict(row) for row in cursor.fetchall()]
        total = len(all_discoveries)
        discoveries = all_discoveries[pagination.offset:pagination.offset + pagination.limit]
    
    return {
        'data': discoveries,
        'pagination': {
            'offset': pagination.offset,
            'limit': pagination.limit,
            'total': total
        }
    }


@router.get("/sources")
def get_discovery_sources(db=Depends(get_db)):
    """Get discovery sources and their statistics"""
    cursor = db.cursor()
    
    # Get ecosystem tag distribution
    cursor.execute("""
        SELECT 
            unnest(ecosystem_tags) as source_name,
            'ecosystem_tag' as source_type,
            COUNT(*) as entity_count
        FROM github_profile
        WHERE ecosystem_tags IS NOT NULL AND array_length(ecosystem_tags, 1) > 0
        GROUP BY unnest(ecosystem_tags)
        ORDER BY COUNT(*) DESC
    """)
    
    sources = []
    for row in cursor.fetchall():
        source_dict = dict(row)
        source_dict['description'] = f"Profiles tagged with {source_dict['source_name']}"
        sources.append(source_dict)
    
    return {
        'success': True,
        'data': sources,
        'total': len(sources)
    }


@router.get("/stats")
def get_discovery_stats(db=Depends(get_db)):
    """Get overall discovery statistics"""
    cursor = db.cursor()
    
    # GitHub profiles discovered
    cursor.execute("""
        SELECT 
            COUNT(*) as total_profiles,
            COUNT(CASE WHEN person_id IS NOT NULL THEN 1 END) as linked_to_people,
            COUNT(CASE WHEN ecosystem_tags IS NOT NULL AND array_length(ecosystem_tags, 1) > 0 THEN 1 END) as tagged_profiles,
            AVG(CASE WHEN followers > 0 THEN followers END) as avg_followers,
            MAX(created_at) as last_discovery
        FROM github_profile
    """)
    
    profile_stats = dict(cursor.fetchone())
    
    # Repository stats
    cursor.execute("""
        SELECT 
            COUNT(*) as total_repos,
            COUNT(CASE WHEN ecosystem_ids IS NOT NULL AND array_length(ecosystem_ids, 1) > 0 THEN 1 END) as tagged_repos,
            AVG(CASE WHEN stars > 0 THEN stars END) as avg_stars,
            SUM(contributor_count) as total_contributors_tracked
        FROM github_repository
    """)
    
    repo_stats = dict(cursor.fetchone())
    
    # Contribution stats
    cursor.execute("""
        SELECT 
            COUNT(*) as total_contributions,
            SUM(contribution_count) as total_commits_tracked
        FROM github_contribution
    """)
    
    contribution_stats = dict(cursor.fetchone())
    
    # Ecosystem counts
    cursor.execute("""
        SELECT 
            unnest(ecosystem_tags) as ecosystem,
            COUNT(*) as count
        FROM github_profile
        WHERE ecosystem_tags IS NOT NULL AND array_length(ecosystem_tags, 1) > 0
        GROUP BY unnest(ecosystem_tags)
        ORDER BY COUNT(*) DESC
        LIMIT 10
    """)
    
    top_ecosystems = [dict(row) for row in cursor.fetchall()]
    
    return {
        'success': True,
        'data': {
            'profiles': profile_stats,
            'repositories': repo_stats,
            'contributions': contribution_stats,
            'top_ecosystems': top_ecosystems
        }
    }


@router.get("/ecosystem/{ecosystem_name}")
def get_ecosystem_details(ecosystem_name: str, db=Depends(get_db)):
    """Get detailed information about a specific ecosystem"""
    cursor = db.cursor()
    
    # Profile count
    cursor.execute("""
        SELECT COUNT(*) 
        FROM github_profile 
        WHERE %s = ANY(ecosystem_tags)
    """, (ecosystem_name,))
    profile_count = cursor.fetchone()[0]
    
    if profile_count == 0:
        raise HTTPException(status_code=404, detail=f"Ecosystem '{ecosystem_name}' not found")
    
    # Repository count - count repos from contributors in this ecosystem
    cursor.execute("""
        SELECT COUNT(DISTINCT r.repo_id)
        FROM github_repository r
        JOIN github_contribution gc ON r.repo_id = gc.repo_id
        JOIN github_profile gp ON gc.github_profile_id = gp.github_profile_id
        WHERE %s = ANY(gp.ecosystem_tags)
    """, (ecosystem_name,))
    repo_count = cursor.fetchone()[0]
    
    # Top contributors
    cursor.execute("""
        SELECT 
            github_username,
            github_name,
            bio,
            followers,
            public_repos,
            avatar_url
        FROM github_profile
        WHERE %s = ANY(ecosystem_tags)
        ORDER BY followers DESC NULLS LAST, importance_score DESC NULLS LAST
        LIMIT 10
    """, (ecosystem_name,))
    top_contributors = [dict(row) for row in cursor.fetchall()]
    
    # Top repositories - find repos from contributors in this ecosystem
    cursor.execute("""
        SELECT 
            r.full_name,
            r.description,
            r.stars,
            r.forks,
            r.language,
            r.contributor_count,
            COUNT(DISTINCT gc.github_profile_id) as ecosystem_contributors
        FROM github_repository r
        JOIN github_contribution gc ON r.repo_id = gc.repo_id
        JOIN github_profile gp ON gc.github_profile_id = gp.github_profile_id
        WHERE %s = ANY(gp.ecosystem_tags)
        GROUP BY r.repo_id, r.full_name, r.description, r.stars, r.forks, r.language, r.contributor_count
        ORDER BY r.stars DESC NULLS LAST, ecosystem_contributors DESC
        LIMIT 10
    """, (ecosystem_name,))
    top_repos = [dict(row) for row in cursor.fetchall()]
    
    return {
        'success': True,
        'data': {
            'ecosystem': ecosystem_name,
            'profile_count': profile_count,
            'repo_count': repo_count,
            'top_contributors': top_contributors,
            'top_repositories': top_repos
        }
    }

