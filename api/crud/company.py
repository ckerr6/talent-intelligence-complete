# ABOUTME: CRUD operations for Company entity
# ABOUTME: Database queries and mutations for companies

from typing import List, Optional, Dict, Any
from uuid import UUID
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from migration_scripts.migration_utils import normalize_linkedin_url, generate_person_id


def get_company(conn, company_id: str) -> Optional[Dict]:
    """Get a company by ID"""
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT 
            c.company_id::text,
            c.company_name,
            c.linkedin_url,
            c.linkedin_slug,
            c.website_url,
            c.industry,
            c.hq,
            c.founded_year,
            c.size_bucket,
            COUNT(DISTINCT e.person_id) as employee_count_in_db
        FROM company c
        LEFT JOIN employment e ON c.company_id = e.company_id
        WHERE c.company_id = %s::uuid
        GROUP BY c.company_id
    """, (company_id,))
    
    row = cursor.fetchone()
    if not row:
        return None
    
    # RealDictCursor returns dict-like objects
    return dict(row)


def get_companies(conn, filters: Dict[str, Any], offset: int = 0, limit: int = 50) -> tuple[List[Dict], int]:
    """Get companies with filters and pagination"""
    cursor = conn.cursor()
    
    # Build WHERE clause
    where_clauses = []
    params = []
    param_count = 1
    
    if filters.get('industry'):
        where_clauses.append(f"LOWER(c.industry) LIKE LOWER(${param_count})")
        params.append(f"%{filters['industry']}%")
        param_count += 1
    
    if filters.get('has_website') is not None:
        if filters['has_website']:
            where_clauses.append("c.website_url IS NOT NULL AND c.website_url != ''")
        else:
            where_clauses.append("(c.website_url IS NULL OR c.website_url = '')")
    
    if filters.get('size_bucket'):
        where_clauses.append(f"c.size_bucket = ${param_count}")
        params.append(filters['size_bucket'])
        param_count += 1
    
    where_sql = "WHERE " + " AND ".join(where_clauses) if where_clauses else ""
    
    # Count total
    count_query = f"SELECT COUNT(*) as count FROM company c {where_sql}"
    cursor.execute(count_query, params)
    total = cursor.fetchone()['count']
    
    # Get page of results
    query = f"""
        SELECT 
            c.company_id::text,
            c.company_name,
            c.website_url,
            c.industry,
            c.size_bucket,
            COUNT(DISTINCT e.person_id) as employee_count_in_db
        FROM company c
        LEFT JOIN employment e ON c.company_id = e.company_id
        {where_sql}
        GROUP BY c.company_id
        ORDER BY c.company_name
        LIMIT ${param_count} OFFSET ${param_count + 1}
    """
    
    params.extend([limit, offset])
    cursor.execute(query, params)
    
    companies = [dict(row) for row in cursor.fetchall()]
    
    return companies, total


def create_company(conn, company_data: Dict) -> str:
    """Create a new company"""
    cursor = conn.cursor()
    
    # Normalize LinkedIn URL
    normalized_linkedin = normalize_linkedin_url(company_data.get('linkedin_url'))
    
    cursor.execute("""
        INSERT INTO company 
        (company_domain, company_name, linkedin_url, linkedin_slug, website_url, industry, hq, founded_year, size_bucket)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        RETURNING company_id::text
    """, (
        company_data.get('company_domain', company_data.get('company_name', 'unknown').lower().replace(' ', '') + '.com'),
        company_data.get('company_name'),
        company_data.get('linkedin_url'),
        company_data.get('linkedin_slug') or normalized_linkedin.split('/')[-1] if normalized_linkedin else None,
        company_data.get('website_url'),
        company_data.get('industry'),
        company_data.get('hq'),
        company_data.get('founded_year'),
        company_data.get('size_bucket')
    ))
    
    created_id = cursor.fetchone()['company_id']
    conn.commit()
    
    return created_id


def update_company(conn, company_id: str, company_data: Dict) -> bool:
    """Update a company"""
    cursor = conn.cursor()
    
    # Build UPDATE clause dynamically
    update_fields = []
    params = []
    param_count = 1
    
    for field in ['company_name', 'linkedin_url', 'linkedin_slug', 'website_url', 'industry', 'hq', 'founded_year', 'size_bucket']:
        if field in company_data and company_data[field] is not None:
            update_fields.append(f"{field} = ${param_count}")
            params.append(company_data[field])
            param_count += 1
    
    if not update_fields:
        return False
    
    # Add company_id to params
    params.append(company_id)
    
    query = f"""
        UPDATE company
        SET {', '.join(update_fields)}
        WHERE company_id = ${param_count}::uuid
    """
    
    cursor.execute(query, params)
    updated = cursor.rowcount > 0
    
    if updated:
        conn.commit()
    
    return updated


def delete_company(conn, company_id: str) -> bool:
    """Delete a company"""
    cursor = conn.cursor()
    
    # Note: This might fail if there are employment records
    # Consider soft delete or cascade rules
    cursor.execute("""
        DELETE FROM company
        WHERE company_id = %s::uuid
    """, (company_id,))
    
    deleted = cursor.rowcount > 0
    
    if deleted:
        conn.commit()
    
    return deleted


def get_company_employees(conn, company_id: str, offset: int = 0, limit: int = 50) -> tuple[List[Dict], int]:
    """Get employees of a company"""
    cursor = conn.cursor()
    
    # Count total
    cursor.execute("""
        SELECT COUNT(DISTINCT p.person_id) as count
        FROM person p
        JOIN employment e ON p.person_id = e.person_id
        WHERE e.company_id = %s::uuid
    """, (company_id,))
    
    total = cursor.fetchone()['count']
    
    # Get results
    cursor.execute("""
        SELECT DISTINCT
            p.person_id::text,
            p.full_name,
            p.linkedin_url,
            p.location,
            e.title,
            e.start_date,
            e.end_date
        FROM person p
        JOIN employment e ON p.person_id = e.person_id
        WHERE e.company_id = %s::uuid
        ORDER BY e.start_date DESC NULLS LAST, p.full_name
        LIMIT %s OFFSET %s
    """, (company_id, limit, offset))
    
    employees = [dict(row) for row in cursor.fetchall()]
    
    return employees, total


def get_company_hiring_timeline(conn, company_id: str) -> List[Dict]:
    """Get hiring timeline - employees by start date"""
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT 
            DATE_TRUNC('month', e.start_date)::date as month,
            COUNT(*) as hires_count,
            ARRAY_AGG(p.full_name ORDER BY e.start_date) as names
        FROM employment e
        JOIN person p ON e.person_id = p.person_id
        WHERE e.company_id = %s::uuid
        AND e.start_date IS NOT NULL
        GROUP BY DATE_TRUNC('month', e.start_date)
        ORDER BY month
    """, (company_id,))
    
    return [dict(row) for row in cursor.fetchall()]


