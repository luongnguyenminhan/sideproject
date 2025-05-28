"""
Redis Client Utility for Caching

This module provides a Redis client with caching functionality
"""

import json
import redis.asyncio as redis
from typing import Any, Optional
from app.core.config import get_settings


class RedisClient:
    """Redis client for caching operations"""
    
    def __init__(self):
        self.settings = get_settings()
        # Extract Redis URL from Celery broker URL for consistency
        redis_url = self.settings.CELERY_BROKER_URL.replace("/0", "/1")  # Use DB 1 for cache
        self.redis_client = redis.from_url(redis_url, decode_responses=True)
    
    async def get(self, key: str) -> Optional[Any]:
        """
        Get value from Redis cache
        
        Args:
            key: Cache key
            
        Returns:
            Cached value or None if not found
        """
        try:
            data = await self.redis_client.get(key)
            if data:
                return json.loads(data)
            return None
        except Exception:
            # If Redis is unavailable, return None to fallback to API call
            return None
    
    async def set(self, key: str, value: Any, ttl: int = 86400) -> bool:
        """
        Set value in Redis cache with TTL
        
        Args:
            key: Cache key
            value: Value to cache
            ttl: Time to live in seconds (default: 24 hours)
            
        Returns:
            True if successful, False otherwise
        """
        try:
            data = json.dumps(value, default=str)
            await self.redis_client.setex(key, ttl, data)
            return True
        except Exception:
            # If Redis is unavailable, continue without caching
            return False
    
    async def delete(self, key: str) -> bool:
        """
        Delete key from Redis cache
        
        Args:
            key: Cache key to delete
            
        Returns:
            True if successful, False otherwise
        """
        try:
            await self.redis_client.delete(key)
            return True
        except Exception:
            return False
    
    async def exists(self, key: str) -> bool:
        """
        Check if key exists in Redis cache
        
        Args:
            key: Cache key to check
            
        Returns:
            True if key exists, False otherwise
        """
        try:
            return bool(await self.redis_client.exists(key))
        except Exception:
            return False
    
    async def close(self):
        """Close Redis connection"""
        try:
            await self.redis_client.close()
        except Exception:
            pass


# Global Redis client instance
redis_client = RedisClient()
