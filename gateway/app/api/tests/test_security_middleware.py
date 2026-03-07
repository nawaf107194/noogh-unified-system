import pytest
from unittest.mock import MagicMock
from gateway.app.api.security_middleware import SecurityMiddleware
import threading

class TestSecurityMiddleware:

    @pytest.fixture
    def middleware(self):
        return SecurityMiddleware(MagicMock())

    def test_happy_path(self, middleware):
        # Normal initialization with default parameters
        assert middleware.max_requests == 200
        assert isinstance(middleware.history, dict)
        assert isinstance(middleware.lock, threading.Lock)

    def test_edge_cases(self):
        # Empty input for app
        with pytest.raises(TypeError):
            SecurityMiddleware(None)
        
        # Boundary case for max_requests_per_minute
        min_value = 1
        max_value = 1000
        mid_value = (min_value + max_value) // 2
        
        middleware_min = SecurityMiddleware(MagicMock(), min_value)
        middleware_max = SecurityMiddleware(MagicMock(), max_value)
        middleware_mid = SecurityMiddleware(MagicMock(), mid_value)
        
        assert middleware_min.max_requests == min_value
        assert middleware_max.max_requests == max_value
        assert middleware_mid.max_requests == mid_value

    def test_error_cases(self):
        # Invalid input types
        with pytest.raises(TypeError):
            SecurityMiddleware("not an app")
        
        with pytest.raises(TypeError):
            SecurityMiddleware(MagicMock(), "not an int")

        # Negative value for max_requests_per_minute
        with pytest.raises(ValueError):
            SecurityMiddleware(MagicMock(), -1)

    def test_async_behavior(self):
        # Since the provided code does not explicitly involve async operations,
        # we can only test the thread safety aspect.
        # This is more of a smoke test to ensure no immediate issues arise.
        from concurrent.futures import ThreadPoolExecutor

        def init_and_check():
            mw = SecurityMiddleware(MagicMock())
            assert mw.max_requests == 200
            assert isinstance(mw.history, dict)
            assert isinstance(mw.lock, threading.Lock)

        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(init_and_check) for _ in range(10)]
            for future in futures:
                future.result()  # This will raise any exceptions if they occur