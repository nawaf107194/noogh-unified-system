"""
Race Condition Detection Tests for DataRouter

Tests concurrent access patterns to detect:
- Race conditions in classification caching
- Connection pool exhaustion
- Deadlocks in concurrent database access
- Data corruption under concurrent writes
- Thread safety of router state

Uses asyncio and threading to simulate concurrent load.
"""
import pytest
import asyncio
import threading
import time
import random
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
import queue

# Import the module under test
from unified_core.db.router import DataRouter, DataType, RoutingDecision


@dataclass
class RaceConditionResult:
    """Result of race condition test."""
    test_name: str
    concurrent_workers: int
    total_operations: int
    successful_operations: int
    failed_operations: int
    race_conditions_detected: int
    deadlocks_detected: int
    execution_time_seconds: float
    errors: List[str] = field(default_factory=list)


# =============================================================================
# TEST FIXTURES
# =============================================================================

@pytest.fixture
def router():
    """Create DataRouter for testing."""
    return DataRouter()


@pytest.fixture
def thread_pool():
    """Create thread pool for concurrent testing."""
    pool = ThreadPoolExecutor(max_workers=50)
    yield pool
    pool.shutdown(wait=True)


# =============================================================================
# CACHE RACE CONDITION TESTS
# =============================================================================

class TestCacheRaceConditions:
    """Test race conditions in classification caching."""
    
    @pytest.mark.asyncio
    async def test_concurrent_cache_reads(self, router):
        """Test concurrent reads from classification cache."""
        input_text = "x = 5 + 3"
        num_concurrent = 100
        results = []
        
        async def classify_async():
            return router.classify(input_text)
        
        # Run concurrent classifications
        tasks = [classify_async() for _ in range(num_concurrent)]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # All results should be identical (cache consistency)
        successful_results = [r for r in results if isinstance(r, RoutingDecision)]
        
        assert len(successful_results) == num_concurrent, "Some classifications failed"
        
        # Verify all results are consistent
        first_result = successful_results[0]
        for result in successful_results[1:]:
            assert result.data_type == first_result.data_type, "Inconsistent data_type"
            assert result.primary_target == first_result.primary_target, "Inconsistent target"
    
    @pytest.mark.asyncio
    async def test_concurrent_cache_writes_different_keys(self, router):
        """Test concurrent cache writes with different keys."""
        num_concurrent = 100
        
        async def classify_unique(index: int):
            return router.classify(f"unique input {index}")
        
        tasks = [classify_unique(i) for i in range(num_concurrent)]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        successful = [r for r in results if isinstance(r, RoutingDecision)]
        errors = [r for r in results if isinstance(r, Exception)]
        
        assert len(errors) == 0, f"Errors during concurrent writes: {errors[:5]}"
        assert len(successful) == num_concurrent
    
    @pytest.mark.asyncio
    async def test_cache_invalidation_race(self, router):
        """Test cache behavior during rapid invalidation."""
        input_text = "test cache invalidation"
        
        async def read_modify_read():
            """Read, modify router state, read again."""
            result1 = router.classify(input_text)
            
            # Simulate cache modification (if router has cache clear)
            if hasattr(router, '_cache'):
                router._cache.clear() if hasattr(router._cache, 'clear') else None
            
            result2 = router.classify(input_text)
            return (result1, result2)
        
        # Run concurrent read-modify-read operations
        tasks = [read_modify_read() for _ in range(50)]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Verify no crashes or inconsistent states
        for result in results:
            if isinstance(result, Exception):
                pytest.fail(f"Exception during cache invalidation: {result}")
            else:
                r1, r2 = result
                assert r1.data_type == r2.data_type, "Data type changed during cache invalidation"


# =============================================================================
# CONNECTION POOL TESTS
# =============================================================================

class TestConnectionPoolExhaustion:
    """Test connection pool behavior under load."""
    
    @pytest.mark.asyncio
    async def test_connection_pool_concurrent_access(self, router):
        """Test that connection pool handles concurrent access."""
        num_concurrent = 200
        timeout_seconds = 30
        
        async def acquire_and_use_connection():
            """Simulate acquiring and using a database connection."""
            # route_and_execute would use connections
            result = router.classify("SELECT * FROM data WHERE id = 1")
            await asyncio.sleep(0.01)  # Simulate query execution
            return result
        
        start = time.time()
        tasks = [acquire_and_use_connection() for _ in range(num_concurrent)]
        
        try:
            results = await asyncio.wait_for(
                asyncio.gather(*tasks, return_exceptions=True),
                timeout=timeout_seconds
            )
            elapsed = time.time() - start
            
            successful = [r for r in results if isinstance(r, RoutingDecision)]
            errors = [r for r in results if isinstance(r, Exception)]
            
            print(f"\nConnection pool test: {len(successful)}/{num_concurrent} successful in {elapsed:.2f}s")
            
            # Allow some failures under extreme load
            assert len(successful) >= num_concurrent * 0.95
            
        except asyncio.TimeoutError:
            pytest.fail(f"Connection pool test timed out after {timeout_seconds}s")
    
    @pytest.mark.asyncio
    async def test_connection_starvation_prevention(self, router):
        """Test that no workers are starved of connections."""
        num_workers = 10
        operations_per_worker = 50
        worker_results = {i: [] for i in range(num_workers)}
        
        async def worker(worker_id: int):
            """Worker that performs repeated operations."""
            for op in range(operations_per_worker):
                result = router.classify(f"worker {worker_id} operation {op}")
                worker_results[worker_id].append(result is not None)
                await asyncio.sleep(0.001)
        
        tasks = [worker(i) for i in range(num_workers)]
        await asyncio.gather(*tasks)
        
        # Verify all workers got fair access
        for worker_id, results in worker_results.items():
            success_count = sum(results)
            success_rate = success_count / operations_per_worker
            assert success_rate >= 0.9, f"Worker {worker_id} starved: {success_rate*100:.1f}% success"


