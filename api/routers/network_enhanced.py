"""
Enhanced Network Analysis API
Multi-node search, technology filtering, and advanced graph features
"""

from fastapi import APIRouter, Depends, HTTPException, Query, Body
from typing import List, Optional, Set
from psycopg2.extras import RealDictCursor
import logging

from api.dependencies import get_db

router = APIRouter(prefix="/api/network", tags=["network-enhanced"])
logger = logging.getLogger(__name__)


@router.post("/multi-node-graph")
async def get_multi_node_graph(
    person_ids: List[str] = Body(..., description="List of 2-4 person IDs to center the graph on"),
    max_degree: int = Body(2, ge=1, le=3, description="Maximum degrees of separation"),
    limit: int = Body(200, ge=10, le=500, description="Maximum nodes to return"),
    technologies: Optional[List[str]] = Body(None, description="Filter by technologies (e.g., ['Python', 'React'])"),
    connection_types: Optional[List[str]] = Body(None, description="Filter by connection types"),
    employment_status: Optional[str] = Body(None, description="Filter: 'current', 'former', or 'all'"),
    company_filter: Optional[str] = Body(None, description="Filter by company name"),
    db=Depends(get_db)
):
    """
    Get network graph for multiple people simultaneously
    
    Returns:
    - Nodes for all specified people and their connections
    - Edges showing relationships
    - Connector nodes (people who connect the specified people)
    - Technology overlap information
    """
    
    if not person_ids or len(person_ids) > 4:
        raise HTTPException(status_code=400, detail="Please provide 2-4 person IDs")
    
    try:
        cursor = db.cursor(cursor_factory=RealDictCursor)
        
        # Get center people details
        cursor.execute("""
            SELECT person_id, full_name, headline, location
            FROM person
            WHERE person_id = ANY(%s::uuid[])
        """, (person_ids,))
        center_people = cursor.fetchall()
        
        if len(center_people) != len(person_ids):
            raise HTTPException(status_code=404, detail="One or more persons not found")
        
        # Build nodes and edges
        nodes = []
        edges = []
        node_ids_set = set()
        
        # Add center nodes
        for person in center_people:
            person_id = str(person['person_id'])
            nodes.append({
                'person_id': person_id,
                'name': person['full_name'],
                'title': person['headline'],
                'location': person['location'],
                'degree': 0,
                'is_center': True
            })
            node_ids_set.add(person_id)
        
        # Get connections for each center person
        connection_query = """
            WITH coworker_connections AS (
                SELECT DISTINCT 
                    e.src_person_id as source_id,
                    e.dst_person_id as connected_id,
                    e.company_id,
                    'coworker' as type,
                    e.overlap_months,
                    CASE WHEN e.last_overlap_end >= CURRENT_DATE - INTERVAL '6 months' 
                         THEN 'current' ELSE 'former' END as employment_status
                FROM edge_coemployment e
                WHERE e.src_person_id = ANY(%s::uuid[])
        """
        
        params = [person_ids]
        
        if company_filter:
            connection_query += """
                AND e.company_id IN (
                    SELECT company_id FROM company WHERE company_name ILIKE %s
                )
            """
            params.append(f"%{company_filter}%")
        
        if employment_status and employment_status != 'all':
            if employment_status == 'current':
                connection_query += " AND e.last_overlap_end >= CURRENT_DATE - INTERVAL '6 months'"
            else:  # former
                connection_query += " AND e.last_overlap_end < CURRENT_DATE - INTERVAL '6 months'"
        
        connection_query += """
            ),
            github_connections AS (
                SELECT DISTINCT 
                    gp1.person_id as source_id,
                    gp2.person_id as connected_id,
                    NULL::uuid as company_id,
                    'github_collaborator' as type,
                    NULL::integer as overlap_months,
                    NULL::text as employment_status
                FROM github_profile gp1
                JOIN github_contribution gc1 ON gp1.github_profile_id = gc1.github_profile_id
                JOIN github_contribution gc2 ON gc1.repo_id = gc2.repo_id
                JOIN github_profile gp2 ON gc2.github_profile_id = gp2.github_profile_id
                JOIN github_repository gr ON gc1.repo_id = gr.repo_id
                WHERE gp1.person_id = ANY(%s::uuid[])
                AND gp2.person_id != ALL(%s::uuid[])
        """
        params.extend([person_ids, person_ids])
        
        if technologies:
            tech_placeholders = ','.join(['%s'] * len(technologies))
            connection_query += f" AND LOWER(gr.language) IN ({tech_placeholders})"
            params.extend([tech.lower() for tech in technologies])
        
        connection_query += """
            ),
            all_connections AS (
                SELECT * FROM coworker_connections
                UNION ALL
                SELECT * FROM github_connections
            )
            SELECT 
                ac.source_id,
                ac.connected_id,
                ac.type,
                ac.company_id,
                ac.overlap_months,
                ac.employment_status,
                p.person_id,
                p.full_name,
                p.headline,
                p.location
            FROM all_connections ac
            JOIN person p ON ac.connected_id = p.person_id
            LIMIT %s
        """
        params.append(limit)
        
        cursor.execute(connection_query, params)
        all_connections = cursor.fetchall()
        
        # Process connections
        connector_candidates = {}  # Track how many center people each node connects to
        
        for conn in all_connections:
            source_id = str(conn['source_id'])
            person_id = str(conn['person_id'])
            
            # Add node if not already present
            if person_id not in node_ids_set:
                nodes.append({
                    'person_id': person_id,
                    'name': conn['full_name'],
                    'title': conn['headline'],
                    'location': conn['location'],
                    'degree': 1,
                    'is_center': False,
                    'is_connector': False  # Will update later
                })
                node_ids_set.add(person_id)
                connector_candidates[person_id] = set()
            
            # Track which center people this node connects to
            if person_id in connector_candidates:
                connector_candidates[person_id].add(source_id)
            
            # Add edge
            edges.append({
                'source': source_id,
                'target': person_id,
                'connection_type': conn['type'],
                'company_id': str(conn['company_id']) if conn['company_id'] else None,
                'overlap_months': conn['overlap_months'],
                'employment_status': conn['employment_status']
            })
        
        # Mark connectors (nodes that connect 2+ center people)
        connectors = []
        for person_id, connected_centers in connector_candidates.items():
            if len(connected_centers) >= 2:
                # Update node to mark as connector
                for node in nodes:
                    if node['person_id'] == person_id:
                        node['is_connector'] = True
                        node['connects'] = list(connected_centers)
                        connectors.append(node)
                        break
        
        # Get technology overlap if technologies filter is applied
        tech_overlap = None
        if technologies:
            cursor.execute("""
                SELECT 
                    p.person_id,
                    p.full_name,
                    array_agg(DISTINCT gr.language) as technologies,
                    COUNT(DISTINCT gr.repo_id) as repo_count
                FROM person p
                JOIN github_profile gp ON p.person_id = gp.person_id
                JOIN github_contribution gc ON gp.github_profile_id = gc.github_profile_id
                JOIN github_repository gr ON gc.repo_id = gr.repo_id
                WHERE p.person_id = ANY(%s::uuid[])
                AND LOWER(gr.language) = ANY(%s::text[])
                GROUP BY p.person_id, p.full_name
            """, (list(node_ids_set), [t.lower() for t in technologies]))
            tech_overlap = cursor.fetchall()
        
        cursor.close()
        
        result = {
            'center_people': [str(p['person_id']) for p in center_people],
            'node_count': len(nodes),
            'edge_count': len(edges),
            'connector_count': len(connectors),
            'nodes': nodes,
            'edges': edges,
            'connectors': connectors,
            'technology_overlap': tech_overlap if tech_overlap else []
        }
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error building multi-node graph: {str(e)}")


