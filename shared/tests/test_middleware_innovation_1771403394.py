import pytest

class MockApp:
    def __call__(self, environ, start_response):
        pass

@pytest.fixture
def mock_app():
    return MockApp()

class TestMiddlewareInit:

    def test_happy_path(self, mock_app):
        middleware = Middleware(mock_app, max_bytes=512 * 1024)
        assert middleware.app == mock_app
        assert middleware.max_bytes == 512 * 1024

    def test_default_max_bytes(self, mock_app):
        middleware = Middleware(mock_app)
        assert middleware.app == mock_app
        assert middleware.max_bytes == 1024 * 1024

    def test_none_app(self):
        with pytest.raises(TypeError):
            Middleware(None)

    def test_invalid_max_bytes_type(self, mock_app):
        with pytest.raises(TypeError):
            Middleware(mock_app, max_bytes="not an integer")

    def test_negative_max_bytes(self, mock_app):
        with pytest.raises(ValueError):
            Middleware(mock_app, max_bytes=-1024)

    def test_zero_max_bytes(self, mock_app):
        with pytest.raises(ValueError):
            Middleware(mock_app, max_bytes=0)