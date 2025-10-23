"""
Network analysis CRUD operations
Handles co-employment graph queries, pathfinding, and network distance calculations
"""

from typing import List, Dict, Optional, Tuple
from collections import deque
import psycopg2
from psycopg2.extras import RealDictCursor


def get_connections(
    person_id: str,
    connection_type: Optional[str] = None,
    limit: int = 100,
    db=None
) -> List[Dict]:
    """
    Get all connections for a person
    
    Args:
        person_id: UUID of the person
        connection_type: Filter by 'coworker' or 'github_collaborator' or None for all
        limit: Maximum number of connections to return
        
    Returns:
        List of connected people with connection metadata
    """
    
    if connection_type == 'coworker' or connection_type is None:
        # Get coworker connections
        coworker_query = """
            SELECT DISTINCT
                p.person_id,
                p.full_name,
                p.headline,
                p.location,
                'coworker' as connection_type,
                c.company_name,
                e1.start_date as overlap_start,
                e1.end_date as overlap_end
            FROM edge_coemployment ec
            JOIN person p ON ec.dst_person_id = p.person_id
            JOIN employment e1 ON ec.src_person_id = e1.person_id AND ec.company_id = e1.company_id
            JOIN employment e2 ON ec.dst_person_id = e2.person_id AND ec.company_id = e2.company_id
            JOIN company c ON ec.company_id = c.company_id
            WHERE ec.src_person_id = %s
            ORDER BY e1.start_date DESC
            LIMIT %s
        """
        
        cursor = db.cursor(cursor_factory=RealDictCursor)
        cursor.execute(coworker_query, (person_id, limit))
        connections = [dict(row) for row in cursor.fetchall()]
        cursor.close()
        
        if connection_type == 'coworker':
            return connections
    
    if connection_type == 'github_collaborator' or connection_type is None:
        # Get GitHub collaborator connections
        github_query = """
            SELECT DISTINCT
                p2.person_id,
                p2.full_name,
                p2.headline,
                p2.location,
                'github_collaborator' as connection_type,
                gr.full_name as repo_name,
                gr.description as repo_description,
                gc1.contribution_count + gc2.contribution_count as total_contributions
            FROM github_profile gp1
            JOIN github_contribution gc1 ON gp1.github_profile_id = gc1.github_profile_id
            JOIN github_contribution gc2 ON gc1.repo_id = gc2.repo_id
            JOIN github_profile gp2 ON gc2.github_profile_id = gp2.github_profile_id
            JOIN person p2 ON gp2.person_id = p2.person_id
            JOIN github_repository gr ON gc1.repo_id = gr.repo_id
            WHERE gp1.person_id = %s
            AND p2.person_id != %s
            ORDER BY total_contributions DESC
            LIMIT %s
        """
        
        cursor = db.cursor(cursor_factory=RealDictCursor)
        cursor.execute(github_query, (person_id, person_id, limit))
        github_connections = [dict(row) for row in cursor.fetchall()]
        cursor.close()
        
        if connection_type == 'github_collaborator':
            return github_connections
        
        # Merge both types if no filter
        connections.extend(github_connections)
    
    return connections[:limit]


def find_shortest_path(
    source_person_id: str,
    target_person_id: str,
    max_depth: int = 3,
    db=None
) -> Optional[Dict]:
    """
    Find shortest path between two people using BFS
    
    Args:
        source_person_id: Starting person UUID
        target_person_id: Target person UUID
        max_depth: Maximum degrees of separation to search
        
    Returns:
        Dict with path details or None if no path found
    """
    
    # Check cache first
    cached_path = get_cached_path(source_person_id, target_person_id, db)
    if cached_path:
        return cached_path
    
    # BFS to find shortest path
    queue = deque([(source_person_id, [source_person_id])])
    visited = {source_person_id}
    
    while queue:
        current_id, path = queue.popleft()
        
        if len(path) > max_depth + 1:
            continue
        
        if current_id == target_person_id:
            # Found path - enrich with details
            enriched_path = enrich_path(path, db)
            
            # Cache the path
            cache_path(source_person_id, target_person_id, enriched_path, db)
            
            return enriched_path
        
        # Get all connections
        cursor = db.cursor(cursor_factory=RealDictCursor)
        
        # Get coworker connections
        cursor.execute("""
            SELECT DISTINCT dst_person_id as person_id
            FROM edge_coemployment
            WHERE src_person_id = %s
            LIMIT 50
        """, (current_id,))
        
        coworker_ids = [row['person_id'] for row in cursor.fetchall()]
        
        # Get GitHub collaborator connections
        cursor.execute("""
            SELECT DISTINCT p2.person_id
            FROM github_profile gp1
            JOIN github_contribution gc1 ON gp1.github_profile_id = gc1.github_profile_id
            JOIN github_contribution gc2 ON gc1.repo_id = gc2.repo_id
            JOIN github_profile gp2 ON gc2.github_profile_id = gp2.github_profile_id
            JOIN person p2 ON gp2.person_id = p2.person_id
            WHERE gp1.person_id = %s AND p2.person_id != %s
            LIMIT 50
        """, (current_id, current_id))
        
        github_ids = [row['person_id'] for row in cursor.fetchall()]
        cursor.close()
        
        all_connections = set(coworker_ids + github_ids)
        
        for conn_id in all_connections:
            if conn_id not in visited:
                visited.add(conn_id)
                queue.append((conn_id, path + [conn_id]))
    
    return None  # No path found


