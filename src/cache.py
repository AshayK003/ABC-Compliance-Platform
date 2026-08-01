"""Simple in-memory cache with TTL support."""

from __future__ import annotations

import time
from typing import Any, Optional

from src.config import settings


class Cache:
    """Simple in-memory cache with TTL."""

    def __init__(self) -> None:
        self._store: dict[str, tuple[Any, float]] = {}

    def get(self, key: str) -> Optional[Any]:
        if not settings.cache_enabled:
            return None
        entry = self._store.get(key)
        if entry is None:
            return None
        value, expires_at = entry
        if time.time() > expires_at:
            del self._store[key]
            return None
        return value

    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        if not settings.cache_enabled:
            return
        ttl = ttl or settings.cache_ttl_seconds
        expires_at = time.time() + ttl
        self._store[key] = (value, expires_at)

    def delete(self, key: str) -> None:
        self._store.pop(key, None)

    def clear(self) -> None:
        self._store.clear()


# Global cache instance
cache = Cache()


def cache_key(*parts: str) -> str:
    """Generate a cache key from parts."""
    return ":".join(parts)


def cached(ttl: Optional[int] = None):
    """Decorator for caching function results."""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            # Generate cache key from function name and args
            key_parts = [func.__name__] + [str(arg) for arg in args] + [f"{k}={v}" for k, v in sorted(kwargs.items())]
            key = cache_key(*key_parts)

            cached_value = cache.get(key)
            if cached_value is not None:
                return cached_value

            result = await func(*args, **kwargs)
            cache.set(key, result, ttl)
            return result
        return wrapper
    return decorator


def invalidate_cache(*key_parts: str) -> None:
    """Invalidate a cache key."""
    key = cache_key(*key_parts)
    cache.delete(key)


def invalidate_pattern(pattern: str) -> None:
    """Invalidate all keys matching a pattern (simple prefix match)."""
    keys_to_delete = [k for k in cache._store.keys() if k.startswith(pattern)]
    for key in keys_to_delete:
        cache.delete(key)