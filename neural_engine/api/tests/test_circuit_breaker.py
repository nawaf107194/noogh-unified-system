import pytest
import asyncio

from neural_engine.api.circuit_breaker import CircuitBreaker

# Happy path
def test_happy_path():
    breaker = CircuitBreaker(max_concurrent=5, timeout_seconds=60)
    assert breaker.semaphore._value == 5
    assert breaker.timeout == 60

# Edge cases
def test_edge_case_default_values():
    breaker = CircuitBreaker()
    assert breaker.semaphore._value == 1
    assert breaker.timeout == 30

def test_edge_case_max_concurrent_zero():
    breaker = CircuitBreaker(max_concurrent=0)
    assert breaker.semaphore._value == 0
    assert breaker.timeout == 30

def test_edge_case_timeout_zero():
    breaker = CircuitBreaker(timeout_seconds=0)
    assert breaker.semaphore._value == 1
    assert breaker.timeout == 0

# Error cases
def test_error_case_max_concurrent_negative():
    with pytest.raises(ValueError) as excinfo:
        CircuitBreaker(max_concurrent=-1)
    assert "max_concurrent must be non-negative" in str(excinfo.value)

def test_error_case_timeout_negative():
    with pytest.raises(ValueError) as excinfo:
        CircuitBreaker(timeout_seconds=-1)
    assert "timeout_seconds must be non-negative" in str(excinfo.value)

# Async behavior
@pytest.mark.asyncio
async def test_async_behavior():
    async def test_coroutine():
        async with breaker.semaphore:
            await asyncio.sleep(0.1)

    breaker = CircuitBreaker(max_concurrent=1, timeout_seconds=1)
    tasks = [test_coroutine() for _ in range(2)]
    done, pending = await asyncio.wait(tasks, return_when=asyncio.ALL_COMPLETED)
    assert len(done) == 2
    assert len(pending) == 0