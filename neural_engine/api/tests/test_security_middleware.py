import pytest
from collections import defaultdict
import threading

from neural_engine.api.security_middleware import SecurityMiddleware

def test_happy_path():
    app = "dummy_app"
    max_requests_per_minute = 200
    middleware = SecurityMiddleware(app, max_requests_per_minute)
    assert isinstance(middleware, SecurityMiddleware)
    assert middleware.max_requests == max_requests_per_minute
    assert middleware.requests == defaultdict(list)
    assert isinstance(middleware.lock, threading.Lock)

def test_edge_cases():
    app = "dummy_app"
    max_requests_per_minute = 0
    middleware = SecurityMiddleware(app, max_requests_per_minute)
    assert isinstance(middleware, SecurityMiddleware)
    assert middleware.max_requests == 0
    assert middleware.requests == defaultdict(list)
    assert isinstance(middleware.lock, threading.Lock)

def test_error_cases():
    app = "dummy_app"
    with pytest.raises(ValueError):
        SecurityMiddleware(app, -1)

def test_async_behavior():
    # Since the __init__ method does not involve any async behavior,
    # we don't need to create tests for it.
    pass