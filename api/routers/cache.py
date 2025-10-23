"""
Cache Management API

Provides endpoints for cache monitoring and management.
"""

from fastapi import APIRouter, HTTPException
from api.services.cache_service import get_cache

router = APIRouter(prefix="/api/cache", tags=["cache"])


@router.get("/status")
async def get_cache_status():
    """
    Get cache statistics and health status.
    
    Returns:
    - Connection status
    - Number of cached keys
    - Memory usage
    - Hit rate
    - Hits and misses
    """
    cache = get_cache()
    stats = cache.get_stats()
    
    return {
        "success": True,
        "cache": stats
    }


@router.post("/clear")
async def clear_cache():
    """
    Clear all cached data.
    
    USE WITH CAUTION: This will clear ALL cached data.
    """
    cache = get_cache()
    
    if not cache.is_available():
        raise HTTPException(status_code=503, detail="Cache service unavailable")
    
    cache.clear_all()
    
    return {
        "success": True,
        "message": "Cache cleared successfully"
    }


@router.delete("/key/{key}")
async def delete_cache_key(key: str):
    """
    Delete a specific cache key.
    
    Args:
        key: The cache key to delete
    """
    cache = get_cache()
    
    if not cache.is_available():
        raise HTTPException(status_code=503, detail="Cache service unavailable")
    
    success = cache.delete(key)
    
    if success:
        return {
            "success": True,
            "message": f"Key '{key}' deleted successfully"
        }
    else:
        raise HTTPException(status_code=404, detail=f"Key '{key}' not found")


@router.delete("/pattern/{pattern}")
async def delete_cache_pattern(pattern: str):
    """
    Delete all keys matching a pattern.
    
    Args:
        pattern: Pattern to match (e.g., "network_graph:*")
    """
    cache = get_cache()
    
    if not cache.is_available():
        raise HTTPException(status_code=503, detail="Cache service unavailable")
    
    cache.delete_pattern(pattern)
    
    return {
        "success": True,
        "message": f"All keys matching '{pattern}' deleted successfully"
    }

