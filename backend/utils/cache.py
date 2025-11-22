"""Caching utilities for API responses."""

from typing import Any, Optional
from functools import wraps
import json
import hashlib
import time


class SimpleCache:
    """Simple in-memory cache with TTL."""
    
    def __init__(self, ttl: int = 3600):
        """
        Initialize cache.
        
        Args:
            ttl: Time to live in seconds (default: 1 hour)
        """
        self._cache: dict = {}
        self.ttl = ttl
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache if not expired."""
        if key in self._cache:
            value, timestamp = self._cache[key]
            if time.time() - timestamp < self.ttl:
                return value
            else:
                del self._cache[key]
        return None
    
    def set(self, key: str, value: Any) -> None:
        """Set value in cache."""
        self._cache[key] = (value, time.time())
    
    def clear(self) -> None:
        """Clear all cache entries."""
        self._cache.clear()


# Global cache instance
cache = SimpleCache(ttl=3600)


def cache_key(*args, **kwargs) -> str:
    """Generate cache key from function arguments."""
    key_data = json.dumps({"args": args, "kwargs": kwargs}, sort_keys=True)
    return hashlib.md5(key_data.encode()).hexdigest()


def cached(ttl: int = 3600):
    """Decorator for caching function results."""
    def decorator(func):
        func_cache = SimpleCache(ttl=ttl)
        
        @wraps(func)
        def wrapper(*args, **kwargs):
            key = f"{func.__name__}:{cache_key(*args, **kwargs)}"
            result = func_cache.get(key)
            if result is None:
                result = func(*args, **kwargs)
                func_cache.set(key, result)
            return result
        return wrapper
    return decorator

