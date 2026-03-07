import time
from typing import Dict

class RateLimiter:
    def __init__(self, requests_per_minute: int, burst_size: int):
        self.buckets = {}
        self.requests_per_minute = requests_per_minute
        self.burst_size = burst_size

    def get_stats(self, client_id: str = None) -> Dict:
        """Get rate limiter statistics."""
        if client_id:
            tokens, last_update = self.buckets.get(client_id, (self.burst_size, time.time()))
            return {"client_id": client_id, "tokens_available": tokens, "last_update": last_update}
        else:
            return {
                "total_clients": len(self.buckets),
                "requests_per_minute": self.requests_per_minute,
                "burst_size": self.burst_size,
            }

@pytest.fixture
def rate_limiter():
    return RateLimiter(requests_per_minute=60, burst_size=10)

def test_get_stats_happy_path(rate_limiter):
    client_id = "user123"
    stats = rate_limiter.get_stats(client_id)
    assert isinstance(stats, dict)
    assert stats["client_id"] == client_id
    assert stats["tokens_available"] == 10
    assert stats["last_update"]

def test_get_stats_no_client(rate_limiter):
    stats = rate_limiter.get_stats()
    assert isinstance(stats, dict)
    assert stats["total_clients"] == 0
    assert stats["requests_per_minute"] == 60
    assert stats["burst_size"] == 10

def test_get_stats_empty_bucket(rate_limiter):
    client_id = "user456"
    rate_limiter.buckets[client_id] = (0, time.time())
    stats = rate_limiter.get_stats(client_id)
    assert isinstance(stats, dict)
    assert stats["client_id"] == client_id
    assert stats["tokens_available"] == 0
    assert stats["last_update"]

def test_get_stats_negative_tokens(rate_limiter):
    client_id = "user789"
    rate_limiter.buckets[client_id] = (-5, time.time())
    stats = rate_limiter.get_stats(client_id)
    assert isinstance(stats, dict)
    assert stats["client_id"] == client_id
    assert stats["tokens_available"] == 0
    assert stats["last_update"]

def test_get_stats_large_time_difference(rate_limiter):
    client_id = "user1011"
    rate_limiter.buckets[client_id] = (5, time.time() - 61)
    stats = rate_limiter.get_stats(client_id)
    assert isinstance(stats, dict)
    assert stats["client_id"] == client_id
    assert stats["tokens_available"] == 10
    assert stats["last_update"]

def test_get_stats_invalid_client_id(rate_limiter):
    stats = rate_limiter.get_stats("invalid_client")
    assert stats is None

def test_get_stats_none_client_id(rate_limiter):
    stats = rate_limiter.get_stats(None)
    assert stats is None