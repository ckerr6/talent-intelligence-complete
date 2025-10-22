# ABOUTME: CRUD operations for graph/relationship queries
# ABOUTME: Database queries for co-employment and social network data

from typing import List, Dict, Any, Optional, Tuple
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))


def get_coworkers(conn, person_id: str, limit: int = 100, offset: int = 0) -> Tuple[List[Dict], int]:
    """Get all people who worked with this person at any company"""
    cursor = conn.cursor()
    
    # Get coworkers from edge_coemployment
    cursor.execute("""
        WITH coworker_edges AS (
            SELECT 
                CASE 
                    WHEN src_person_id = %s::uuid THEN dst_person_id
                    ELSE src_person_id
                END as coworker_id,
                company_id,
                overlap_months,
                first_overlap_start,
                last_overlap_end
            FROM edge_coemployment
            WHERE src_person_id = %s::uuid OR dst_person_id = %s::uuid
        )
        SELECT 
            p.person_id::text,
            p.full_name,
            p.location,
            p.headline,
            c.company_name,
            ce.overlap_months,
            ce.first_overlap_start,
            ce.last_overlap_end
        FROM coworker_edges ce
        JOIN person p ON p.person_id = ce.coworker_id
        LEFT JOIN company c ON c.company_id = ce.company_id
        ORDER BY ce.overlap_months DESC NULLS LAST, p.full_name
        LIMIT %s OFFSET %s
    """, (person_id, person_id, person_id, limit, offset))
    
    coworkers = [dict(row) for row in cursor.fetchall()]
    
    # Get total count
    cursor.execute("""
        SELECT COUNT(DISTINCT 
            CASE 
                WHEN src_person_id = %s::uuid THEN dst_person_id
                ELSE src_person_id
            END
        ) as count
        FROM edge_coemployment
        WHERE src_person_id = %s::uuid OR dst_person_id = %s::uuid
    """, (person_id, person_id, person_id))
    
    total = cursor.fetchone()['count']
    
    return coworkers, total


def get_company_network(
    conn, 
    company_id: str, 
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    limit: int = 500
) -> Dict[str, Any]:
    """Get the co-employment network for a specific company"""
    cursor = conn.cursor()
    
    # Build date filter
    date_filter = ""
    params = [company_id]
    
    if start_date and end_date:
        date_filter = """
            AND (
                (first_overlap_start IS NULL AND last_overlap_end IS NULL)
                OR (
                    first_overlap_start <= %s::date 
                    AND (last_overlap_end >= %s::date OR last_overlap_end IS NULL)
                )
            )
        """
        params.extend([end_date, start_date])
    
    # Get edges for this company
    cursor.execute(f"""
        SELECT 
            src_person_id::text,
            dst_person_id::text,
            overlap_months,
            first_overlap_start,
            last_overlap_end
        FROM edge_coemployment
        WHERE company_id = %s::uuid
        {date_filter}
        LIMIT %s
    """, params + [limit])
    
    edges = [dict(row) for row in cursor.fetchall()]
    
    # Get all unique person IDs from edges
    person_ids = set()
    for edge in edges:
        person_ids.add(edge['src_person_id'])
        person_ids.add(edge['dst_person_id'])
    
    # Get person details
    nodes = []
    if person_ids:
        cursor.execute("""
            SELECT 
                person_id::text,
                full_name,
                location,
                headline,
                followers_count
            FROM person
            WHERE person_id = ANY(%s::uuid[])
        """, (list(person_ids),))
        
        nodes = [dict(row) for row in cursor.fetchall()]
    
    return {
        'nodes': nodes,
        'edges': edges,
        'node_count': len(nodes),
        'edge_count': len(edges)
    }


def get_graph_stats(conn) -> Dict[str, Any]:
    """Get overall graph statistics"""
    cursor = conn.cursor()
    
    # Get edge count
    cursor.execute("SELECT COUNT(*) as count FROM edge_coemployment")
    edge_count = cursor.fetchone()['count']
    
    # Get unique person count in graph
    cursor.execute("""
        SELECT COUNT(DISTINCT person_id) as count
        FROM (
            SELECT src_person_id as person_id FROM edge_coemployment
            UNION
            SELECT dst_person_id as person_id FROM edge_coemployment
        ) all_people
    """)
    people_in_graph = cursor.fetchone()['count']
    
    # Get connection distribution
    cursor.execute("""
        WITH connection_counts AS (
            SELECT person_id, COUNT(*) as connections
            FROM (
                SELECT src_person_id as person_id FROM edge_coemployment
                UNION ALL
                SELECT dst_person_id as person_id FROM edge_coemployment
            ) all_connections
            GROUP BY person_id
        )
        SELECT 
            MIN(connections) as min_connections,
            MAX(connections) as max_connections,
            AVG(connections)::integer as avg_connections,
            PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY connections)::integer as median_connections
        FROM connection_counts
    """)
    
    distribution = cursor.fetchone()
    
    return {
        'total_edges': edge_count,
        'people_in_graph': people_in_graph,
        'min_connections': distribution['min_connections'] if distribution else 0,
        'max_connections': distribution['max_connections'] if distribution else 0,
        'avg_connections': distribution['avg_connections'] if distribution else 0,
        'median_connections': distribution['median_connections'] if distribution else 0
    }


