"""
Network Analysis API Router
Provides endpoints for network graph visualization, pathfinding, and connection analysis
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Optional
from collections import deque
from psycopg2.extras import RealDictCursor
import logging

from api.dependencies import get_db
from api.crud import network as network_crud
from api.services.cache_service import get_cache

router = APIRouter(prefix="/api/network", tags=["network"])
logger = logging.getLogger(__name__)


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
    Get network graph data for visualization - OPTIMIZED WITH CACHING
    
    Returns nodes and edges formatted for vis.js/d3
    Uses optimized batch queries instead of N+1 pattern
    Results are cached for 10 minutes
    """
    
    # Build cache key from parameters
    cache = get_cache()
    cache_key = f"network_graph:{center}:{max_degree}:{limit}"
    if company_filter:
        cache_key += f":company={company_filter}"
    if repo_filter:
        cache_key += f":repo={repo_filter}"
    
    # Try to get from cache
    cached_result = cache.get(cache_key)
    if cached_result:
        logger.info(f"✨ Cache hit: network_graph for {center}")
        return cached_result
    
    logger.info(f"🔄 Cache miss: network_graph for {center}, querying database...")
    
    try:
        cursor = db.cursor(cursor_factory=RealDictCursor)
        
        # Get center person
        cursor.execute(
            "SELECT person_id, full_name, headline, location FROM person WHERE person_id = %s",
            (center,)
        )
        center_person = cursor.fetchone()
        
        if not center_person:
            raise HTTPException(status_code=404, detail="Person not found")
        
        nodes = [{
            'person_id': str(center_person['person_id']),
            'name': center_person['full_name'],
            'title': center_person['headline'],
            'location': center_person['location'],
            'degree': 0
        }]
        
        # OPTIMIZED: Get all 1st degree connections in ONE batch query
        conn_query = """
            WITH coworker_connections AS (
                SELECT DISTINCT 
                    e.dst_person_id as connected_id,
                    'coworker' as type,
                    %s as source_id
                FROM edge_coemployment e
                WHERE e.src_person_id = %s
        """
        params = [center, center]
        
        if company_filter:
            conn_query += """
                AND e.company_id IN (
                    SELECT company_id FROM company 
                    WHERE company_name ILIKE %s
                )
            """
            params.append(f"%{company_filter}%")
        
        conn_query += """
                LIMIT 150
            ),
            github_connections AS (
                SELECT DISTINCT 
                    p2.person_id as connected_id,
                    'github_collaborator' as type,
                    %s as source_id
                FROM github_profile gp1
                JOIN github_contribution gc1 ON gp1.github_profile_id = gc1.github_profile_id
                JOIN github_contribution gc2 ON gc1.repo_id = gc2.repo_id
                JOIN github_profile gp2 ON gc2.github_profile_id = gp2.github_profile_id
                JOIN person p2 ON gp2.person_id = p2.person_id
                WHERE gp1.person_id = %s 
                AND p2.person_id != %s
        """
        params.extend([center, center, center])
        
        if repo_filter:
            conn_query += """
                AND gc1.repo_id IN (
                    SELECT repo_id FROM github_repository 
                    WHERE full_name ILIKE %s
                )
            """
            params.append(f"%{repo_filter}%")
        
        conn_query += """
                LIMIT 150
            ),
            all_connections AS (
                SELECT * FROM coworker_connections
                UNION
                SELECT * FROM github_connections
            )
            SELECT 
                ac.source_id,
                ac.connected_id,
                ac.type,
                p.person_id,
                p.full_name,
                p.headline,
                p.location
            FROM all_connections ac
            JOIN person p ON ac.connected_id = p.person_id
            LIMIT %s
        """
        params.append(limit - 1)  # -1 for center node
        
        cursor.execute(conn_query, params)
        degree1_connections = cursor.fetchall()
        
        edges = []
        degree1_ids = set()
        
        for conn in degree1_connections:
            person_id = str(conn['person_id'])
            degree1_ids.add(person_id)
            
            nodes.append({
                'person_id': person_id,
                'name': conn['full_name'],
                'title': conn['headline'],
                'location': conn['location'],
                'degree': 1
            })
            edges.append({
                'source': center,
                'target': person_id,
                'connection_type': conn['type']
            })
        
        # For degree 2+, add more efficient queries if needed
        if max_degree >= 2 and len(nodes) < limit and len(degree1_ids) > 0:
            # Get 2nd degree connections in batch
            degree1_list = list(degree1_ids)[:20]  # Limit to top 20 1st degree for 2nd degree expansion
            
            conn_query_2 = """
                WITH source_people AS (
                    SELECT unnest(%s::uuid[]) as person_id
                ),
                coworker_connections AS (
                    SELECT DISTINCT 
                        e.src_person_id as source_id,
                        e.dst_person_id as connected_id,
                        'coworker' as type
                    FROM edge_coemployment e
                    WHERE e.src_person_id = ANY(%s::uuid[])
                    AND e.dst_person_id != %s
            """
            params_2 = [degree1_list, degree1_list, center]
            
            if company_filter:
                conn_query_2 += """
                    AND e.company_id IN (
                        SELECT company_id FROM company 
                        WHERE company_name ILIKE %s
                    )
                """
                params_2.append(f"%{company_filter}%")
            
            conn_query_2 += """
                    LIMIT 100
                ),
                all_connections AS (
                    SELECT * FROM coworker_connections
                )
                SELECT 
                    ac.source_id,
                    ac.connected_id,
                    ac.type,
                    p.person_id,
                    p.full_name,
                    p.headline,
                    p.location
                FROM all_connections ac
                JOIN person p ON ac.connected_id = p.person_id
                WHERE p.person_id != %s
                LIMIT %s
            """
            params_2.extend([center, limit - len(nodes)])
            
            cursor.execute(conn_query_2, params_2)
            degree2_connections = cursor.fetchall()
            
            degree2_ids = set()
            for conn in degree2_connections:
                person_id = str(conn['person_id'])
                
                # Skip if already in graph
                if person_id not in degree2_ids and person_id not in degree1_ids and person_id != center:
                    degree2_ids.add(person_id)
                    
                    nodes.append({
                        'person_id': person_id,
                        'name': conn['full_name'],
                        'title': conn['headline'],
                        'location': conn['location'],
                        'degree': 2
                    })
                
                edges.append({
                    'source': str(conn['source_id']),
                    'target': person_id,
                    'connection_type': conn['type']
                })
        
        cursor.close()
        
        result = {
            'center_person_id': center,
            'max_degree': max_degree,
            'node_count': len(nodes),
            'edge_count': len(edges),
            'nodes': nodes,
            'edges': edges
        }
        
        # Cache result for 10 minutes (600 seconds)
        cache.set(cache_key, result, ttl=600)
        logger.info(f"💾 Cached network_graph for {center}")
        
        return result
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error building network graph: {str(e)}")