@router.get("/technologies-by-network/{person_id}")
async def get_network_technologies(
    person_id: str,
    max_degree: int = Query(2, ge=1, le=3),
    db=Depends(get_db)
):
    """
    Get technology distribution across a person's network
    
    Returns:
    - Technologies used in the network
    - Number of people using each technology
    - Top repositories for each technology
    """
    
    try:
        cursor = db.cursor(cursor_factory=RealDictCursor)
        
        # Get network people first
        cursor.execute("""
            WITH network_level_1 AS (
                SELECT DISTINCT dst_person_id as person_id
                FROM edge_coemployment
                WHERE src_person_id = %s
                LIMIT 200
            ),
            network_all AS (
                SELECT %s::uuid as person_id
                UNION
                SELECT person_id FROM network_level_1
            )
            SELECT 
                gr.language as technology,
                COUNT(DISTINCT gp.person_id) as person_count,
                COUNT(DISTINCT gr.repo_id) as repo_count,
                SUM(gr.stars) as total_stars,
                array_agg(DISTINCT gr.full_name ORDER BY gr.stars DESC) FILTER (WHERE gr.stars > 0) as top_repos
            FROM network_all na
            JOIN github_profile gp ON na.person_id = gp.person_id
            JOIN github_contribution gc ON gp.github_profile_id = gc.github_profile_id
            JOIN github_repository gr ON gc.repo_id = gr.repo_id
            WHERE gr.language IS NOT NULL
            GROUP BY gr.language
            HAVING COUNT(DISTINCT gp.person_id) >= 2
            ORDER BY COUNT(DISTINCT gp.person_id) DESC, SUM(gr.stars) DESC
            LIMIT 50
        """, (person_id, person_id))
        
        technologies = cursor.fetchall()
        
        cursor.close()
        
        return {
            'person_id': person_id,
            'technology_count': len(technologies),
            'technologies': [
                {
                    'name': tech['technology'],
                    'person_count': tech['person_count'],
                    'repo_count': tech['repo_count'],
                    'total_stars': tech['total_stars'] or 0,
                    'top_repos': (tech['top_repos'] or [])[:5]  # Top 5 repos
                }
                for tech in technologies
            ]
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching network technologies: {str(e)}")