def get_top_connected_people(conn, limit: int = 10) -> List[Dict]:
    """Get the most connected people in the network"""
    cursor = conn.cursor()
    
    cursor.execute("""
        WITH all_connections AS (
            SELECT src_person_id as person_id FROM edge_coemployment
            UNION ALL
            SELECT dst_person_id as person_id FROM edge_coemployment
        )
        SELECT 
            p.person_id::text,
            p.full_name,
            p.location,
            p.headline,
            COUNT(*) as connection_count
        FROM all_connections ac
        JOIN person p ON ac.person_id = p.person_id
        GROUP BY p.person_id, p.full_name, p.location, p.headline
        ORDER BY connection_count DESC
        LIMIT %s
    """, (limit,))
    
    return [dict(row) for row in cursor.fetchall()]


def search_by_multiple_criteria(
    conn,
    company: Optional[str] = None,
    location: Optional[str] = None,
    has_email: Optional[bool] = None,
    has_github: Optional[bool] = None,
    headline_keyword: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    limit: int = 100,
    offset: int = 0
) -> Tuple[List[Dict], int]:
    """Complex search across multiple criteria"""
    cursor = conn.cursor()
    
    conditions = []
    params = []
    
    # Base query (optimized for demo - uses DISTINCT ON for fast deduplication)
    query = """
        SELECT DISTINCT ON (p.person_id)
            p.person_id::text,
            p.full_name,
            p.first_name,
            p.last_name,
            p.location,
            p.headline,
            p.linkedin_url,
            p.followers_count,
            (SELECT c.company_id::text FROM employment e 
             JOIN company c ON e.company_id = c.company_id 
             WHERE e.person_id = p.person_id 
             ORDER BY e.start_date DESC NULLS LAST LIMIT 1) as company_id,
            (SELECT c.company_name FROM employment e 
             JOIN company c ON e.company_id = c.company_id 
             WHERE e.person_id = p.person_id 
             ORDER BY e.start_date DESC NULLS LAST LIMIT 1) as company_name
        FROM person p
    """
    
    # Join tables as needed (only for filtering, not for display)
    joins = []
    
    # Add employment/company join if company filtering is needed
    if company or start_date or end_date:
        joins.append("LEFT JOIN employment e ON p.person_id = e.person_id")
        joins.append("LEFT JOIN company c ON e.company_id = c.company_id")
    
    if has_email:
        joins.append("LEFT JOIN person_email pe ON p.person_id = pe.person_id")
    
    if has_github:
        joins.append("LEFT JOIN github_profile gp ON p.person_id = gp.person_id")
    
    # Add joins
    if joins:
        query += " " + " ".join(joins)
    
    # Build conditions
    if company:
        conditions.append("LOWER(c.company_name) LIKE LOWER(%s)")
        params.append(f"%{company}%")
    
    if location:
        conditions.append("LOWER(p.location) LIKE LOWER(%s)")
        params.append(f"%{location}%")
    
    if has_email is True:
        conditions.append("pe.person_id IS NOT NULL")
    elif has_email is False:
        conditions.append("pe.person_id IS NULL")
    
    if has_github is True:
        conditions.append("gp.person_id IS NOT NULL")
    elif has_github is False:
        conditions.append("gp.person_id IS NULL")
    
    if headline_keyword:
        conditions.append("LOWER(p.headline) LIKE LOWER(%s)")
        params.append(f"%{headline_keyword}%")
    
    if start_date:
        conditions.append("e.start_date >= %s")
        params.append(start_date)
    
    if end_date:
        conditions.append("(e.end_date <= %s OR e.end_date IS NULL)")
        params.append(end_date)
    
    # Add WHERE clause
    if conditions:
        query += " WHERE " + " AND ".join(conditions)
    
    # Add ordering and pagination (must order by person_id first for DISTINCT ON)
    query += " ORDER BY p.person_id, p.full_name LIMIT %s OFFSET %s"
    params.extend([limit, offset])
    
    cursor.execute(query, params)
    results = [dict(row) for row in cursor.fetchall()]
    
    # Get total count
    count_query = """
        SELECT COUNT(DISTINCT p.person_id) as count
        FROM person p
    """
    
    if joins:
        count_query += " " + " ".join(joins)
    
    if conditions:
        count_query += " WHERE " + " AND ".join(conditions)
    
    cursor.execute(count_query, params[:-2])  # Exclude limit and offset
    total = cursor.fetchone()['count']
    
    return results, total

