import sys
from unittest.mock import MagicMock

# Mock redis module before importing anything else
sys.modules["redis"] = MagicMock()
sys.modules["redis.cluster"] = MagicMock()

# Setup mocks
mock_redis = sys.modules["redis"]
mock_redis_cluster = sys.modules["redis.cluster"]
MockCluster = MagicMock()
mock_redis_cluster.RedisCluster = MockCluster

# Now import our code
from gateway.app.core.redis_pool import RedisManager, get_redis_client

def test_cluster_initialization():
    print("Testing Redis Cluster Initialization Logic...")
    
    # Reset Singleton
    RedisManager._instance = None
    RedisManager._pool = None
    RedisManager._client = None
    
    # 1. Test Standalone (Default)
    RedisManager.initialize("redis://localhost:6379/0")
    print("Initialized Standalone.")
    
    # Verify ConnectionPool was called
    mock_redis.ConnectionPool.from_url.assert_called()
    print("✅ Standalone: ConnectionPool created.")
    
    # Reset
    RedisManager._pool = None
    RedisManager._client = None
    
    # 2. Test Cluster
    nodes = "redis-node-0:6379,redis-node-1:6379"
    RedisManager.initialize("", cluster_nodes=nodes)
    print("Initialized Cluster.")
    
    # Verify RedisCluster was instantiated with correct nodes
    MockCluster.assert_called()
    call_args = MockCluster.call_args
    print(f"Cluster Call Args: {call_args}")
    
    passed_nodes = call_args.kwargs.get("startup_nodes")
    expected_nodes = [{"host": "redis-node-0", "port": 6379}, {"host": "redis-node-1", "port": 6379}]
    
    assert passed_nodes == expected_nodes
    print("✅ Cluster: Startup nodes passed correctly.")
    
    print("✅ All Cluster Logic Verification Passed.")

if __name__ == "__main__":
    test_cluster_initialization()
