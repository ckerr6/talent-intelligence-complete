"""
Network Analysis API Router
Provides endpoints for network graph visualization, pathfinding, and connection analysis
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Optional
from collections import deque
from psycopg2.extras import RealDictCursor

from api.dependencies import get_db
from api.crud import network as network_crud

router = APIRouter(prefix="/api/network", tags=["network"])


@router.get("/connections/{person_id}")
async def get_connections(
    person_id: str,
    connection_type: Optional[str] = Query(None, description="Filter by 'coworker' or 'github_collaborator'"),
    limit: int = Query(100, ge=1, le=500),
    db=Depends(get_db)
):
    """
    Get all connections for a person
    
    Returns list of connected people with connection metadata
    """
    
    try:
        connections = network_crud.get_connections(
            person_id=person_id,
            connection_type=connection_type,
            limit=limit,
            db=db
        )
        
        return {
            'person_id': person_id,
            'total_connections': len(connections),
            'connections': connections
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching connections: {str(e)}")


@router.get("/path/{source_id}/{target_id}")
async def find_path(
    source_id: str,
    target_id: str,
    max_depth: int = Query(3, ge=1, le=5),
    db=Depends(get_db)
):
    """
    Find shortest path between two people
    
    Returns path with nodes and edges, or 404 if no path exists
    """
    
    if source_id == target_id:
        return {
            'path_length': 0,
            'nodes': [{
                'person_id': source_id,
                'position': 0
            }],
            'edges': []
        }
    
    try:
        path = network_crud.find_shortest_path(
            source_person_id=source_id,
            target_person_id=target_id,
            max_depth=max_depth,
            db=db
        )
        
        if path is None:
            raise HTTPException(
                status_code=404,
                detail=f"No path found between {source_id} and {target_id} within {max_depth} degrees"
            )
        
        return path
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error finding path: {str(e)}")


@router.get("/mutual/{person1_id}/{person2_id}")
async def get_mutual_connections(
    person1_id: str,
    person2_id: str,
    limit: int = Query(50, ge=1, le=200),
    db=Depends(get_db)
):
    """
    Find mutual connections between two people
    
    Returns list of people connected to both
    """
    
    try:
        mutual = network_crud.get_mutual_connections(
            person1_id=person1_id,
            person2_id=person2_id,
            limit=limit,
            db=db
        )
        
        return {
            'person1_id': person1_id,
            'person2_id': person2_id,
            'mutual_count': len(mutual),
            'mutual_connections': mutual
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error finding mutual connections: {str(e)}")


@router.get("/distance/{source_id}/{target_id}")
async def get_network_distance(
    source_id: str,
    target_id: str,
    db=Depends(get_db)
):
    """
    Calculate degrees of separation between two people
    
    Returns number of hops or null if not connected within 3 degrees
    """
    
    try:
        distance = network_crud.calculate_network_distance(
            source_person_id=source_id,
            target_person_id=target_id,
            db=db
        )
        
        return {
            'source_id': source_id,
            'target_id': target_id,
            'degrees_of_separation': distance,
            'connected': distance is not None
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error calculating distance: {str(e)}")


@router.get("/stats/{person_id}")
async def get_network_stats(
    person_id: str,
    db=Depends(get_db)
):
    """
    Get network statistics for a person
    
    Returns connection counts, top companies, etc.
    """
    
    try:
        stats = network_crud.get_network_stats(person_id=person_id, db=db)
        
        return {
            'person_id': person_id,
            **stats
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching network stats: {str(e)}")


@router.get("/graph")
async def get_network_graph(
    center: str = Query(..., description="Center person UUID"),
    max_degree: int = Query(2, ge=1, le=3, description="Maximum degrees of separation"),
    limit: int = Query(100, ge=10, le=500, description="Maximum nodes to return"),
    company_filter: Optional[str] = Query(None, description="Filter connections by company"),
    repo_filter: Optional[str] = Query(None, description="Filter connections by GitHub repo"),
    db=Depends(get_db)
):
    """
    Get network graph data for visualization
    
    Returns nodes and edges formatted for vis.js/d3
    Performs BFS from center person up to max_degree hops
    """
    
    try:
        nodes = []
        edges = []
        visited = set()
        
        # BFS to build graph
        queue = deque([(center, 0)])
        
        cursor = db.cursor(cursor_factory=RealDictCursor)
        
        while queue and len(nodes) < limit:
            person_id, degree = queue.popleft()
            
            if person_id in visited or degree > max_degree:
                continue
            
            visited.add(person_id)
            
            # Get person details
            cursor.execute(
                "SELECT person_id, full_name, headline, location FROM person WHERE person_id = %s",
                (person_id,)
            )
            
            person = cursor.fetchone()
            
            if not person:
                continue
            
            nodes.append({
                'person_id': person['person_id'],
                'name': person['full_name'],
                'title': person['headline'],
                'location': person['location'],
                'degree': degree
            })
            
            # Get connections
            connections_query = """
                SELECT DISTINCT dst_person_id as connected_id, 'coworker' as type
                FROM edge_coemployment
                WHERE src_person_id = %s
            """
            
            params = [person_id]
            
            if company_filter:
                connections_query += " AND company_id IN (SELECT company_id FROM company WHERE company_name ILIKE %s)"
                params.append(f"%{company_filter}%")
            
            connections_query += """
                UNION
                SELECT DISTINCT p2.person_id, 'github_collaborator' as type
                FROM github_contribution gc1
                JOIN github_contribution gc2 ON gc1.repo_id = gc2.repo_id
                JOIN github_profile gp2 ON gc2.github_profile_id = gp2.github_profile_id
                JOIN person p2 ON gp2.person_id = p2.person_id
                JOIN github_profile gp1 ON gc1.github_profile_id = gp1.github_profile_id
                WHERE gp1.person_id = %s AND p2.person_id != %s
            """
            
            params.extend([person_id, person_id])
            
            if repo_filter:
                connections_query += " AND gc1.repo_id IN (SELECT repo_id FROM github_repository WHERE full_name ILIKE %s)"
                params.append(f"%{repo_filter}%")
            
            connections_query += " LIMIT 50"
            
            cursor.execute(connections_query, params)
            connections = cursor.fetchall()
            
            for conn in connections:
                conn_id = conn['connected_id']
                edges.append({
                    'source': person_id,
                    'target': conn_id,
                    'connection_type': conn['type']
                })
                
                if degree < max_degree and len(visited) < limit:
                    queue.append((conn_id, degree + 1))
        
        cursor.close()
        
        return {
            'center_person_id': center,
            'max_degree': max_degree,
            'node_count': len(nodes),
            'edge_count': len(edges),
            'nodes': nodes,
            'edges': edges
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error building network graph: {str(e)}")

