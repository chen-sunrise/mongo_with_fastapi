import asyncio

import pytest

from app.infra.circuit_breaker import CircuitBreaker


@pytest.mark.asyncio
async def test_circuit_breaker_opens_after_threshold():
    breaker = CircuitBreaker(failure_threshold=2, recovery_seconds=1)

    assert await breaker.can_execute() is True

    await breaker.record_failure()
    assert await breaker.can_execute() is True

    await breaker.record_failure()
    assert await breaker.can_execute() is False


@pytest.mark.asyncio
async def test_circuit_breaker_recovers_after_timeout():
    breaker = CircuitBreaker(failure_threshold=1, recovery_seconds=1)

    await breaker.record_failure()
    assert await breaker.can_execute() is False

    await asyncio.sleep(1.05)

    assert await breaker.can_execute() is True
