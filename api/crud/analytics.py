# ABOUTME: CRUD operations for Analytics endpoints
# ABOUTME: Queries for analytics and data visualizations

from typing import List, Optional, Dict, Any


def get_top_repositories(conn, company_id: Optional[str] = None, limit: int = 20) -> List[Dict]:
    """Get top repositories by contribution count"""
    cursor = conn.cursor()
    
    where_clause = ""
    params = []
    
    if company_id:
        where_clause = "WHERE gr.company_id = %s::uuid"
        params.append(company_id)
    
    query = f"""
        SELECT 
            gr.repo_id::text as repository_id,
            gr.repo_name,
            gr.full_name as repo_full_name,
            gr.description,
            gr.language,
            gr.stars,
            gr.forks,
            COUNT(DISTINCT gc.github_profile_id) as contributor_count,
            SUM(gc.contribution_count) as total_contributions
        FROM github_repository gr
        LEFT JOIN github_contribution gc ON gr.repo_id = gc.repo_id
        {where_clause}
        GROUP BY gr.repo_id, gr.repo_name, gr.full_name, 
                 gr.description, gr.language, gr.stars, gr.forks
        ORDER BY total_contributions DESC NULLS LAST
        LIMIT %s
    """
    
    params.append(limit)
    cursor.execute(query, params)
    
    return [dict(row) for row in cursor.fetchall()]


def get_top_contributors(
    conn, 
    company_id: Optional[str] = None, 
    repo_id: Optional[str] = None,
    limit: int = 50
) -> List[Dict]:
    """Get top contributors by commit count"""
    cursor = conn.cursor()
    
    where_clauses = []
    params = []
    
    if company_id:
        where_clauses.append("c.company_id = %s::uuid")
        params.append(company_id)
    
    if repo_id:
        where_clauses.append("gc.repo_id = %s::uuid")
        params.append(repo_id)
    
    where_sql = "WHERE " + " AND ".join(where_clauses) if where_clauses else ""
    
    query = f"""
        SELECT 
            p.person_id::text,
            p.full_name,
            gp.github_username,
            gp.github_name,
            SUM(gc.contribution_count) as total_contributions,
            COUNT(DISTINCT gc.repo_id) as repo_count,
            MAX(gc.last_contribution_date)::text as last_contribution
        FROM github_contribution gc
        JOIN github_profile gp ON gc.github_profile_id = gp.github_profile_id
        LEFT JOIN person p ON gp.person_id = p.person_id
        LEFT JOIN github_repository gr ON gc.repo_id = gr.repo_id
        LEFT JOIN company c ON gr.company_id = c.company_id
        {where_sql}
        GROUP BY p.person_id, p.full_name, gp.github_username, gp.github_name
        ORDER BY total_contributions DESC
        LIMIT %s
    """
    
    params.append(limit)
    cursor.execute(query, params)
    
    return [dict(row) for row in cursor.fetchall()]


def get_technology_distribution(conn, company_id: Optional[str] = None) -> List[Dict]:
    """Get technology/language distribution across repositories"""
    cursor = conn.cursor()
    
    where_clause = ""
    params = []
    
    if company_id:
        where_clause = "WHERE company_id = %s::uuid"
        params = [company_id, company_id]  # Need twice - once for subquery, once for main
        language_filter = "AND"
    else:
        language_filter = "WHERE"
    
    query = f"""
        SELECT 
            language,
            COUNT(*) as repo_count,
            SUM(stars) as total_stars,
            SUM(forks) as total_forks,
            ROUND(
                COUNT(*)::numeric / 
                (SELECT COUNT(*) FROM github_repository {where_clause}) * 100, 
                2
            ) as percentage
        FROM github_repository
        {where_clause}
        {language_filter} language IS NOT NULL 
        AND language != ''
        GROUP BY language
        ORDER BY repo_count DESC
        LIMIT 20
    """
    
    cursor.execute(query, params)
    
    return [dict(row) for row in cursor.fetchall()]


def get_developer_activity_summary(
    conn, 
    company_id: Optional[str] = None,
    person_id: Optional[str] = None
) -> Dict:
    """Get aggregated developer activity statistics"""
    cursor = conn.cursor()
    
    where_clauses = []
    params = []
    
    if company_id:
        where_clauses.append("gr.company_id = %s::uuid")
        params.append(company_id)
    
    if person_id:
        where_clauses.append("p.person_id = %s::uuid")
        params.append(person_id)
    
    where_sql = "WHERE " + " AND ".join(where_clauses) if where_clauses else ""
    
    # Get summary statistics
    query = f"""
        SELECT 
            COUNT(DISTINCT gp.github_profile_id) as active_developers,
            COUNT(DISTINCT gc.repo_id) as active_repositories,
            SUM(gc.contribution_count) as total_contributions,
            MIN(gc.last_contribution_date)::text as earliest_contribution,
            MAX(gc.last_contribution_date)::text as latest_contribution
        FROM github_contribution gc
        JOIN github_profile gp ON gc.github_profile_id = gp.github_profile_id
        LEFT JOIN person p ON gp.person_id = p.person_id
        JOIN github_repository gr ON gc.repo_id = gr.repo_id
        {where_sql}
    """
    
    cursor.execute(query, params)
    row = cursor.fetchone()
    
    result = dict(row) if row else {
        'active_developers': 0,
        'active_repositories': 0,
        'total_contributions': 0,
        'earliest_contribution': None,
        'latest_contribution': None
    }
    
    return result


def get_company_list(conn, limit: int = 100) -> List[Dict]:
    """Get list of companies for filter dropdowns"""
    cursor = conn.cursor()
    
    query = """
        SELECT 
            c.company_id::text,
            c.company_name,
            COUNT(DISTINCT e.person_id) as employee_count
        FROM company c
        LEFT JOIN employment e ON c.company_id = e.company_id
        GROUP BY c.company_id, c.company_name
        HAVING COUNT(DISTINCT e.person_id) > 0
        ORDER BY employee_count DESC, c.company_name
        LIMIT %s
    """
    
    cursor.execute(query, (limit,))
    
    return [dict(row) for row in cursor.fetchall()]

