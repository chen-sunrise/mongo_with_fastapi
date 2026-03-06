import asyncio
import json
import random
import time
from logging import getLogger
from typing import Any, Awaitable, Callable, TypeVar

try:
    from redis.asyncio import Redis
    from redis.exceptions import RedisError
    REDIS_PACKAGE_AVAILABLE = True
except ModuleNotFoundError:
    Redis = Any  # type: ignore[assignment,misc]
    REDIS_PACKAGE_AVAILABLE = False

    class RedisError(Exception):
        pass

from app.core.config import settings
from app.core.observability import REDIS_OPERATION_SECONDS
from app.infra.circuit_breaker import CircuitBreaker

logger = getLogger(__name__)
T = TypeVar("T")


class RedisCache:
    def __init__(self, client: Redis | None):
        self.client = client
        self.breaker = CircuitBreaker(
            failure_threshold=settings.CIRCUIT_BREAKER_FAILURE_THRESHOLD,
            recovery_seconds=settings.CIRCUIT_BREAKER_RECOVERY_SECONDS,
        )

    async def ping(self) -> bool:
        if self.client is None:
            return False
        if not await self.breaker.can_execute():
            return False

        started_at = time.perf_counter()
        try:
            result = await self.client.ping()
            await self.breaker.record_success()
            return bool(result)
        except RedisError:
            await self.breaker.record_failure()
            logger.exception("redis_ping_failed")
            return False
        finally:
            REDIS_OPERATION_SECONDS.labels(operation="ping").observe(time.perf_counter() - started_at)

    async def get_json(self, key: str) -> Any | None:
        if self.client is None:
            return None
        if not await self.breaker.can_execute():
            return None

        started_at = time.perf_counter()
        try:
            value = await self.client.get(key)
            await self.breaker.record_success()
            if value is None:
                return None
            return json.loads(value)
        except RedisError:
            await self.breaker.record_failure()
            logger.exception("redis_get_failed")
            return None
        finally:
            REDIS_OPERATION_SECONDS.labels(operation="get").observe(time.perf_counter() - started_at)

    async def set_json(self, key: str, value: Any, ttl_seconds: int) -> None:
        if self.client is None:
            return
        if not await self.breaker.can_execute():
            return

        started_at = time.perf_counter()
        jitter = random.randint(0, max(ttl_seconds // 10, 1))
        try:
            await self.client.set(name=key, value=json.dumps(value), ex=ttl_seconds + jitter)
            await self.breaker.record_success()
        except RedisError:
            await self.breaker.record_failure()
            logger.exception("redis_set_failed")
        finally:
            REDIS_OPERATION_SECONDS.labels(operation="set").observe(time.perf_counter() - started_at)

    async def delete(self, key: str) -> None:
        if self.client is None:
            return

        started_at = time.perf_counter()
        try:
            await self.client.delete(key)
        except RedisError:
            logger.exception("redis_delete_failed")
        finally:
            REDIS_OPERATION_SECONDS.labels(operation="delete").observe(time.perf_counter() - started_at)

    async def delete_pattern(self, pattern: str) -> None:
        if self.client is None:
            return

        started_at = time.perf_counter()
        try:
            keys = [key async for key in self.client.scan_iter(match=pattern)]
            if keys:
                await self.client.delete(*keys)
        except RedisError:
            logger.exception("redis_delete_pattern_failed")
        finally:
            REDIS_OPERATION_SECONDS.labels(operation="delete_pattern").observe(time.perf_counter() - started_at)

    async def get_or_set_singleflight(
        self,
        *,
        key: str,
        ttl_seconds: int,
        fetcher: Callable[[], Awaitable[T]],
    ) -> tuple[T, bool]:
        cached_value = await self.get_json(key)
        if cached_value is not None:
            return cached_value, True

        if self.client is None:
            fresh = await fetcher()
            return fresh, False

        lock_key = f"lock:{key}"
        lock_acquired = False

        try:
            lock_acquired = await self._acquire_lock(lock_key)
            if lock_acquired:
                fresh = await fetcher()
                await self.set_json(key, fresh, ttl_seconds)
                return fresh, False

            for _ in range(settings.CACHE_LOCK_RETRY_COUNT):
                await asyncio.sleep(settings.CACHE_LOCK_RETRY_DELAY_MS / 1000)
                cached_retry = await self.get_json(key)
                if cached_retry is not None:
                    return cached_retry, True

            fallback = await fetcher()
            return fallback, False
        finally:
            if lock_acquired:
                await self.delete(lock_key)

    async def _acquire_lock(self, key: str) -> bool:
        if self.client is None:
            return False
        if not await self.breaker.can_execute():
            return False

        started_at = time.perf_counter()
        try:
            result = await self.client.set(name=key, value="1", ex=settings.CACHE_LOCK_SECONDS, nx=True)
            await self.breaker.record_success()
            return bool(result)
        except RedisError:
            await self.breaker.record_failure()
            logger.exception("redis_lock_failed")
            return False
        finally:
            REDIS_OPERATION_SECONDS.labels(operation="lock").observe(time.perf_counter() - started_at)


async def create_redis_client() -> Redis | None:
    if not REDIS_PACKAGE_AVAILABLE:
        logger.warning("redis_package_not_installed")
        return None
    if settings.REDIS_URL is None:
        return None
    client = Redis.from_url(
        settings.REDIS_URL,
        socket_timeout=settings.REDIS_SOCKET_TIMEOUT_SECONDS,
        socket_connect_timeout=settings.REDIS_SOCKET_TIMEOUT_SECONDS,
        decode_responses=True,
    )
    try:
        await client.ping()
    except RedisError:
        logger.exception("redis_initial_ping_failed")
    return client
