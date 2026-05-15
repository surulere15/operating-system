"""
Redis-Based Distributed Rate Limiter
Production-grade rate limiting that works across multiple servers

Features:
- Distributed (works across multiple servers)
- Persistent (survives process restarts)
- Atomic operations (thread-safe)
- Sliding window algorithm
- Automatic cleanup
- Per-endpoint and per-user rate limiting

Upgrade from in-memory rate limiter:
- ✅ Multi-server support
- ✅ Persistent across restarts
- ✅ Atomic operations
- ✅ Lower memory usage
- ✅ Automatic expiration
"""

import time
import logging
from typing import Optional, Dict
from dataclasses import dataclass
from enum import Enum

try:
    import redis.asyncio as redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    redis = None

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ============================================================================
# CONFIGURATION
# ============================================================================

@dataclass
class RateLimitConfig:
    """Rate limit configuration"""
    per_second: int = 10
    per_minute: int = 100
    per_hour: int = 1000
    per_day: int = 10000


class RateLimitWindow(Enum):
    """Rate limit time windows"""
    SECOND = (1, "second")
    MINUTE = (60, "minute")
    HOUR = (3600, "hour")
    DAY = (86400, "day")

    def __init__(self, seconds: int, name: str):
        self.seconds = seconds
        self.display_name = name


# ============================================================================
# REDIS RATE LIMITER
# ============================================================================

class RedisRateLimiter:
    """
    Distributed rate limiter using Redis sorted sets

    Uses sliding window algorithm:
    - Stores timestamps in Redis sorted set
    - Removes old entries atomically
    - Counts entries in window
    - Works across multiple servers
    """

    def __init__(
        self,
        redis_client: redis.Redis,
        config: RateLimitConfig = None,
        key_prefix: str = "ratelimit"
    ):
        """
        Initialize Redis rate limiter

        Args:
            redis_client: Async Redis client
            config: Rate limit configuration
            key_prefix: Redis key prefix
        """
        if not REDIS_AVAILABLE:
            raise ImportError("redis package required: pip install redis[asyncio]")

        self.redis = redis_client
        self.config = config or RateLimitConfig()
        self.key_prefix = key_prefix

        logger.info("✅ Redis Rate Limiter initialized")
        logger.info(f"   Limits: {self.config.per_second}/s, {self.config.per_minute}/m, "
                   f"{self.config.per_hour}/h, {self.config.per_day}/d")

    async def acquire(
        self,
        identifier: str,
        window: RateLimitWindow = RateLimitWindow.SECOND,
        custom_limit: Optional[int] = None
    ) -> bool:
        """
        Attempt to acquire rate limit token

        Args:
            identifier: Rate limit identifier (endpoint, user_id, etc.)
            window: Time window to check
            custom_limit: Override default limit for this window

        Returns:
            True if allowed, False if rate limited
        """
        # Get limit for this window
        limit = custom_limit or self._get_limit_for_window(window)

        # Redis key
        key = f"{self.key_prefix}:{identifier}:{window.display_name}"

        # Current time
        now = time.time()
        window_start = now - window.seconds

        # Use Redis pipeline for atomic operations
        pipe = self.redis.pipeline()

        # 1. Remove old entries (outside window)
        pipe.zremrangebyscore(key, 0, window_start)

        # 2. Add current timestamp
        pipe.zadd(key, {str(now): now})

        # 3. Count entries in window
        pipe.zcount(key, window_start, now)

        # 4. Set expiration (cleanup)
        pipe.expire(key, window.seconds * 2)

        # Execute pipeline
        results = await pipe.execute()
        count = results[2]  # Count result

        # Check if within limit
        allowed = count <= limit

        if not allowed:
            logger.warning(f"⚠️ Rate limit exceeded: {identifier} ({count}/{limit} {window.display_name})")

        return allowed

    async def acquire_multi(
        self,
        identifier: str,
        windows: list[RateLimitWindow] = None
    ) -> Dict[str, bool]:
        """
        Check rate limits for multiple windows at once

        Args:
            identifier: Rate limit identifier
            windows: Time windows to check (default: all)

        Returns:
            Dictionary of window -> allowed status
        """
        if windows is None:
            windows = [
                RateLimitWindow.SECOND,
                RateLimitWindow.MINUTE,
                RateLimitWindow.HOUR,
                RateLimitWindow.DAY
            ]

        results = {}
        for window in windows:
            results[window.display_name] = await self.acquire(identifier, window)

        # Only allowed if all windows allow
        all_allowed = all(results.values())

        return {
            "allowed": all_allowed,
            "windows": results
        }

    async def get_remaining(
        self,
        identifier: str,
        window: RateLimitWindow = RateLimitWindow.SECOND
    ) -> int:
        """
        Get remaining requests in window

        Args:
            identifier: Rate limit identifier
            window: Time window

        Returns:
            Number of remaining requests
        """
        key = f"{self.key_prefix}:{identifier}:{window.display_name}"
        now = time.time()
        window_start = now - window.seconds

        # Count current requests in window
        count = await self.redis.zcount(key, window_start, now)

        # Get limit
        limit = self._get_limit_for_window(window)

        return max(0, limit - count)

    async def reset(self, identifier: str, window: Optional[RateLimitWindow] = None):
        """
        Reset rate limit for identifier

        Args:
            identifier: Rate limit identifier
            window: Specific window to reset (None = all windows)
        """
        if window:
            key = f"{self.key_prefix}:{identifier}:{window.display_name}"
            await self.redis.delete(key)
        else:
            # Reset all windows
            pattern = f"{self.key_prefix}:{identifier}:*"
            keys = await self.redis.keys(pattern)
            if keys:
                await self.redis.delete(*keys)

        logger.info(f"✅ Rate limit reset: {identifier}")

    async def get_status(self, identifier: str) -> Dict:
        """
        Get rate limit status for identifier

        Args:
            identifier: Rate limit identifier

        Returns:
            Status dictionary with counts and remaining for all windows
        """
        now = time.time()
        status = {}

        for window in RateLimitWindow:
            key = f"{self.key_prefix}:{identifier}:{window.display_name}"
            window_start = now - window.seconds

            # Get count
            count = await self.redis.zcount(key, window_start, now)

            # Get limit
            limit = self._get_limit_for_window(window)

            status[window.display_name] = {
                "count": count,
                "limit": limit,
                "remaining": max(0, limit - count),
                "reset_in_seconds": window.seconds
            }

        return status

    async def wait_if_needed(
        self,
        identifier: str,
        window: RateLimitWindow = RateLimitWindow.SECOND,
        max_wait: float = 60.0
    ) -> float:
        """
        Wait until rate limit allows request

        Args:
            identifier: Rate limit identifier
            window: Time window to check
            max_wait: Maximum wait time in seconds

        Returns:
            Time waited in seconds
        """
        import asyncio

        start_time = time.time()

        while True:
            # Try to acquire
            if await self.acquire(identifier, window):
                wait_time = time.time() - start_time
                if wait_time > 0.1:
                    logger.info(f"⏱️ Waited {wait_time:.2f}s for rate limit")
                return wait_time

            # Check if exceeded max wait
            elapsed = time.time() - start_time
            if elapsed >= max_wait:
                raise TimeoutError(f"Rate limit wait exceeded {max_wait}s")

            # Sleep before retry (adaptive backoff)
            sleep_time = min(0.5, window.seconds / 10)
            await asyncio.sleep(sleep_time)

    def _get_limit_for_window(self, window: RateLimitWindow) -> int:
        """Get configured limit for time window"""
        limits = {
            RateLimitWindow.SECOND: self.config.per_second,
            RateLimitWindow.MINUTE: self.config.per_minute,
            RateLimitWindow.HOUR: self.config.per_hour,
            RateLimitWindow.DAY: self.config.per_day,
        }
        return limits[window]


