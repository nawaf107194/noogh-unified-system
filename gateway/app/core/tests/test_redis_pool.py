import pytest

from gateway.app.core.redis_pool import get_client

class TestRedisPool:

    def test_happy_path(self):
        # Arrange
        cls = type('MockClass', (), {'_client': redis.Redis(host='localhost', port=6379)})
        
        # Act
        result = get_client(cls)
        
        # Assert
        assert isinstance(result, redis.Redis)

    def test_edge_case_none_client(self):
        # Arrange
        cls = type('MockClass', (), {'_client': None})
        
        # Act
        result = get_client(cls)
        
        # Assert
        assert result is None

    def test_edge_case_uninitialized_client(self):
        # Arrange
        class MockClass:
            _client = None
        
        # Act
        result = get_client(MockClass)
        
        # Assert
        assert result is None

    def test_error_case_invalid_input(self):
        with pytest.raises(TypeError):
            get_client("not a class")