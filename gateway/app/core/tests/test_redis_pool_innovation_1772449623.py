import pytest
import redis
from unittest.mock import patch

class MockRedisCluster:
    def __init__(self, startup_nodes):
        pass

    def set(self, key, value):
        return True

def test_initialize_happy_path():
    from gateway.app.core.redis_pool import RedisPool
    
    with patch('redis.RedisCluster', new_callable=MockRedisCluster) as mock_redis_cluster:
        RedisPool.initialize("redis://localhost:6379")
        assert RedisPool._client is not None
        assert isinstance(RedisPool._client, MockRedisCluster)
        assert RedisPool._pool is None

def test_initialize_with_cluster_nodes():
    from gateway.app.core.redis_pool import RedisPool
    
    with patch('gateway.app.core.redis_pool.RedisCluster') as mock_redis_cluster:
        RedisPool.initialize("redis://localhost:6379", "host1:port1,host2:port2")
        assert RedisPool._client is not None
        assert isinstance(RedisPool._client, mock_redis_cluster)
        assert RedisPool._pool is None

def test_initialize_empty_redis_url():
    from gateway.app.core.redis_pool import RedisPool
    
    with patch('redis.RedisCluster') as mock_redis_cluster:
        RedisPool.initialize("")
        assert RedisPool._client is None
        assert RedisPool._pool is None

def test_initialize_none_redis_url():
    from gateway.app.core.redis_pool import RedisPool
    
    with patch('redis.RedisCluster') as mock_redis_cluster:
        RedisPool.initialize(None)
        assert RedisPool._client is None
        assert RedisPool._pool is None

def test_initialize_empty_cluster_nodes():
    from gateway.app.core.redis_pool import RedisPool
    
    with patch('redis.RedisCluster') as mock_redis_cluster:
        RedisPool.initialize("redis://localhost:6379", "")
        assert RedisPool._client is not None
        assert isinstance(RedisPool._client, mock_redis_cluster)
        assert RedisPool._pool is None

def test_initialize_none_cluster_nodes():
    from gateway.app.core.redis_pool import RedisPool
    
    with patch('redis.RedisCluster') as mock_redis_cluster:
        RedisPool.initialize("redis://localhost:6379", None)
        assert RedisPool._client is not None
        assert isinstance(RedisPool._client, mock_redis_cluster)
        assert RedisPool._pool is None

def test_initialize_invalid_redis_url():
    from gateway.app.core.redis_pool import RedisPool
    
    with patch('redis.RedisCluster') as mock_redis_cluster:
        RedisPool.initialize("invalid://url")
        assert RedisPool._client is None
        assert RedisPool._pool is None

def test_initialize_invalid_cluster_nodes_format():
    from gateway.app.core.redis_pool import RedisPool
    
    with patch('redis.RedisCluster') as mock_redis_cluster:
        RedisPool.initialize("redis://localhost:6379", "invalid_node")
        assert RedisPool._client is None
        assert RedisPool._pool is None

def test_initialize_async_behavior():
    from gateway.app.core.redis_pool import RedisPool
    
    with patch('gateway.app.core.redis_pool.RedisCluster') as mock_redis_cluster:
        with pytest.raises(NotImplementedError):
            RedisPool.initialize("redis://localhost:6379", asyncio=True)