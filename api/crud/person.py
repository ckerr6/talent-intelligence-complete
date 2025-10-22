# ABOUTME: CRUD operations for Person entity
# ABOUTME: Database queries and mutations for people

from typing import List, Optional, Dict, Any
from uuid import UUID
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from migration_scripts.migration_utils import normalize_linkedin_url, generate_person_id


def get_person(conn, person_id: str) -> Optional[Dict]:
    """Get a person by ID"""
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT 
            person_id::text,
            full_name,
            first_name,
            last_name,
            linkedin_url,
            normalized_linkedin_url,
            location,
            headline,
            description,
            followers_count,
            refreshed_at::text as refreshed_at
        FROM person
        WHERE person_id = %s::uuid
    """, (person_id,))
    
    row = cursor.fetchone()
    if not row:
        return None
    
    # RealDictCursor returns dict-like objects, so we can use them directly
    person = dict(row)
    
    # Get emails
    cursor.execute("""
        SELECT email_id, email, email_type, is_primary, verified, source
        FROM person_email
        WHERE person_id = %s::uuid
    """, (person_id,))
    
    person['emails'] = []
    for email_row in cursor.fetchall():
        email_dict = dict(email_row)
        email_dict['person_id'] = person_id
        person['emails'].append(email_dict)
    
    # Get employment history
    cursor.execute("""
        SELECT e.employment_id, e.title, 
               e.start_date::text as start_date, 
               e.end_date::text as end_date,
               (e.end_date IS NULL) as is_current,
               c.company_id::text, c.company_name
        FROM employment e
        LEFT JOIN company c ON e.company_id = c.company_id
        WHERE e.person_id = %s::uuid
        ORDER BY (e.end_date IS NULL) DESC, e.start_date DESC NULLS LAST
        LIMIT 10
    """, (person_id,))
    
    person['employment'] = []
    for emp_row in cursor.fetchall():
        emp_dict = dict(emp_row)
        emp_dict['person_id'] = person_id
        person['employment'].append(emp_dict)
    
    return person


def get_people(conn, filters: Dict[str, Any], offset: int = 0, limit: int = 50) -> tuple[List[Dict], int]:
    """Get people with filters and pagination"""
    cursor = conn.cursor()
    
    # Build WHERE clause
    where_clauses = []
    params = []
    param_count = 1
    
    if filters.get('company'):
        where_clauses.append(f"""
            EXISTS (
                SELECT 1 FROM employment e
                JOIN company c ON e.company_id = c.company_id
                WHERE e.person_id = p.person_id
                AND LOWER(c.company_name) LIKE LOWER(${param_count})
            )
        """)
        params.append(f"%{filters['company']}%")
        param_count += 1
    
    if filters.get('location'):
        where_clauses.append(f"LOWER(p.location) LIKE LOWER(${param_count})")
        params.append(f"%{filters['location']}%")
        param_count += 1
    
    if filters.get('headline'):
        where_clauses.append(f"LOWER(p.headline) LIKE LOWER(${param_count})")
        params.append(f"%{filters['headline']}%")
        param_count += 1
    
    if filters.get('has_email') is not None:
        if filters['has_email']:
            where_clauses.append("EXISTS (SELECT 1 FROM person_email WHERE person_id = p.person_id)")
        else:
            where_clauses.append("NOT EXISTS (SELECT 1 FROM person_email WHERE person_id = p.person_id)")
    
    if filters.get('has_github') is not None:
        if filters['has_github']:
            where_clauses.append("EXISTS (SELECT 1 FROM github_profile WHERE person_id = p.person_id)")
        else:
            where_clauses.append("NOT EXISTS (SELECT 1 FROM github_profile WHERE person_id = p.person_id)")
    
    where_sql = "WHERE " + " AND ".join(where_clauses) if where_clauses else ""
    
    # Count total
    count_query = f"SELECT COUNT(*) as count FROM person p {where_sql}"
    cursor.execute(count_query, params)
    total = cursor.fetchone()['count']
    
    # Get page of results
    query = f"""
        SELECT 
            p.person_id::text,
            p.full_name,
            p.linkedin_url,
            p.location,
            p.headline
        FROM person p
        {where_sql}
        ORDER BY p.full_name
        LIMIT %s OFFSET %s
    """
    params.extend([limit, offset])
    
    cursor.execute(query, params)
    
    people = [dict(row) for row in cursor.fetchall()]
    
    return people, total


def create_person(conn, person_data: Dict) -> str:
    """Create a new person"""
    cursor = conn.cursor()
    
    # Generate or use provided ID
    person_id = generate_person_id(
        linkedin_url=person_data.get('linkedin_url'),
        full_name=person_data.get('full_name')
    )
    
    # Normalize LinkedIn URL
    normalized_linkedin = normalize_linkedin_url(person_data.get('linkedin_url'))
    
    cursor.execute("""
        INSERT INTO person 
        (person_id, full_name, first_name, last_name, linkedin_url, normalized_linkedin_url,
         location, headline, description)
        VALUES (%s::uuid, %s, %s, %s, %s, %s, %s, %s, %s)
        RETURNING person_id::text
    """, (
        person_id,
        person_data.get('full_name'),
        person_data.get('first_name'),
        person_data.get('last_name'),
        person_data.get('linkedin_url'),
        normalized_linkedin,
        person_data.get('location'),
        person_data.get('headline'),
        person_data.get('description')
    ))
    
    created_id = cursor.fetchone()['person_id']
    
    # Add emails if provided
    if person_data.get('emails'):
        for email_data in person_data['emails']:
            cursor.execute("""
                INSERT INTO person_email (person_id, email, email_type, is_primary)
                VALUES (%s::uuid, %s, %s, %s)
            """, (
                created_id,
                email_data['email'],
                email_data.get('email_type', 'unknown'),
                email_data.get('is_primary', False)
            ))
    
    conn.commit()
    return created_id


def update_person(conn, person_id: str, person_data: Dict) -> bool:
    """Update a person"""
    cursor = conn.cursor()
    
    # Build UPDATE clause dynamically
    update_fields = []
    params = []
    param_count = 1
    
    for field in ['full_name', 'first_name', 'last_name', 'linkedin_url', 'location', 'headline', 'description']:
        if field in person_data and person_data[field] is not None:
            update_fields.append(f"{field} = ${param_count}")
            params.append(person_data[field])
            param_count += 1
    
    # Update normalized LinkedIn if linkedin_url is being updated
    if 'linkedin_url' in person_data:
        normalized = normalize_linkedin_url(person_data['linkedin_url'])
        update_fields.append(f"normalized_linkedin_url = ${param_count}")
        params.append(normalized)
        param_count += 1
    
    if not update_fields:
        return False
    
    # Add person_id to params
    params.append(person_id)
    
    query = f"""
        UPDATE person
        SET {', '.join(update_fields)}
        WHERE person_id = ${param_count}::uuid
    """
    
    cursor.execute(query, params)
    updated = cursor.rowcount > 0
    
    if updated:
        conn.commit()
    
    return updated


def delete_person(conn, person_id: str) -> bool:
    """Delete a person (and related records via CASCADE)"""
    cursor = conn.cursor()
    
    cursor.execute("""
        DELETE FROM person
        WHERE person_id = %s::uuid
    """, (person_id,))
    
    deleted = cursor.rowcount > 0
    
    if deleted:
        conn.commit()
    
    return deleted


def search_people_by_company(conn, company_name: str, offset: int = 0, limit: int = 50) -> tuple[List[Dict], int]:
    """Search people by company name"""
    cursor = conn.cursor()
    
    # Count total
    cursor.execute("""
        SELECT COUNT(DISTINCT p.person_id) as count
        FROM person p
        JOIN employment e ON p.person_id = e.person_id
        JOIN company c ON e.company_id = c.company_id
        WHERE LOWER(c.company_name) LIKE LOWER(%s)
    """, (f"%{company_name}%",))
    
    total = cursor.fetchone()['count']
    
    # Get results
    cursor.execute("""
        SELECT DISTINCT
            p.person_id::text,
            p.full_name,
            p.linkedin_url,
            p.location,
            p.headline
        FROM person p
        JOIN employment e ON p.person_id = e.person_id
        JOIN company c ON e.company_id = c.company_id
        WHERE LOWER(c.company_name) LIKE LOWER(%s)
        ORDER BY p.full_name
        LIMIT %s OFFSET %s
    """, (f"%{company_name}%", limit, offset))
    
    people = [dict(row) for row in cursor.fetchall()]
    
    return people, total


def search_people_by_location(conn, location: str, offset: int = 0, limit: int = 50) -> tuple[List[Dict], int]:
    """Search people by location"""
    cursor = conn.cursor()
    
    # Count total
    cursor.execute("""
        SELECT COUNT(*) as count
        FROM person
        WHERE LOWER(location) LIKE LOWER(%s)
    """, (f"%{location}%",))
    
    total = cursor.fetchone()['count']
    
    # Get results
    cursor.execute("""
        SELECT 
            person_id::text,
            full_name,
            linkedin_url,
            location,
            headline
        FROM person
        WHERE LOWER(location) LIKE LOWER(%s)
        ORDER BY full_name
        LIMIT %s OFFSET %s
    """, (f"%{location}%", limit, offset))
    
    people = [dict(row) for row in cursor.fetchall()]
    
    return people, total

