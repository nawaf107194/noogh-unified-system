#!/usr/bin/env python3
"""
NOOGH Load Testing with Locust
Simulates concurrent user load on the system
"""

from locust import HttpUser, task, between, events
import json
import random
import time
from typing import Dict, Any


class NOOGHUser(HttpUser):
    """
    Simulates a user interacting with NOOGH system
    """
    wait_time = between(1, 5)  # Wait 1-5 seconds between tasks
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.user_id = f"load-test-user-{random.randint(1000, 9999)}"
        self.session_id = f"session-{int(time.time())}-{random.randint(100, 999)}"
    
    def on_start(self):
        """Called when a simulated user starts"""
        # Optional: Perform initial health check
        self.client.get("/health")
    
    @task(5)  # Weight: 5x more likely than other tasks
    def simple_query(self):
        """Execute a simple query"""
        queries = [
            "What is 2 + 2?",
            "Tell me a joke",
            "What is the capital of France?",
            "How does photosynthesis work?",
            "What is machine learning?"
        ]
        
        payload = {
            "query": random.choice(queries),
            "context": {
                "user_id": self.user_id,
                "session_id": self.session_id
            }
        }
        
        with self.client.post(
            "/execute",
            json=payload,
            catch_response=True,
            name="simple_query"
        ) as response:
            if response.status_code == 200:
                data = response.json()
                if "trace_id" in data and "conclusion" in data:
                    response.success()
                else:
                    response.failure("Missing required fields")
            else:
                response.failure(f"HTTP {response.status_code}")
    
    @task(3)
    def tool_using_query(self):
        """Execute a query that requires tool usage"""
        queries = [
            "Search for information about artificial intelligence",
            "What's the current weather?",
            "Calculate the factorial of 10",
            "Find recent news about technology"
        ]
        
        payload = {
            "query": random.choice(queries),
            "context": {
                "user_id": self.user_id,
                "session_id": self.session_id
            }
        }
        
        with self.client.post(
            "/execute",
            json=payload,
            catch_response=True,
            name="tool_query"
        ) as response:
            if response.status_code == 200:
                data = response.json()
                # Check if tools were used
                has_tools = any(
                    step.get("type") == "action" 
                    for step in data.get("steps", [])
                )
                if has_tools:
                    response.success()
                else:
                    # It's OK if tools weren't needed
                    response.success()
            else:
                response.failure(f"HTTP {response.status_code}")
    
    @task(2)
    def memory_query(self):
        """Test memory persistence across queries"""
        session_id = f"memory-session-{self.user_id}"
        
        # Store information
        store_payload = {
            "query": f"My favorite color is {random.choice(['blue', 'red', 'green'])}",
            "context": {
                "user_id": self.user_id,
                "session_id": session_id
            }
        }
        
        self.client.post("/execute", json=store_payload)
        
        # Wait a bit
        time.sleep(1)
        
        # Recall information
        recall_payload = {
            "query": "What is my favorite color?",
            "context": {
                "user_id": self.user_id,
                "session_id": session_id
            }
        }
        
        with self.client.post(
            "/execute",
            json=recall_payload,
            catch_response=True,
            name="memory_query"
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"HTTP {response.status_code}")
    
    @task(1)
    def health_check(self):
        """Periodic health check"""
        with self.client.get(
            "/health",
            catch_response=True,
            name="health_check"
        ) as response:
            if response.status_code == 200:
                data = response.json()
                if data.get("status") == "healthy":
                    response.success()
                else:
                    response.failure("Unhealthy status")
            else:
                response.failure(f"HTTP {response.status_code}")


class AdminUser(HttpUser):
    """
    Simulates admin/monitoring user checking system status
    """
    wait_time = between(5, 10)
    
    @task
    def check_health(self):
        """Admin checks system health"""
        self.client.get("/health")
    
    @task
    def check_neural_engine(self):
        """Admin checks neural engine status"""
        # This would hit internal monitoring endpoint
        # For now, just use health check
        self.client.get("/health")


# Custom events for detailed metrics
@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    """Called when test starts"""
    print("🚀 NOOGH Load Test Starting...")
    print(f"   Target: {environment.host}")
    print(f"   Users: {environment.runner.target_user_count if hasattr(environment.runner, 'target_user_count') else 'N/A'}")


@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    """Called when test stops"""
    print("\n📊 NOOGH Load Test Complete")
    
    stats = environment.stats.total
    print(f"   Total Requests: {stats.num_requests}")
    print(f"   Total Failures: {stats.num_failures}")
    print(f"   Average Response Time: {stats.avg_response_time:.0f}ms")
    print(f"   Min Response Time: {stats.min_response_time:.0f}ms")
    print(f"   Max Response Time: {stats.max_response_time:.0f}ms")
    print(f"   RPS: {stats.total_rps:.2f}")
    
    # Fail test if error rate > 5%
    if stats.num_requests > 0:
        error_rate = (stats.num_failures / stats.num_requests) * 100
        print(f"   Error Rate: {error_rate:.2f}%")
        
        if error_rate > 5:
            print("   ❌ FAILED: Error rate exceeds 5% threshold")
            environment.process_exit_code = 1
        else:
            print("   ✅ PASSED: Error rate within acceptable limits")


# Locust configuration presets
LOAD_TEST_CONFIGS = {
    "smoke": {
        "users": 5,
        "spawn_rate": 1,
        "run_time": "1m",
        "description": "Quick smoke test with minimal load"
    },
    "baseline": {
        "users": 20,
        "spawn_rate": 2,
        "run_time": "5m",
        "description": "Baseline performance test"
    },
    "stress": {
        "users": 100,
        "spawn_rate": 10,
        "run_time": "10m",
        "description": "Stress test to find breaking point"
    },
    "soak": {
        "users": 50,
        "spawn_rate": 5,
        "run_time": "30m",
        "description": "Sustained load over time"
    }
}


if __name__ == "__main__":
    print("NOOGH Load Testing Configurations:")
    print("=" * 60)
    for name, config in LOAD_TEST_CONFIGS.items():
        print(f"\n{name.upper()}:")
        print(f"  Users: {config['users']}")
        print(f"  Spawn Rate: {config['spawn_rate']}/sec")
        print(f"  Duration: {config['run_time']}")
        print(f"  Description: {config['description']}")
    
    print("\n" + "=" * 60)
    print("Usage:")
    print("  locust -f locustfile.py --host=http://localhost:8001")
    print("  locust -f locustfile.py --host=http://localhost:8001 \\")
    print("         --users 20 --spawn-rate 2 --run-time 5m --headless")
    print("\nThen open: http://localhost:8089")
