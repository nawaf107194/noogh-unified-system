import pytest

from gateway.app.api.security_middleware import SecurityMiddleware

class MockApp:
    pass

def test_init_happy_path():
    app = MockApp()
    middleware = SecurityMiddleware(app, max_bytes=10 * 1024 * 1024)
    assert isinstance(middleware, SecurityMiddleware)
    assert middleware.app == app
    assert middleware.max_bytes == 10 * 1024 * 1024

def test_init_with_default_max_bytes():
    app = MockApp()
    middleware = SecurityMiddleware(app)
    assert isinstance(middleware, SecurityMiddleware)
    assert middleware.app == app
    assert middleware.max_bytes == 10 * 1024 * 1024

def test_init_with_none_max_bytes():
    app = MockApp()
    with pytest.raises(ValueError):
        SecurityMiddleware(app, max_bytes=None)

def test_init_with_empty_max_bytes():
    app = MockApp()
    with pytest.raises(ValueError):
        SecurityMiddleware(app, max_bytes="")

def test_init_with_negative_max_bytes():
    app = MockApp()
    with pytest.raises(ValueError):
        SecurityMiddleware(app, max_bytes=-10)