# ============================================================================
# USER-SPECIFIC RATE LIMITER
# ============================================================================

class UserRateLimiter:
    """
    Per-user rate limiting with tier-based quotas

    Supports different rate limits based on user subscription tier:
    - Free: 10 req/s
    - Basic: 50 req/s
    - Pro: 200 req/s
    - Enterprise: 1000 req/s
    """

    TIER_LIMITS = {
        "free": RateLimitConfig(per_second=10, per_minute=100, per_hour=1000, per_day=10000),
        "basic": RateLimitConfig(per_second=50, per_minute=500, per_hour=5000, per_day=50000),
        "pro": RateLimitConfig(per_second=200, per_minute=2000, per_hour=20000, per_day=200000),
        "enterprise": RateLimitConfig(per_second=1000, per_minute=10000, per_hour=100000, per_day=1000000),
    }

    def __init__(self, redis_client: redis.Redis):
        """
        Initialize user rate limiter

        Args:
            redis_client: Async Redis client
        """
        self.redis = redis_client
        self.limiters: Dict[str, RedisRateLimiter] = {}

        # Create rate limiter for each tier
        for tier, config in self.TIER_LIMITS.items():
            self.limiters[tier] = RedisRateLimiter(
                redis_client,
                config=config,
                key_prefix=f"user_ratelimit:{tier}"
            )

        logger.info("✅ User Rate Limiter initialized")
        logger.info(f"   Tiers: {list(self.TIER_LIMITS.keys())}")

    async def acquire(
        self,
        user_id: int,
        user_tier: str = "free",
        endpoint: Optional[str] = None
    ) -> bool:
        """
        Check if user can make request

        Args:
            user_id: User ID
            user_tier: User subscription tier
            endpoint: Optional endpoint identifier

        Returns:
            True if allowed, False if rate limited
        """
        # Get rate limiter for user tier
        limiter = self.limiters.get(user_tier.lower(), self.limiters["free"])

        # Create identifier
        identifier = f"user:{user_id}"
        if endpoint:
            identifier = f"{identifier}:{endpoint}"

        # Check all windows
        result = await limiter.acquire_multi(identifier)

        return result["allowed"]

    async def get_status(self, user_id: int, user_tier: str = "free") -> Dict:
        """Get rate limit status for user"""
        limiter = self.limiters.get(user_tier.lower(), self.limiters["free"])
        identifier = f"user:{user_id}"

        return await limiter.get_status(identifier)


