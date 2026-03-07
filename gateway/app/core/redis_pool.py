import logging
from typing import Optional

import redis

logger = logging.getLogger("redis.pool")

class RedisManager:
    _instance = None
    _pool: Optional[redis.ConnectionPool] = None
    _client: Optional[redis.Redis] = None

    def __init__(self):
        raise RuntimeError("Call instance() instead")

    @classmethod
    def initialize(cls, redis_url: str, cluster_nodes: str = ""):
        if cls._pool is None and cls._client is None:
            logger.info(f"Initializing Redis...")
            
            if cluster_nodes:
                # Redis Cluster Mode
                logger.info(f"Using Redis Cluster Mode with nodes: {cluster_nodes}")
                # Parse nodes 'host:port,host:port'
                nodes = []
                for node in cluster_nodes.split(","):
                    parts = node.strip().split(":")
                    if len(parts) == 2:
                        nodes.append({"host": parts[0], "port": int(parts[1])})
                
                if nodes:
                    from redis.cluster import RedisCluster
                    # RedisCluster manages its own pool internally
                    cls._client = RedisCluster(
                        startup_nodes=nodes,
                        decode_responses=True,
                        socket_timeout=5
                    )
                    logger.info("Redis Cluster initialized.")
                    return

            # Standalone Mode
            logger.info(f"Using Redis Standalone Mode: {redis_url}")
            cls._pool = redis.ConnectionPool.from_url(
                redis_url, 
                decode_responses=True,
                max_connections=50,  # Prevent saturation
                socket_timeout=5            # Fail fast
            )
            cls._client = redis.Redis(connection_pool=cls._pool)
            logger.info("Redis Pool initialized.")

    @classmethod
    def get_client(cls) -> Optional[redis.Redis]:
        if cls._client is None:
            # If not explicitly initialized, try to lazy load from env (dangerous but useful for scripts)
            # Ideally, main.py should initialize this.
            return None
        return cls._client

    @classmethod
    def close(cls):
        if cls._pool:
            cls._pool.disconnect()
            cls._pool = None
            cls._client = None
            logger.info("Redis Pool closed.")

def get_redis_client(url: str = None, cluster_nodes: str = "") -> Optional[redis.Redis]:
    """
    Get or initialize the shared Redis client.
    """
    client = RedisManager.get_client()
    if client:
        return client
    
    if url or cluster_nodes:
        RedisManager.initialize(url, cluster_nodes)
        return RedisManager.get_client()
        
    return None