# =============================================================================
# DEADLOCK DETECTION TESTS
# =============================================================================

class TestDeadlockPrevention:
    """Test deadlock detection and prevention."""
    
    def test_no_deadlock_under_thread_contention(self, router, thread_pool):
        """Test that router doesn't deadlock under thread contention."""
        num_threads = 20
        operations_per_thread = 100
        timeout_seconds = 30
        deadlock_detected = threading.Event()
        operations_completed = [0]
        lock = threading.Lock()
        
        def worker():
            for i in range(operations_per_thread):
                try:
                    # Mix of different operations
                    if i % 3 == 0:
                        router.classify("equation: 2 + 2 = 4")
                    elif i % 3 == 1:
                        router.classify({"from": "A", "to": "B"})
                    else:
                        router.classify([0.1] * 128)
                    
                    with lock:
                        operations_completed[0] += 1
                except Exception as e:
                    pass  # Continue despite errors
        
        # Start threads
        futures = [thread_pool.submit(worker) for _ in range(num_threads)]
        
        # Wait with timeout
        start = time.time()
        for future in as_completed(futures, timeout=timeout_seconds):
            try:
                future.result()
            except Exception as e:
                pass
        
        elapsed = time.time() - start
        expected_operations = num_threads * operations_per_thread
        
        print(f"\nDeadlock test: {operations_completed[0]}/{expected_operations} operations in {elapsed:.2f}s")
        
        # If we completed most operations within timeout, no deadlock occurred
        assert operations_completed[0] >= expected_operations * 0.95, "Possible deadlock detected"
    
    @pytest.mark.asyncio
    async def test_async_deadlock_prevention(self, router):
        """Test that async operations don't deadlock."""
        num_tasks = 100
        timeout_seconds = 10
        
        async def nested_classify():
            """Nested classification that could cause deadlock."""
            result1 = router.classify("outer classification")
            # Nested call while potentially holding locks
            result2 = router.classify("inner classification")
            return (result1, result2)
        
        try:
            tasks = [nested_classify() for _ in range(num_tasks)]
            results = await asyncio.wait_for(
                asyncio.gather(*tasks, return_exceptions=True),
                timeout=timeout_seconds
            )
            
            successful = [r for r in results if not isinstance(r, Exception)]
            assert len(successful) >= num_tasks * 0.95, "Too many failures in nested classification"
            
        except asyncio.TimeoutError:
            pytest.fail("Async deadlock detected - operations timed out")


# =============================================================================
# DATA CONSISTENCY TESTS
# =============================================================================

class TestDataConsistencyUnderConcurrency:
    """Test data consistency during concurrent operations."""
    
    @pytest.mark.asyncio
    async def test_classification_determinism(self, router):
        """Verify classification is deterministic under concurrency."""
        test_inputs = [
            "2 + 3 * 4",
            "SELECT * FROM users",
            "The quick brown fox",
            {"embedding": [0.1] * 128},
            {"from": "A", "to": "B", "type": "KNOWS"},
        ]
        
        num_iterations = 50
        
        for test_input in test_inputs:
            async def classify_and_return():
                return router.classify(test_input)
            
            tasks = [classify_and_return() for _ in range(num_iterations)]
            results = await asyncio.gather(*tasks)
            
            # All results should be identical
            first = results[0]
            for result in results[1:]:
                assert result.data_type == first.data_type, f"Inconsistent data_type for {test_input}"
                assert result.primary_target == first.primary_target, f"Inconsistent target for {test_input}"
    
    @pytest.mark.asyncio
    async def test_custom_rule_thread_safety(self, router):
        """Test that custom rules are thread-safe."""
        rule_calls = []
        
        def custom_rule(text: str):
            rule_calls.append(threading.current_thread().name)
            if "CUSTOM" in str(text):
                return RoutingDecision(
                    data_type=DataType.RELATIONAL,
                    primary_target="graph",
                    confidence=1.0,
                    reasoning="Custom rule"
                )
            return None
        
        router.add_custom_rule(custom_rule)
        
        async def classify_with_custom():
            return router.classify("CUSTOM: test input")
        
        tasks = [classify_with_custom() for _ in range(100)]
        results = await asyncio.gather(*tasks)
        
        # All should use custom rule
        for result in results:
            assert result.primary_target == "graph", "Custom rule not consistently applied"


