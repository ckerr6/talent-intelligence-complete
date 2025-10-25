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

# Global graph service (loaded on startup)
_graph_service: Optional[GraphReasoningService] = None


def get_graph_service() -> GraphReasoningService:
    """Get or initialize graph reasoning service"""
    global _graph_service
    
    if _graph_service is None:
        with get_db_context() as conn:
            _graph_service = GraphReasoningService(db_connection=conn)
            _graph_service.build_graph_from_database(limit=10000)  # Limit for performance
            _graph_service.compute_node_embeddings()
    
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
async def get_graph_statistics():
    """
    Get comprehensive graph statistics.
    
    Returns:
    - Node and edge counts
    - Density and clustering metrics
    - Top central nodes
    """
    service = get_graph_service()
    
    try:
        stats = service.compute_graph_statistics()
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
    """
    global _graph_service
    
    try:
        with get_db_context() as conn:
            _graph_service = GraphReasoningService(db_connection=conn)
            _graph_service.build_graph_from_database(limit=limit)
            _graph_service.compute_node_embeddings()
        
        stats = _graph_service.compute_graph_statistics()
        
        return {
            "status": "success",
            "message": "Graph rebuilt successfully",
            "statistics": stats
        }
    except Exception as e:
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