def enrich_path(path: List[str], db) -> Dict:
    """
    Add person details and connection types to a path
    
    Args:
        path: List of person_ids
        
    Returns:
        Dict with enriched path information
    """
    
    cursor = db.cursor(cursor_factory=RealDictCursor)
    
    # Get person details for each node
    cursor.execute("""
        SELECT person_id, full_name, headline, location
        FROM person
        WHERE person_id = ANY(%s)
    """, (path,))
    
    people_by_id = {row['person_id']: dict(row) for row in cursor.fetchall()}
    
    # Build enriched path
    nodes = []
    edges = []
    
    for i, person_id in enumerate(path):
        person = people_by_id.get(person_id, {})
        nodes.append({
            'person_id': person_id,
            'name': person.get('full_name', 'Unknown'),
            'headline': person.get('headline'),
            'location': person.get('location'),
            'position': i
        })
        
        if i < len(path) - 1:
            # Determine connection type between this node and next
            next_id = path[i + 1]
            
            # Check for coworker relationship
            cursor.execute("""
                SELECT c.company_name
                FROM edge_coemployment ec
                JOIN company c ON ec.company_id = c.company_id
                WHERE ec.src_person_id = %s AND ec.dst_person_id = %s
                LIMIT 1
            """, (person_id, next_id))
            
            coworker = cursor.fetchone()
            
            if coworker:
                edges.append({
                    'from': person_id,
                    'to': next_id,
                    'type': 'coworker',
                    'company': coworker['company_name']
                })
            else:
                # Check for GitHub collaboration
                cursor.execute("""
                    SELECT gr.full_name as repo_name
                    FROM github_profile gp1
                    JOIN github_contribution gc1 ON gp1.github_profile_id = gc1.github_profile_id
                    JOIN github_contribution gc2 ON gc1.repo_id = gc2.repo_id
                    JOIN github_profile gp2 ON gc2.github_profile_id = gp2.github_profile_id
                    JOIN github_repository gr ON gc1.repo_id = gr.repo_id
                    WHERE gp1.person_id = %s AND gp2.person_id = %s
                    LIMIT 1
                """, (person_id, next_id))
                
                github = cursor.fetchone()
                
                if github:
                    edges.append({
                        'from': person_id,
                        'to': next_id,
                        'type': 'github_collaborator',
                        'repo': github['repo_name']
                    })
                else:
                    edges.append({
                        'from': person_id,
                        'to': next_id,
                        'type': 'unknown'
                    })
    
    cursor.close()
    
    return {
        'path_length': len(path) - 1,
        'nodes': nodes,
        'edges': edges
    }


def get_mutual_connections(
    person1_id: str,
    person2_id: str,
    limit: int = 50,
    db=None
) -> List[Dict]:
    """
    Find mutual connections between two people
    
    Returns:
        List of people who are connected to both
    """
    
    cursor = db.cursor(cursor_factory=RealDictCursor)
    
    cursor.execute("""
        WITH person1_connections AS (
            SELECT DISTINCT dst_person_id as person_id
            FROM edge_coemployment
            WHERE src_person_id = %s
        ),
        person2_connections AS (
            SELECT DISTINCT dst_person_id as person_id
            FROM edge_coemployment
            WHERE src_person_id = %s
        )
        SELECT 
            p.person_id,
            p.full_name,
            p.headline,
            p.location,
            COUNT(DISTINCT ec1.company_id) as shared_companies
        FROM person1_connections p1c
        JOIN person2_connections p2c ON p1c.person_id = p2c.person_id
        JOIN person p ON p1c.person_id = p.person_id
        LEFT JOIN edge_coemployment ec1 ON p.person_id = ec1.dst_person_id AND ec1.src_person_id = %s
        GROUP BY p.person_id, p.full_name, p.headline, p.location
        ORDER BY shared_companies DESC
        LIMIT %s
    """, (person1_id, person2_id, person1_id, limit))
    
    mutual = [dict(row) for row in cursor.fetchall()]
    cursor.close()
    
    return mutual


