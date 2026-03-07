import pytest
from unittest.mock import patch
from gateway.app.core.redis_pool import RedisPool

class TestRedisPoolInitialize:

    @pytest.fixture(autouse=True)
    def setup(self):
        RedisPool._pool = None
        RedisPool._client = None

    def test_happy_path_cluster_mode(self):
        with patch('redis.cluster.RedisCluster') as mock_redis_cluster:
            cluster_nodes = "host1:6379,host2:6379"
            RedisPool.initialize("dummy_url", cluster_nodes)
            mock_redis_cluster.assert_called_once_with(
                startup_nodes=[{"host": "host1", "port": 6379}, {"host": "host2", "port": 6379}],
                decode_responses=True,
                socket_timeout=5
            )
            assert RedisPool._client is not None
            assert RedisPool._pool is None

    def test_happy_path_standalone_mode(self):
        with patch('redis.Redis') as mock_redis:
            redis_url = "redis://localhost:6379"
            RedisPool.initialize(redis_url)
            mock_redis.assert_called_once_with(
                connection_pool=RedisPool._pool,
                decode_responses=True
            )
            assert RedisPool._client is not None
            assert RedisPool._pool is not None

    def test_empty_cluster_nodes(self):
        with patch('redis.cluster.RedisCluster') as mock_redis_cluster:
            cluster_nodes = ""
            RedisPool.initialize("dummy_url", cluster_nodes)
            mock_redis_cluster.assert_not_called()
            assert RedisPool._client is None
            assert RedisPool._pool is None

    def test_none_cluster_nodes(self):
        with patch('redis.cluster.RedisCluster') as mock_redis_cluster:
            cluster_nodes = None
            RedisPool.initialize("dummy_url", cluster_nodes)
            mock_redis_cluster.assert_not_called()
            assert RedisPool._client is None
            assert RedisPool._pool is None

    def test_invalid_cluster_nodes(self):
        with patch('redis.cluster.RedisCluster') as mock_redis_cluster:
            cluster_nodes = "host1:6379,invalid_host"
            RedisPool.initialize("dummy_url", cluster_nodes)
            mock_redis_cluster.assert_not_called()
            assert RedisPool._client is None
            assert RedisPool._pool is None

    def test_empty_redis_url(self):
        with patch('redis.Redis') as mock_redis:
            redis_url = ""
            RedisPool.initialize(redis_url)
            mock_redis.assert_not_called()
            assert RedisPool._client is None
            assert RedisPool._pool is None

    def test_none_redis_url(self):
        with patch('redis.Redis') as mock_redis:
            redis_url = None
            RedisPool.initialize(redis_url)
            mock_redis.assert_not_called()
            assert RedisPool._client is None
            assert RedisPool._pool is None