# ============================================================================
# FALLBACK: IN-MEMORY RATE LIMITER (No Redis)
# ============================================================================

class InMemoryRateLimiter:
    """
    Fallback rate limiter for when Redis is unavailable
    WARNING: Only works on single server, not distributed
    """

    def __init__(self, config: RateLimitConfig = None):
        from collections import deque, defaultdict

        self.config = config or RateLimitConfig()
        self.timestamps: Dict[str, deque] = defaultdict(lambda: deque(maxlen=10000))

        logger.warning("⚠️ Using in-memory rate limiter (not distributed)")
        logger.warning("   For production, use Redis-based rate limiter")

    async def acquire(
        self,
        identifier: str,
        window: RateLimitWindow = RateLimitWindow.SECOND,
        custom_limit: Optional[int] = None
    ) -> bool:
        """Check rate limit (in-memory)"""
        import asyncio

        key = f"{identifier}:{window.display_name}"
        now = time.time()
        window_start = now - window.seconds

        # Remove old timestamps
        while self.timestamps[key] and self.timestamps[key][0] < window_start:
            self.timestamps[key].popleft()

        # Check limit
        limit = custom_limit or self._get_limit_for_window(window)
        count = len(self.timestamps[key])

        if count < limit:
            self.timestamps[key].append(now)
            return True

        return False

    def _get_limit_for_window(self, window: RateLimitWindow) -> int:
        limits = {
            RateLimitWindow.SECOND: self.config.per_second,
            RateLimitWindow.MINUTE: self.config.per_minute,
            RateLimitWindow.HOUR: self.config.per_hour,
            RateLimitWindow.DAY: self.config.per_day,
        }
        return limits[window]


# ============================================================================
# EXAMPLE USAGE
# ============================================================================

async def example_usage():
    print("\n" + "="*80)
    print("REDIS RATE LIMITER - DEMO")
    print("="*80)

    # Initialize Redis client
    redis_client = redis.Redis(
        host='localhost',
        port=6379,
        db=0,
        decode_responses=False
    )

    try:
        # Test connection
        await redis_client.ping()
        print("✅ Redis connection successful")

        # Create rate limiter
        config = RateLimitConfig(
            per_second=5,
            per_minute=20,
            per_hour=100,
            per_day=1000
        )

        limiter = RedisRateLimiter(redis_client, config)

        # Test rate limiting
        print("\n📊 Testing rate limits...")

        identifier = "api:test_endpoint"

        # Make requests
        for i in range(10):
            allowed = await limiter.acquire(identifier, RateLimitWindow.SECOND)
            status = "✅ Allowed" if allowed else "❌ Rate limited"
            print(f"   Request {i+1}: {status}")

            if i == 4:  # After 5 requests (limit), next should be blocked
                print(f"\n   📊 Status after {i+1} requests:")
                status = await limiter.get_status(identifier)
                for window, data in status.items():
                    print(f"      {window}: {data['count']}/{data['limit']} (remaining: {data['remaining']})")

        # Wait for reset
        print("\n⏱️ Waiting for rate limit reset...")
        await limiter.wait_if_needed(identifier, RateLimitWindow.SECOND)
        print("   ✅ Rate limit reset")

        # Test user rate limiter
        print("\n📊 Testing user rate limiter...")
        user_limiter = UserRateLimiter(redis_client)

        user_id = 123
        for tier in ["free", "basic", "pro", "enterprise"]:
            allowed = await user_limiter.acquire(user_id, tier)
            print(f"   User {user_id} ({tier}): {'✅ Allowed' if allowed else '❌ Rate limited'}")

        print("\n" + "="*80)
        print("✅ REDIS RATE LIMITER DEMO COMPLETE")
        print("="*80)

    except redis.ConnectionError:
        print("❌ Redis not available - using fallback in-memory rate limiter")

        fallback = InMemoryRateLimiter(config)
        for i in range(10):
            allowed = await fallback.acquire(identifier, RateLimitWindow.SECOND)
            print(f"   Request {i+1}: {'✅ Allowed' if allowed else '❌ Rate limited'}")

    finally:
        await redis_client.close()


if __name__ == "__main__":
    import asyncio

    if not REDIS_AVAILABLE:
        print("❌ Redis package not installed")
        print("   Install: pip install redis[asyncio]")
    else:
        asyncio.run(example_usage())