def calculate_network_distance(
    source_person_id: str,
    target_person_id: str,
    db=None
) -> Optional[int]:
    """
    Calculate degrees of separation between two people
    
    Returns:
        Number of hops (1 = direct connection, 2 = friend of friend, etc.) or None
    """
    
    path = find_shortest_path(source_person_id, target_person_id, max_depth=3, db=db)
    
    if path:
        return path['path_length']
    
    return None


def get_cached_path(
    source_person_id: str,
    target_person_id: str,
    db
) -> Optional[Dict]:
    """
    Retrieve cached path if available and fresh (< 7 days old)
    """
    
    cursor = db.cursor(cursor_factory=RealDictCursor)
    
    cursor.execute("""
        SELECT path_length, path_nodes, cached_at
        FROM network_paths
        WHERE source_person_id = %s AND target_person_id = %s
        AND cached_at > NOW() - INTERVAL '7 days'
    """, (source_person_id, target_person_id))
    
    result = cursor.fetchone()
    cursor.close()
    
    if result:
        return {
            'path_length': result['path_length'],
            'nodes': result['path_nodes'].get('nodes', []),
            'edges': result['path_nodes'].get('edges', []),
            'cached': True
        }
    
    return None


def cache_path(
    source_person_id: str,
    target_person_id: str,
    path_data: Dict,
    db
):
    """
    Cache a computed path for future lookups
    """
    
    cursor = db.cursor()
    
    cursor.execute("""
        INSERT INTO network_paths (source_person_id, target_person_id, path_length, path_nodes, cached_at)
        VALUES (%s, %s, %s, %s, NOW())
        ON CONFLICT (source_person_id, target_person_id)
        DO UPDATE SET
            path_length = EXCLUDED.path_length,
            path_nodes = EXCLUDED.path_nodes,
            cached_at = NOW()
    """, (
        source_person_id,
        target_person_id,
        path_data['path_length'],
        psycopg2.extras.Json({'nodes': path_data['nodes'], 'edges': path_data['edges']})
    ))
    
    db.commit()
    cursor.close()


def get_network_stats(person_id: str, db) -> Dict:
    """
    Get network statistics for a person
    
    Returns:
        Dict with connection counts, top companies, etc.
    """
    
    cursor = db.cursor(cursor_factory=RealDictCursor)
    
    # Count coworker connections
    cursor.execute("""
        SELECT COUNT(DISTINCT dst_person_id) as coworker_count
        FROM edge_coemployment
        WHERE src_person_id = %s
    """, (person_id,))
    
    coworker_count = cursor.fetchone()['coworker_count']
    
    # Count GitHub collaborators
    cursor.execute("""
        SELECT COUNT(DISTINCT p2.person_id) as github_count
        FROM github_profile gp1
        JOIN github_contribution gc1 ON gp1.github_profile_id = gc1.github_profile_id
        JOIN github_contribution gc2 ON gc1.repo_id = gc2.repo_id
        JOIN github_profile gp2 ON gc2.github_profile_id = gp2.github_profile_id
        JOIN person p2 ON gp2.person_id = p2.person_id
        WHERE gp1.person_id = %s AND p2.person_id != %s
    """, (person_id, person_id))
    
    github_count = cursor.fetchone()['github_count']
    
    # Top companies in network
    cursor.execute("""
        SELECT c.company_name, COUNT(DISTINCT ec.dst_person_id) as connection_count
        FROM edge_coemployment ec
        JOIN company c ON ec.company_id = c.company_id
        WHERE ec.src_person_id = %s
        GROUP BY c.company_name
        ORDER BY connection_count DESC
        LIMIT 10
    """, (person_id,))
    
    top_companies = [dict(row) for row in cursor.fetchall()]
    
    cursor.close()
    
    return {
        'total_connections': coworker_count + github_count,
        'coworker_connections': coworker_count,
        'github_connections': github_count,
        'top_companies': top_companies
    }