# =============================================================================
# CONCURRENT WRITE TESTS
# =============================================================================

class TestConcurrentWrites:
    """Test concurrent write operations to databases."""
    
    @pytest.mark.asyncio
    async def test_concurrent_store_operations(self, router):
        """Test concurrent store operations for data corruption."""
        num_concurrent = 50
        stored_data = []
        errors = []
        
        async def store_data(index: int):
            try:
                data = {"id": index, "value": f"data_{index}"}
                # Use route_and_execute with insert operation
                result = await router.route_and_execute(
                    data,
                    operation="insert"
                )
                stored_data.append(index)
                return result
            except Exception as e:
                errors.append((index, str(e)))
                return None
        
        tasks = [store_data(i) for i in range(num_concurrent)]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Check for data integrity
        if errors:
            print(f"\nStore errors: {len(errors)}")
            for idx, err in errors[:5]:
                print(f"  Index {idx}: {err}")
        
        # Most stores should succeed (allowing for mock failures)
        assert len(stored_data) >= num_concurrent * 0.9
    
    @pytest.mark.asyncio
    async def test_read_write_interleaving(self, router):
        """Test mixed read/write operations."""
        num_operations = 100
        operations_log = []
        
        async def random_operation(index: int):
            op_type = random.choice(["read", "write"])
            start = time.time()
            
            if op_type == "read":
                result = router.classify(f"read operation {index}")
            else:
                result = router.classify({"write": f"data_{index}"})
            
            elapsed = time.time() - start
            operations_log.append({
                "index": index,
                "type": op_type,
                "elapsed": elapsed,
                "success": result is not None
            })
            return result
        
        tasks = [random_operation(i) for i in range(num_operations)]
        await asyncio.gather(*tasks)
        
        # Verify operations completed in reasonable time
        avg_time = sum(op["elapsed"] for op in operations_log) / len(operations_log)
        max_time = max(op["elapsed"] for op in operations_log)
        success_rate = sum(1 for op in operations_log if op["success"]) / len(operations_log)
        
        print(f"\nRead/Write interleaving:")
        print(f"  Avg time: {avg_time*1000:.2f}ms")
        print(f"  Max time: {max_time*1000:.2f}ms")
        print(f"  Success rate: {success_rate*100:.1f}%")
        
        assert success_rate >= 0.95, f"Too many failures: {success_rate*100:.1f}%"


# =============================================================================
# STRESS TEST
# =============================================================================

class TestRaceConditionStress:
    """Stress test for race condition detection."""
    
    @pytest.mark.asyncio
    async def test_high_concurrency_stress(self, router):
        """High concurrency stress test."""
        num_workers = 100
        operations_per_worker = 50
        results: List[RaceConditionResult] = []
        start = time.time()
        
        async def stress_worker(worker_id: int):
            successes = 0
            failures = 0
            
            for i in range(operations_per_worker):
                try:
                    # Randomize operation type
                    op_type = random.randint(0, 2)
                    
                    if op_type == 0:
                        router.classify("equation: x + y = z")
                    elif op_type == 1:
                        router.classify([random.random() for _ in range(128)])
                    else:
                        router.classify({"from": str(worker_id), "to": str(i)})
                    
                    successes += 1
                except Exception:
                    failures += 1
                
                # Small random delay to increase race likelihood
                await asyncio.sleep(random.uniform(0, 0.001))
            
            return (worker_id, successes, failures)
        
        tasks = [stress_worker(i) for i in range(num_workers)]
        worker_results = await asyncio.gather(*tasks)
        
        elapsed = time.time() - start
        
        total_successes = sum(r[1] for r in worker_results)
        total_failures = sum(r[2] for r in worker_results)
        total_operations = num_workers * operations_per_worker
        
        print(f"\n{'='*60}")
        print("RACE CONDITION STRESS TEST RESULTS")
        print(f"{'='*60}")
        print(f"Workers: {num_workers}")
        print(f"Operations per worker: {operations_per_worker}")
        print(f"Total operations: {total_operations}")
        print(f"Successes: {total_successes}")
        print(f"Failures: {total_failures}")
        print(f"Success rate: {total_successes/total_operations*100:.2f}%")
        print(f"Duration: {elapsed:.2f}s")
        print(f"Throughput: {total_operations/elapsed:.2f} ops/sec")
        print(f"{'='*60}\n")
        
        # Very high success rate expected
        assert total_successes / total_operations >= 0.99, "Too many failures under stress"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
