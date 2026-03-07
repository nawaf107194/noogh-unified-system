import pytest

from noogh_unified_system.src.shared.middleware import Middleware


def test_middleware_normal_inputs():
    app = object()
    middleware = Middleware(app, max_bytes=1024 * 512)
    assert middleware.app is app
    assert middleware.max_bytes == 1024 * 512


def test_middleware_default_max_bytes():
    app = object()
    middleware = Middleware(app)
    assert middleware.app is app
    assert middleware.max_bytes == 1024 * 1024


def test_middleware_none_app():
    with pytest.raises(ValueError) as e:
        Middleware(None, max_bytes=1024 * 512)
    assert str(e.value) == "app cannot be None"


def test_middleware_negative_max_bytes():
    with pytest.raises(ValueError) as e:
        Middleware(object(), max_bytes=-1)
    assert str(e.value) == "max_bytes must be a non-negative integer"