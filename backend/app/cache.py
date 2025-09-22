"""
Caching layer for fare rules to handle millions of users.
Uses Redis for distributed caching with fallback to in-memory cache.
"""

import json
import time
from typing import Dict, Tuple, Optional, Any
from functools import lru_cache
import hashlib

# Note: Add to requirements.txt if using Redis:
# redis==5.0.1

try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    print("Redis not installed. Using in-memory cache only.")


class FareRulesCache:
    """
    Multi-level caching strategy for fare rules:
    1. In-memory LRU cache (process level)
    2. Redis cache (shared across processes)
    3. Database (source of truth)
    """
    
    def __init__(self, redis_url: Optional[str] = None, ttl: int = 3600):
        """
        Initialize cache with optional Redis connection.
        
        Args:
            redis_url: Redis connection URL (e.g., redis://localhost:6379)
            ttl: Time to live in seconds (default 1 hour)
        """
        self.ttl = ttl
        self.redis_client = None
        
        # In-memory cache for this process
        self._memory_cache: Dict[str, Any] = {}
        self._cache_timestamps: Dict[str, float] = {}
        
        # Initialize Redis if available
        if REDIS_AVAILABLE and redis_url:
            try:
                self.redis_client = redis.from_url(redis_url)
                self.redis_client.ping()
                print("Redis cache initialized successfully")
            except Exception as e:
                print(f"Redis connection failed: {e}. Using in-memory cache only.")
                self.redis_client = None
    
    def _make_key(self, from_zone: int, to_zone: int) -> str:
        """Generate cache key for zone pair."""
        # Normalize zones (always use lower zone first)
        z1, z2 = sorted([from_zone, to_zone])
        return f"fare:{z1}:{z2}"
    
    def _is_memory_cache_valid(self, key: str) -> bool:
        """Check if in-memory cache entry is still valid."""
        if key not in self._cache_timestamps:
            return False
        return (time.time() - self._cache_timestamps[key]) < self.ttl
    
    @lru_cache(maxsize=1000)
    def get_fare_cached(self, from_zone: int, to_zone: int) -> Optional[float]:
        """
        Get fare with multi-level caching.
        
        Cache lookup order:
        1. In-memory LRU cache
        2. Redis cache
        3. Database (if cache miss)
        """
        key = self._make_key(from_zone, to_zone)
        
        # Level 1: Check in-memory cache
        if key in self._memory_cache and self._is_memory_cache_valid(key):
            return self._memory_cache[key]
        
        # Level 2: Check Redis cache
        if self.redis_client:
            try:
                cached_value = self.redis_client.get(key)
                if cached_value:
                    fare = float(cached_value)
                    # Update in-memory cache
                    self._memory_cache[key] = fare
                    self._cache_timestamps[key] = time.time()
                    return fare
            except Exception as e:
                print(f"Redis get error: {e}")
        
        # Cache miss - will need to fetch from database
        return None
    
    def set_fare_cache(self, from_zone: int, to_zone: int, fare: float):
        """Store fare in all cache levels."""
        key = self._make_key(from_zone, to_zone)
        
        # Update in-memory cache
        self._memory_cache[key] = fare
        self._cache_timestamps[key] = time.time()
        
        # Update Redis cache
        if self.redis_client:
            try:
                self.redis_client.setex(key, self.ttl, str(fare))
            except Exception as e:
                print(f"Redis set error: {e}")
    
    def invalidate_cache(self, from_zone: Optional[int] = None, to_zone: Optional[int] = None):
        """
        Invalidate cache entries.
        If zones specified, invalidate specific entry.
        Otherwise, invalidate all entries.
        """
        if from_zone and to_zone:
            # Invalidate specific entry
            key = self._make_key(from_zone, to_zone)
            
            # Clear from memory
            self._memory_cache.pop(key, None)
            self._cache_timestamps.pop(key, None)
            self.get_fare_cached.cache_clear()
            
            # Clear from Redis
            if self.redis_client:
                try:
                    self.redis_client.delete(key)
                except Exception as e:
                    print(f"Redis delete error: {e}")
        else:
            # Clear all caches
            self._memory_cache.clear()
            self._cache_timestamps.clear()
            self.get_fare_cached.cache_clear()
            
            if self.redis_client:
                try:
                    # Clear all fare keys
                    for key in self.redis_client.scan_iter("fare:*"):
                        self.redis_client.delete(key)
                except Exception as e:
                    print(f"Redis clear error: {e}")
    
    def bulk_load_fares(self, fare_rules: Dict[Tuple[int, int], float]):
        """
        Bulk load fare rules into cache.
        Useful for warming up cache on startup.
        """
        pipeline = self.redis_client.pipeline() if self.redis_client else None
        
        for (from_zone, to_zone), fare in fare_rules.items():
            key = self._make_key(from_zone, to_zone)
            
            # Update memory cache
            self._memory_cache[key] = fare
            self._cache_timestamps[key] = time.time()
            
            # Add to Redis pipeline
            if pipeline:
                pipeline.setex(key, self.ttl, str(fare))
        
        # Execute Redis pipeline
        if pipeline:
            try:
                pipeline.execute()
                print(f"Bulk loaded {len(fare_rules)} fare rules into cache")
            except Exception as e:
                print(f"Redis bulk load error: {e}")


