from gateway.app.core.redis_pool import get_redis_client, RedisManager

# Simulator 1 (e.g. Health Check)
url = "redis://localhost:6379/0"
client1 = get_redis_client(url)

# Simulator 2 (e.g. Job Worker)
client2 = get_redis_client(url)

# Simulator 3 (e.g. API Request)
client3 = get_redis_client(url)

print(f"Client 1 Pool: {id(client1.connection_pool)}")
print(f"Client 2 Pool: {id(client2.connection_pool)}")
print(f"Client 3 Pool: {id(client3.connection_pool)}")

assert client1.connection_pool is client2.connection_pool
assert client2.connection_pool is client3.connection_pool

# Check Max Connections setting
print(f"Max Connections: {client1.connection_pool.max_connections}")
assert client1.connection_pool.max_connections == 50

print("✅ Redis Connection Pooling Verified: Singleton Pool Active")
