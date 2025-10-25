"""
ABOUTME: FastAPI router for advanced graph reasoning endpoints.
ABOUTME: Provides REST API for network analysis, community detection, and graph intelligence.
"""

from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional, Dict, Any
from pydantic import BaseModel
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from config import get_db_context
from api.services.graph_reasoning_service import GraphReasoningService

router = APIRouter(prefix="/api/graph-reasoning", tags=["graph-reasoning"])

# Global graph service (initialized lazily)
_graph_service: Optional[GraphReasoningService] = None
_graph_initialized: bool = False


def get_graph_service(require_graph: bool = True) -> GraphReasoningService:
    """
    Get or initialize graph reasoning service.
    
    Args:
        require_graph: If True, raises error if graph not built. If False, returns service anyway.
    
    Returns:
        GraphReasoningService instance
    """
    global _graph_service, _graph_initialized
    
    # Initialize service object (fast)
    if _graph_service is None:
        with get_db_context() as conn:
            _graph_service = GraphReasoningService(db_connection=conn)
    
    # Check if graph is built
    if require_graph and not _graph_initialized:
        raise HTTPException(
            status_code=503,
            detail="Graph not initialized. Please call POST /api/graph-reasoning/rebuild-graph first."
        )
    
    return _graph_service


# Pydantic models
class SimilarPersonRequest(BaseModel):
    person_id: str
    top_k: int = 10
    min_similarity: float = 0.5


class PathSamplingRequest(BaseModel):
    start_concept: str
    end_concept: str
    max_length: int = 5


class CommunityRequest(BaseModel):
    algorithm: str = 'louvain'


