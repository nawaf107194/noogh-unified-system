import pytest
from gateway.app.api.security_middleware import SecurityMiddleware
from collections import defaultdict
import threading

def test_init_happy_path():
    app = Mock()
    max_requests_per_minute = 100
    middleware = SecurityMiddleware(app, max_requests_per_minute)
    assert middleware.max_requests == max_requests_per_minute
    assert isinstance(middleware.history, defaultdict)
    assert isinstance(middleware.lock, threading.Lock)

def test_init_default_max_requests():
    app = Mock()
    middleware = SecurityMiddleware(app)
    assert middleware.max_requests == 200

def test_init_non_integer_max_requests():
    app = Mock()
    max_requests_per_minute = "200"
    with pytest.raises(TypeError):
        SecurityMiddleware(app, max_requests_per_minute)

def test_init_negative_max_requests():
    app = Mock()
    max_requests_per_minute = -1
    with pytest.raises(ValueError):
        SecurityMiddleware(app, max_requests_per_minute)