class ZonesCache:
    """Cache for available zones list."""
    
    def __init__(self, ttl: int = 3600):
        self.ttl = ttl
        self._zones: Optional[list] = None
        self._zones_timestamp: float = 0
        self._rules_hash: Optional[str] = None
    
    def is_valid(self) -> bool:
        """Check if zones cache is still valid."""
        if self._zones is None:
            return False
        return (time.time() - self._zones_timestamp) < self.ttl
    
    def get_zones(self) -> Optional[list]:
        """Get cached zones if valid."""
        if self.is_valid():
            return self._zones
        return None
    
    def set_zones(self, zones: list, rules_dict: dict):
        """Update zones cache with hash for validation."""
        self._zones = zones
        self._zones_timestamp = time.time()
        # Create hash of rules to detect changes
        rules_str = json.dumps(sorted(rules_dict.items()))
        self._rules_hash = hashlib.md5(rules_str.encode()).hexdigest()
    
    def invalidate(self):
        """Invalidate zones cache."""
        self._zones = None
        self._zones_timestamp = 0
        self._rules_hash = None


# Global cache instances (singleton pattern)
_fare_cache: Optional[FareRulesCache] = None
_zones_cache: Optional[ZonesCache] = None


def get_fare_cache() -> FareRulesCache:
    """Get singleton fare cache instance."""
    global _fare_cache
    if _fare_cache is None:
        redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
        _fare_cache = FareRulesCache(redis_url=redis_url)
        
        # Warm up cache on first access
        try:
            from app.database import get_db_manager
            db_manager = get_db_manager()
            fare_rules = db_manager.get_all_fare_rules()
            _fare_cache.bulk_load_fares(fare_rules)
        except Exception as e:
            print(f"Cache warmup failed: {e}")
    
    return _fare_cache


def get_zones_cache() -> ZonesCache:
    """Get singleton zones cache instance."""
    global _zones_cache
    if _zones_cache is None:
        _zones_cache = ZonesCache()
    return _zones_cache


import os
# Example of how to integrate with existing fare calculator
def get_fare_with_cache(from_zone: int, to_zone: int) -> float:
    """
    Get fare using cache-first strategy.
    
    This would replace direct database calls in the fare calculator.
    """
    cache = get_fare_cache()
    
    # Try cache first
    fare = cache.get_fare_cached(from_zone, to_zone)
    if fare is not None:
        return fare
    
    # Cache miss - fetch from database
    from app.database import get_db_manager
    db_manager = get_db_manager()
    fare = db_manager.get_fare(from_zone, to_zone)
    
    if fare is not None:
        # Store in cache for next time
        cache.set_fare_cache(from_zone, to_zone, fare)
    
    return fare or 0.0
