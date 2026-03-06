import asyncio
import time


class CircuitBreaker:
    def __init__(self, *, failure_threshold: int, recovery_seconds: int):
        self.failure_threshold = failure_threshold
        self.recovery_seconds = recovery_seconds
        self.failure_count = 0
        self.opened_at: float | None = None
        self._lock = asyncio.Lock()

    async def can_execute(self) -> bool:
        async with self._lock:
            if self.opened_at is None:
                return True
            elapsed = time.monotonic() - self.opened_at
            if elapsed >= self.recovery_seconds:
                self.opened_at = None
                self.failure_count = 0
                return True
            return False

    async def record_success(self) -> None:
        async with self._lock:
            self.failure_count = 0
            self.opened_at = None

    async def record_failure(self) -> None:
        async with self._lock:
            self.failure_count += 1
            if self.failure_count >= self.failure_threshold:
                self.opened_at = time.monotonic()
