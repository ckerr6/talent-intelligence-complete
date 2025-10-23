"""
Redis Caching Service

Provides caching functionality for expensive queries.
"""

import redis
import json
import os
import logging
from typing import Optional, Any
from functools import wraps

logger = logging.getLogger(__name__)


class CacheService:
    """Redis caching service for expensive queries."""
    
    def __init__(self):
        """Initialize Redis connection."""
        self.redis_client = None
        self._initialize()
    
    def _initialize(self):
        """Initialize Redis client with connection pooling."""
        try:
            redis_host = os.getenv('REDIS_HOST', 'localhost')
            redis_port = int(os.getenv('REDIS_PORT', 6379))
            redis_db = int(os.getenv('REDIS_DB', 0))
            
            self.redis_client = redis.Redis(
                host=redis_host,
                port=redis_port,
                db=redis_db,
                decode_responses=True,
                socket_connect_timeout=2,
                socket_timeout=2
            )
            
            # Test connection
            self.redis_client.ping()
            logger.info(f"✅ Redis connected: {redis_host}:{redis_port}")
            
        except Exception as e:
            logger.warning(f"⚠️  Redis connection failed: {e}. Caching disabled.")
            self.redis_client = None
    
    def is_available(self) -> bool:
        """Check if Redis is available."""
        if not self.redis_client:
            return False
        try:
            self.redis_client.ping()
            return True
        except:
            return False
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        if not self.is_available():
            return None
        
        try:
            value = self.redis_client.get(key)
            if value:
                return json.loads(value)
            return None
        except Exception as e:
            logger.error(f"Cache get error for key {key}: {e}")
            return None
    
    def set(self, key: str, value: Any, ttl: int = 300):
        """
        Set value in cache with TTL (time to live).
        
        Args:
            key: Cache key
            value: Value to cache (will be JSON serialized)
            ttl: Time to live in seconds (default 5 minutes)
        """
        if not self.is_available():
            return False
        
        try:
            serialized = json.dumps(value)
            self.redis_client.setex(key, ttl, serialized)
            return True
        except Exception as e:
            logger.error(f"Cache set error for key {key}: {e}")
            return False
    
    def delete(self, key: str):
        """Delete key from cache."""
        if not self.is_available():
            return False
        
        try:
            self.redis_client.delete(key)
            return True
        except Exception as e:
            logger.error(f"Cache delete error for key {key}: {e}")
            return False
    
    def delete_pattern(self, pattern: str):
        """Delete all keys matching pattern."""
        if not self.is_available():
            return False
        
        try:
            keys = self.redis_client.keys(pattern)
            if keys:
                self.redis_client.delete(*keys)
            return True
        except Exception as e:
            logger.error(f"Cache delete pattern error for {pattern}: {e}")
            return False
    
    def clear_all(self):
        """Clear all cache (use with caution!)."""
        if not self.is_available():
            return False
        
        try:
            self.redis_client.flushdb()
            logger.info("🗑️  Cache cleared")
            return True
        except Exception as e:
            logger.error(f"Cache clear error: {e}")
            return False
    
    def get_stats(self) -> dict:
        """Get cache statistics."""
        if not self.is_available():
            return {"status": "unavailable"}
        
        try:
            info = self.redis_client.info()
            return {
                "status": "connected",
                "keys": self.redis_client.dbsize(),
                "memory_used": info.get('used_memory_human', 'N/A'),
                "hits": info.get('keyspace_hits', 0),
                "misses": info.get('keyspace_misses', 0),
                "hit_rate": round(
                    info.get('keyspace_hits', 0) / 
                    max(info.get('keyspace_hits', 0) + info.get('keyspace_misses', 0), 1) * 100, 
                    2
                )
            }
        except Exception as e:
            logger.error(f"Cache stats error: {e}")
            return {"status": "error", "message": str(e)}


# Global cache instance
_cache_instance = None

def get_cache() -> CacheService:
    """Get or create cache service instance."""
    global _cache_instance
    if _cache_instance is None:
        _cache_instance = CacheService()
    return _cache_instance


def cache_result(key_prefix: str, ttl: int = 300):
    """
    Decorator to cache function results.
    
    Args:
        key_prefix: Prefix for cache key (function args will be appended)
        ttl: Time to live in seconds
    
    Usage:
        @cache_result("network_graph", ttl=600)
        async def get_network_graph(person_id: str):
            # expensive operation
            return data
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            cache = get_cache()
            
            # Build cache key from function args
            key_parts = [key_prefix]
            key_parts.extend(str(arg) for arg in args if arg)
            key_parts.extend(f"{k}={v}" for k, v in sorted(kwargs.items()) if v)
            cache_key = ":".join(key_parts)
            
            # Try to get from cache
            cached_result = cache.get(cache_key)
            if cached_result is not None:
                logger.info(f"✨ Cache hit: {cache_key}")
                return cached_result
            
            # Execute function
            logger.info(f"🔄 Cache miss: {cache_key}")
            result = await func(*args, **kwargs)
            
            # Cache result
            cache.set(cache_key, result, ttl)
            
            return result
        return wrapper
    return decorator

