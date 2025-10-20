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
            c.normalized_linkedin_url,
            c.website,
            c.industry,
            c.description,
            c.employee_count,
            c.created_at,
            COUNT(DISTINCT e.person_id) as employee_count_in_db
        FROM company c
        LEFT JOIN employment e ON c.company_id = e.company_id
        WHERE c.company_id = %s::uuid
        GROUP BY c.company_id
    """, (company_id,))
    
    row = cursor.fetchone()
    if not row:
        return None
    
    return {
        'company_id': row[0],
        'company_name': row[1],
        'linkedin_url': row[2],
        'normalized_linkedin_url': row[3],
        'website': row[4],
        'industry': row[5],
        'description': row[6],
        'employee_count': row[7],
        'created_at': row[8],
        'employee_count_in_db': row[9]
    }


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
            where_clauses.append("c.website IS NOT NULL AND c.website != ''")
        else:
            where_clauses.append("(c.website IS NULL OR c.website = '')")
    
    if filters.get('min_employees'):
        where_clauses.append(f"c.employee_count >= ${param_count}")
        params.append(filters['min_employees'])
        param_count += 1
    
    where_sql = "WHERE " + " AND ".join(where_clauses) if where_clauses else ""
    
    # Count total
    count_query = f"SELECT COUNT(*) FROM company c {where_sql}"
    cursor.execute(count_query, params)
    total = cursor.fetchone()[0]
    
    # Get page of results
    query = f"""
        SELECT 
            c.company_id::text,
            c.company_name,
            c.website,
            c.industry,
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
    
    companies = []
    for row in cursor.fetchall():
        companies.append({
            'company_id': row[0],
            'company_name': row[1],
            'website': row[2],
            'industry': row[3],
            'employee_count_in_db': row[4]
        })
    
    return companies, total


def create_company(conn, company_data: Dict) -> str:
    """Create a new company"""
    cursor = conn.cursor()
    
    # Normalize LinkedIn URL
    normalized_linkedin = normalize_linkedin_url(company_data.get('linkedin_url'))
    
    cursor.execute("""
        INSERT INTO company 
        (company_name, linkedin_url, normalized_linkedin_url, website, industry, description, employee_count)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        RETURNING company_id::text
    """, (
        company_data.get('company_name'),
        company_data.get('linkedin_url'),
        normalized_linkedin,
        company_data.get('website'),
        company_data.get('industry'),
        company_data.get('description'),
        company_data.get('employee_count')
    ))
    
    created_id = cursor.fetchone()[0]
    conn.commit()
    
    return created_id


def update_company(conn, company_id: str, company_data: Dict) -> bool:
    """Update a company"""
    cursor = conn.cursor()
    
    # Build UPDATE clause dynamically
    update_fields = []
    params = []
    param_count = 1
    
    for field in ['company_name', 'linkedin_url', 'website', 'industry', 'description', 'employee_count']:
        if field in company_data and company_data[field] is not None:
            update_fields.append(f"{field} = ${param_count}")
            params.append(company_data[field])
            param_count += 1
    
    # Update normalized LinkedIn if linkedin_url is being updated
    if 'linkedin_url' in company_data:
        normalized = normalize_linkedin_url(company_data['linkedin_url'])
        update_fields.append(f"normalized_linkedin_url = ${param_count}")
        params.append(normalized)
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
        SELECT COUNT(DISTINCT p.person_id)
        FROM person p
        JOIN employment e ON p.person_id = e.person_id
        WHERE e.company_id = %s::uuid
    """, (company_id,))
    
    total = cursor.fetchone()[0]
    
    # Get results
    cursor.execute("""
        SELECT DISTINCT
            p.person_id::text,
            p.full_name,
            p.linkedin_url,
            p.location,
            e.title,
            e.is_current
        FROM person p
        JOIN employment e ON p.person_id = e.person_id
        WHERE e.company_id = %s::uuid
        ORDER BY e.is_current DESC, p.full_name
        LIMIT %s OFFSET %s
    """, (company_id, limit, offset))
    
    employees = []
    for row in cursor.fetchall():
        employees.append({
            'person_id': row[0],
            'full_name': row[1],
            'linkedin_url': row[2],
            'location': row[3],
            'title': row[4],
            'is_current': row[5]
        })
    
    return employees, total