def get_github_contributors(conn, company_id: str, limit: int = 100, offset: int = 0) -> tuple[List[Dict], int]:
    """Get GitHub contributors who are NOT employees of this company"""
    cursor = conn.cursor()
    
    # Get all repositories for this company
    cursor.execute("""
        SELECT repo_id
        FROM github_repository
        WHERE company_id = %s::uuid
    """, (company_id,))
    
    repo_ids = [row['repo_id'] for row in cursor.fetchall()]
    
    if not repo_ids:
        return [], 0
    
    # Get contributors who are not employees
    cursor.execute("""
        WITH company_employees AS (
            SELECT DISTINCT person_id
            FROM employment
            WHERE company_id = %s::uuid
        )
        SELECT 
            gp.github_profile_id::text,
            gp.github_username,
            gp.github_name,
            gp.github_email,
            gp.followers,
            gp.public_repos,
            gp.bio,
            gp.location,
            COUNT(DISTINCT gc.repo_id) as repo_count,
            SUM(gc.contribution_count) as total_contributions
        FROM github_contribution gc
        JOIN github_profile gp ON gc.github_profile_id = gp.github_profile_id
        WHERE gc.repo_id = ANY(%s::uuid[])
        AND (gp.person_id IS NULL OR gp.person_id NOT IN (SELECT person_id FROM company_employees))
        GROUP BY gp.github_profile_id, gp.github_username, gp.github_name, 
                 gp.github_email, gp.followers, gp.public_repos, gp.bio, gp.location
        ORDER BY total_contributions DESC
        LIMIT %s OFFSET %s
    """, (company_id, repo_ids, limit, offset))
    
    contributors = [dict(row) for row in cursor.fetchall()]
    
    # Get total count
    cursor.execute("""
        WITH company_employees AS (
            SELECT DISTINCT person_id
            FROM employment
            WHERE company_id = %s::uuid
        )
        SELECT COUNT(DISTINCT gp.github_profile_id) as count
        FROM github_contribution gc
        JOIN github_profile gp ON gc.github_profile_id = gp.github_profile_id
        WHERE gc.repo_id = ANY(%s::uuid[])
        AND (gp.person_id IS NULL OR gp.person_id NOT IN (SELECT person_id FROM company_employees))
    """, (company_id, repo_ids))
    
    total = cursor.fetchone()['count']
    
    return contributors, total