@router.get("/stats")
async def get_graph_statistics(
    compute_betweenness: bool = Query(False, description="Compute expensive betweenness centrality"),
    use_cache: bool = Query(True, description="Use cached results if available")
):
    """
    Get comprehensive graph statistics.
    
    Fast stats (always computed):
    - Node and edge counts
    - Density and clustering metrics
    - Degree distribution
    
    Slow stats (only if compute_betweenness=true):
    - Betweenness centrality
    - Top central nodes
    
    Note: Betweenness computation can be slow for graphs >1000 nodes.
    Results are cached for 1 hour.
    """
    service = get_graph_service()
    
    try:
        stats = service.compute_graph_statistics(
            use_cache=use_cache,
            compute_betweenness=compute_betweenness
        )
        return {
            "status": "success",
            "statistics": stats
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error computing statistics: {str(e)}")


@router.get("/similar-people/{person_id}")
async def find_similar_people(
    person_id: str,
    top_k: int = Query(10, le=50),
    min_similarity: float = Query(0.5, ge=0.0, le=1.0)
):
    """
    Find people similar to the given person based on network embeddings.
    
    Uses node embeddings to compute similarity scores.
    """
    service = get_graph_service()
    
    try:
        similar = service.find_similar_nodes(
            node_id=person_id,
            top_k=top_k,
            min_similarity=min_similarity
        )
        
        return {
            "status": "success",
            "person_id": person_id,
            "similar_people": similar,
            "count": len(similar)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error finding similar people: {str(e)}")


@router.get("/key-connectors")
async def get_key_connectors(
    min_betweenness: float = Query(0.01, ge=0.0, le=1.0),
    limit: int = Query(20, le=100)
):
    """
    Find key connector nodes with high betweenness centrality.
    
    These are people who bridge different communities and have high influence.
    """
    service = get_graph_service()
    
    try:
        connectors = service.find_key_connectors(min_betweenness=min_betweenness)
        
        return {
            "status": "success",
            "key_connectors": connectors[:limit],
            "total_found": len(connectors)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error finding key connectors: {str(e)}")


@router.post("/detect-communities")
async def detect_communities(
    algorithm: str = Query('louvain', regex='^(louvain|label_propagation|greedy_modularity)$')
):
    """
    Detect communities in the network.
    
    Algorithms:
    - louvain: Best quality, requires python-louvain package
    - label_propagation: Fast, good quality
    - greedy_modularity: Greedy optimization
    """
    service = get_graph_service()
    
    try:
        communities = service.detect_communities(algorithm=algorithm)
        
        # Return summary (full data would be huge)
        summary = []
        for i, community in enumerate(communities[:50]):  # Top 50 communities
            summary.append({
                'community_id': i,
                'size': len(community),
                'sample_members': list(community)[:5]  # Sample of 5 members
            })
        
        return {
            "status": "success",
            "algorithm": algorithm,
            "num_communities": len(communities),
            "communities": summary
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error detecting communities: {str(e)}")


@router.get("/community/{community_id}")
async def get_community_details(community_id: int):
    """
    Get detailed information about a specific community.
    
    Returns:
    - Community size
    - Density and clustering
    - Top members by influence
    """
    service = get_graph_service()
    
    try:
        # Ensure communities are detected
        if not service.communities:
            service.detect_communities()
        
        info = service.get_community_info(community_id)
        
        return {
            "status": "success",
            "community": info
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting community info: {str(e)}")


@router.post("/path-sampling")
async def sample_paths_between_concepts(request: PathSamplingRequest):
    """
    Sample innovative paths between two concepts.
    
    This implements path sampling from GraphReasoning to find
    novel connections between dissimilar concepts.
    
    Example:
    - start_concept: "blockchain"
    - end_concept: "machine learning"
    - Returns: Paths connecting blockchain experts to ML experts
    """
    service = get_graph_service()
    
    try:
        paths = service.sample_path_between_concepts(
            start_concept=request.start_concept,
            end_concept=request.end_concept,
            max_length=request.max_length
        )
        
        return {
            "status": "success",
            "start_concept": request.start_concept,
            "end_concept": request.end_concept,
            "paths": paths,
            "num_paths": len(paths)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error sampling paths: {str(e)}")


@router.get("/node-embedding/{person_id}")
async def get_node_embedding(person_id: str):
    """
    Get the embedding vector for a person node.
    
    Useful for custom similarity calculations.
    """
    service = get_graph_service()
    
    if person_id not in service.node_embeddings:
        raise HTTPException(status_code=404, detail=f"Person {person_id} not found in graph")
    
    embedding = service.node_embeddings[person_id]
    
    return {
        "status": "success",
        "person_id": person_id,
        "embedding": embedding.tolist(),
        "dimension": len(embedding)
    }


@router.get("/similarity/{person1_id}/{person2_id}")
async def compute_similarity(person1_id: str, person2_id: str):
    """
    Compute similarity score between two people.
    
    Uses cosine similarity on node embeddings.
    """
    service = get_graph_service()
    
    try:
        similarity = service.compute_node_similarity(person1_id, person2_id)
        
        return {
            "status": "success",
            "person1_id": person1_id,
            "person2_id": person2_id,
            "similarity_score": float(similarity)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error computing similarity: {str(e)}")


@router.post("/rebuild-graph")
async def rebuild_graph(limit: Optional[int] = Query(None, le=50000)):
    """
    Rebuild the graph from database.
    
    Use this after significant data changes.
    Note: Betweenness centrality is NOT computed during rebuild for performance.
    """
    global _graph_service, _graph_initialized
    
    try:
        with get_db_context() as conn:
            _graph_service = GraphReasoningService(db_connection=conn)
            _graph_service.build_graph_from_database(limit=limit)
            _graph_service.compute_node_embeddings()
        
        # Mark as initialized
        _graph_initialized = True
        
        # Get fast stats (without betweenness)
        stats = _graph_service.compute_graph_statistics(compute_betweenness=False)
        
        return {
            "status": "success",
            "message": "Graph rebuilt successfully",
            "statistics": stats
        }
    except Exception as e:
        _graph_initialized = False
        raise HTTPException(status_code=500, detail=f"Error rebuilding graph: {str(e)}")


@router.get("/export/graphml")
async def export_to_graphml(output_filename: str = "talent_graph.graphml"):
    """
    Export graph to GraphML format.
    
    Useful for external analysis in tools like Gephi or Cytoscape.
    """
    service = get_graph_service()
    
    try:
        output_path = f"./exports/{output_filename}"
        os.makedirs("./exports", exist_ok=True)
        
        service.export_graph_to_graphml(output_path)
        
        return {
            "status": "success",
            "message": f"Graph exported to {output_path}",
            "path": output_path
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error exporting graph: {str(e)}")


@router.get("/export/json")
async def export_to_json(output_filename: str = "talent_graph.json"):
    """
    Export graph to JSON format.
    """
    service = get_graph_service()
    
    try:
        output_path = f"./exports/{output_filename}"
        os.makedirs("./exports", exist_ok=True)
        
        service.export_graph_to_json(output_path)
        
        return {
            "status": "success",
            "message": f"Graph exported to {output_path}",
            "path": output_path
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error exporting graph: {str(e)}")


@router.get("/info")
async def get_graph_info():
    """
    Get quick graph info without expensive computations.
    
    Returns basic info about graph state and cache status.
    This endpoint works even if graph is not initialized.
    """
    global _graph_initialized
    
    try:
        service = get_graph_service(require_graph=False)
        info = service.get_graph_info()
        info['initialized'] = _graph_initialized
        return {
            "status": "success",
            "graph_info": info
        }
    except Exception as e:
        return {
            "status": "success",
            "graph_info": {
                "status": "not_initialized",
                "initialized": False,
                "message": "Call POST /api/graph-reasoning/rebuild-graph to initialize"
            }
        }


@router.post("/add-person")
async def add_person(person_data: Dict[str, Any]):
    """
    Add a new person node to the graph.
    
    Body should contain:
    - person_id (required)
    - full_name
    - headline
    - location
    - github_username
    - github_followers
    - github_repos
    """
    service = get_graph_service()
    
    try:
        added = service.add_person_node(person_data)
        return {
            "status": "success" if added else "already_exists",
            "person_id": person_data.get('person_id'),
            "added": added
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error adding person: {str(e)}")


@router.post("/add-edge")
async def add_edge(
    src_person_id: str,
    dst_person_id: str,
    edge_type: str,
    attributes: Optional[Dict[str, Any]] = None
):
    """
    Add a collaboration edge between two people.
    
    Args:
    - src_person_id: Source person UUID
    - dst_person_id: Destination person UUID
    - edge_type: 'github_collaboration' or 'coemployment'
    - attributes: Optional edge attributes (strength, shared_repos, etc.)
    """
    service = get_graph_service()
    
    try:
        added = service.add_collaboration_edge(
            src_person_id=src_person_id,
            dst_person_id=dst_person_id,
            edge_type=edge_type,
            **(attributes or {})
        )
        return {
            "status": "success" if added else "already_exists",
            "edge": f"{src_person_id} -> {dst_person_id}",
            "added": added
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error adding edge: {str(e)}")

