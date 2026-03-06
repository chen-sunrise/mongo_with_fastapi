import asyncio
import time
from collections import defaultdict
from logging import getLogger

from fastapi import HTTPException, status
try:
    from redis.exceptions import RedisError
except ModuleNotFoundError:
    class RedisError(Exception):
        pass

from app.infra.redis_cache import RedisCache

logger = getLogger(__name__)


class _InMemoryLimiter:
    def __init__(self):
        self._store: dict[str, tuple[int, float]] = defaultdict(lambda: (0, 0.0))
        self._lock = asyncio.Lock()

    async def increment(self, key: str, window_seconds: int) -> int:
        now = time.monotonic()
        async with self._lock:
            counter, expires_at = self._store[key]
            if now >= expires_at:
                counter = 0
                expires_at = now + window_seconds
            counter += 1
            self._store[key] = (counter, expires_at)
            return counter


class RateLimiter:
    def __init__(self, cache: RedisCache):
        self.cache = cache
        self.fallback_limiter = _InMemoryLimiter()

    async def enforce(self, *, key: str, limit: int, window_seconds: int, message: str) -> None:
        redis_key = f"rate_limit:{key}"

        if self.cache.client is not None:
            try:
                count = await self.cache.client.incr(redis_key)
                if count == 1:
                    await self.cache.client.expire(redis_key, window_seconds)
                if count > limit:
                    raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail=message)
                return
            except RedisError:
                logger.exception("redis_rate_limit_failed")

        fallback_count = await self.fallback_limiter.increment(redis_key, window_seconds)
        if fallback_count > limit:
            raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail=message)
