# cache_helper.py
import redis
import json
import hashlib
import logging
import os
from typing import Any, Optional, Dict
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class CacheHelper:
    """
    Redis cache helper for face recognition search results and other cached data
    """
    
    def __init__(self, redis_url: str = None, default_ttl: int = 3600):
        """
        Initialize cache helper
        
        Args:
            redis_url: Redis connection URL
            default_ttl: Default time-to-live for cached items in seconds
        """
        self.redis_url = redis_url or os.getenv('REDIS_URL', 'redis://localhost:6379/0')
        self.default_ttl = default_ttl
        self.redis_client = None
        self._connect()
    
    def _connect(self):
        """Connect to Redis"""
        try:
            self.redis_client = redis.StrictRedis.from_url(self.redis_url, decode_responses=True)
            # Test connection
            self.redis_client.ping()
            logger.info("Connected to Redis successfully")
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {str(e)}")
            self.redis_client = None
    
    def _ensure_connection(self):
        """Ensure Redis connection is available"""
        if not self.redis_client:
            self._connect()
        return self.redis_client is not None
    
    def generate_search_key(self, query_params: Dict) -> str:
        """
        Generate a cache key for search results
        
        Args:
            query_params: Dictionary containing search parameters
            
        Returns:
            Cache key string
        """
        # Create a deterministic string from query parameters
        param_string = json.dumps(query_params, sort_keys=True)
        cache_key = hashlib.sha256(param_string.encode()).hexdigest()
        return f"search:{cache_key}"
    
    def get_cached_search_result(self, query_params: Dict) -> Optional[Dict]:
        """
        Get cached search result
        
        Args:
            query_params: Dictionary containing search parameters
            
        Returns:
            Cached result or None if not found
        """
        if not self._ensure_connection():
            return None
        
        try:
            cache_key = self.generate_search_key(query_params)
            cached_data = self.redis_client.get(cache_key)
            
            if cached_data:
                result = json.loads(cached_data)
                logger.info(f"Cache hit for search key: {cache_key}")
                return result
            else:
                logger.info(f"Cache miss for search key: {cache_key}")
                return None
                
        except Exception as e:
            logger.error(f"Error retrieving cached search result: {str(e)}")
            return None
    
    def cache_search_result(self, query_params: Dict, result: Dict, ttl: int = None) -> bool:
        """
        Cache search result
        
        Args:
            query_params: Dictionary containing search parameters
            result: Search result to cache
            ttl: Time-to-live in seconds (uses default if not specified)
            
        Returns:
            True if successfully cached, False otherwise
        """
        if not self._ensure_connection():
            return False
        
        try:
            cache_key = self.generate_search_key(query_params)
            ttl = ttl or self.default_ttl
            
            # Add cache metadata
            cached_result = {
                'data': result,
                'cached_at': datetime.utcnow().isoformat(),
                'ttl': ttl
            }
            
            success = self.redis_client.set(
                cache_key, 
                json.dumps(cached_result), 
                ex=ttl
            )
            
            if success:
                logger.info(f"Cached search result with key: {cache_key}, TTL: {ttl}s")
            
            return success
            
        except Exception as e:
            logger.error(f"Error caching search result: {str(e)}")
            return False
    
    def invalidate_search_cache(self, pattern: str = "search:*") -> int:
        """
        Invalidate cached search results
        
        Args:
            pattern: Redis key pattern to match for deletion
            
        Returns:
            Number of keys deleted
        """
        if not self._ensure_connection():
            return 0
        
        try:
            keys = self.redis_client.keys(pattern)
            if keys:
                deleted = self.redis_client.delete(*keys)
                logger.info(f"Invalidated {deleted} cached search results")
                return deleted
            return 0
            
        except Exception as e:
            logger.error(f"Error invalidating search cache: {str(e)}")
            return 0
    
    def get_cache_stats(self) -> Dict:
        """
        Get cache statistics
        
        Returns:
            Dictionary containing cache statistics
        """
        if not self._ensure_connection():
            return {}
        
        try:
            info = self.redis_client.info()
            search_keys = len(self.redis_client.keys("search:*"))
            
            return {
                'redis_version': info.get('redis_version', 'unknown'),
                'used_memory': info.get('used_memory_human', 'unknown'),
                'connected_clients': info.get('connected_clients', 0),
                'total_search_keys': search_keys,
                'keyspace_hits': info.get('keyspace_hits', 0),
                'keyspace_misses': info.get('keyspace_misses', 0),
                'hit_rate': self._calculate_hit_rate(
                    info.get('keyspace_hits', 0), 
                    info.get('keyspace_misses', 0)
                )
            }
            
        except Exception as e:
            logger.error(f"Error getting cache stats: {str(e)}")
            return {}
    
    def _calculate_hit_rate(self, hits: int, misses: int) -> float:
        """Calculate cache hit rate percentage"""
        total = hits + misses
        if total == 0:
            return 0.0
        return round((hits / total) * 100, 2)
    
    def set_generic_cache(self, key: str, value: Any, ttl: int = None) -> bool:
        """
        Set a generic cache entry
        
        Args:
            key: Cache key
            value: Value to cache (will be JSON serialized)
            ttl: Time-to-live in seconds
            
        Returns:
            True if successfully cached, False otherwise
        """
        if not self._ensure_connection():
            return False
        
        try:
            ttl = ttl or self.default_ttl
            serialized_value = json.dumps(value) if not isinstance(value, str) else value
            return self.redis_client.set(key, serialized_value, ex=ttl)
            
        except Exception as e:
            logger.error(f"Error setting generic cache: {str(e)}")
            return False
    
    def get_generic_cache(self, key: str) -> Optional[Any]:
        """
        Get a generic cache entry
        
        Args:
            key: Cache key
            
        Returns:
            Cached value or None if not found
        """
        if not self._ensure_connection():
            return None
        
        try:
            cached_value = self.redis_client.get(key)
            if cached_value:
                try:
                    return json.loads(cached_value)
                except json.JSONDecodeError:
                    return cached_value
            return None
            
        except Exception as e:
            logger.error(f"Error getting generic cache: {str(e)}")
            return None

# Global cache instance
cache_helper = CacheHelper()

