"""
DataRouter Performance Benchmarks

Comprehensive performance profiling for the DataRouter:
- Classification latency (p50, p95, p99, p99.9)
- Throughput measurement (operations/second)
- Memory usage analysis
- Cache hit rate optimization
- Database connection overhead
- Scalability testing

Requires pytest-benchmark for detailed benchmarking.
"""
import pytest
import asyncio
import time
import statistics
import random
import gc
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime
import json

# Import module under test
from unified_core.db.router import DataRouter, DataType, RoutingDecision

# Try to import benchmark plugin
try:
    from pytest_benchmark.fixture import BenchmarkFixture
    BENCHMARK_AVAILABLE = True
except ImportError:
    BENCHMARK_AVAILABLE = False


@dataclass
class PerformanceResult:
    """Performance test result."""
    test_name: str
    iterations: int
    total_time_seconds: float
    mean_latency_ms: float
    p50_latency_ms: float
    p95_latency_ms: float
    p99_latency_ms: float
    p999_latency_ms: float
    throughput_ops_sec: float
    memory_delta_bytes: int = 0


# =============================================================================
# PERFORMANCE TEST DATA
# =============================================================================

# Different input types for comprehensive testing
EQUATION_INPUTS = [
    "2 + 3 * 4",
    "sin(x) + cos(y)",
    "x = sqrt(16) + log(100)",
    "(a + b) * (c - d) / e",
    "integral(x^2, x, 0, 1)",
]

SEMANTIC_INPUTS = [
    "The quick brown fox jumps over the lazy dog",
    "Machine learning is transforming the way we process data",
    "Artificial general intelligence represents a significant milestone",
    "Natural language processing enables computers to understand human language",
    "Deep neural networks have revolutionized pattern recognition",
]

RELATIONAL_INPUTS = [
    {"from": "Alice", "to": "Bob", "type": "KNOWS"},
    {"source": "Document1", "target": "Document2", "relationship": "REFERENCES"},
    {"entity": "Company", "relation": "HAS_SUBSIDIARY", "target": "Subsidiary"},
]

EMBEDDING_INPUTS = [
    [random.random() for _ in range(128)],
    [random.random() for _ in range(256)],
    [random.random() for _ in range(512)],
]


def generate_mixed_workload(n: int) -> List[Any]:
    """Generate a mixed workload of n inputs."""
    workload = []
    for i in range(n):
        choice = i % 4
        if choice == 0:
            workload.append(random.choice(EQUATION_INPUTS))
        elif choice == 1:
            workload.append(random.choice(SEMANTIC_INPUTS))
        elif choice == 2:
            workload.append(random.choice(RELATIONAL_INPUTS))
        else:
            workload.append([random.random() for _ in range(128)])
    return workload


# =============================================================================
# FIXTURES
# =============================================================================

@pytest.fixture
def router():
    """Create fresh router for each test."""
    return DataRouter()


@pytest.fixture
def warmed_router():
    """Create router with warmed cache."""
    r = DataRouter()
    # Warm up with sample inputs
    for inp in EQUATION_INPUTS + SEMANTIC_INPUTS:
        r.classify(inp)
    for inp in RELATIONAL_INPUTS:
        r.classify(inp)
    return r


# =============================================================================
# LATENCY BENCHMARKS
# =============================================================================

class TestLatencyBenchmarks:
    """Latency measurement tests."""
    
    def test_cold_start_latency(self, router):
        """Measure cold start classification latency."""
        latencies = []
        
        # Use unique inputs to avoid cache hits
        for i in range(100):
            inp = f"unique equation {i}: x + {i} = {i+1}"
            start = time.perf_counter()
            router.classify(inp)
            elapsed = (time.perf_counter() - start) * 1000  # Convert to ms
            latencies.append(elapsed)
        
        result = PerformanceResult(
            test_name="cold_start_latency",
            iterations=len(latencies),
            total_time_seconds=sum(latencies) / 1000,
            mean_latency_ms=statistics.mean(latencies),
            p50_latency_ms=statistics.quantiles(latencies, n=2)[0],
            p95_latency_ms=sorted(latencies)[int(len(latencies) * 0.95)],
            p99_latency_ms=sorted(latencies)[int(len(latencies) * 0.99)],
            p999_latency_ms=sorted(latencies)[-1],  # Max for small sample
            throughput_ops_sec=len(latencies) / (sum(latencies) / 1000)
        )
        
        print(f"\n{'-'*50}")
        print(f"Cold Start Latency ({result.iterations} iterations)")
        print(f"  Mean: {result.mean_latency_ms:.3f}ms")
        print(f"  P50:  {result.p50_latency_ms:.3f}ms")
        print(f"  P95:  {result.p95_latency_ms:.3f}ms")
        print(f"  P99:  {result.p99_latency_ms:.3f}ms")
        print(f"  Throughput: {result.throughput_ops_sec:.0f} ops/sec")
        print(f"{'-'*50}")
        
        # Performance assertions
        assert result.mean_latency_ms < 10, f"Mean latency too high: {result.mean_latency_ms}ms"
        assert result.p99_latency_ms < 50, f"P99 latency too high: {result.p99_latency_ms}ms"
    
    def test_warm_cache_latency(self, router):
        """Measure latency with warm cache."""
        input_text = "cached equation: x + y = z"
        
        # Warm the cache
        for _ in range(10):
            router.classify(input_text)
        
        latencies = []
        for _ in range(1000):
            start = time.perf_counter()
            router.classify(input_text)
            elapsed = (time.perf_counter() - start) * 1000
            latencies.append(elapsed)
        
        result = PerformanceResult(
            test_name="warm_cache_latency",
            iterations=len(latencies),
            total_time_seconds=sum(latencies) / 1000,
            mean_latency_ms=statistics.mean(latencies),
            p50_latency_ms=statistics.quantiles(latencies, n=2)[0],
            p95_latency_ms=sorted(latencies)[int(len(latencies) * 0.95)],
            p99_latency_ms=sorted(latencies)[int(len(latencies) * 0.99)],
            p999_latency_ms=sorted(latencies)[int(len(latencies) * 0.999)],
            throughput_ops_sec=len(latencies) / (sum(latencies) / 1000)
        )
        
        print(f"\n{'-'*50}")
        print(f"Warm Cache Latency ({result.iterations} iterations)")
        print(f"  Mean: {result.mean_latency_ms:.4f}ms")
        print(f"  P50:  {result.p50_latency_ms:.4f}ms")
        print(f"  P95:  {result.p95_latency_ms:.4f}ms")
        print(f"  P99:  {result.p99_latency_ms:.4f}ms")
        print(f"  Throughput: {result.throughput_ops_sec:.0f} ops/sec")
        print(f"{'-'*50}")
        
        # Cache hits should be very fast
        assert result.mean_latency_ms < 1, f"Mean latency too high: {result.mean_latency_ms}ms"
    
    def test_latency_by_input_type(self, router):
        """Measure latency for each input type."""
        input_types = {
            "equation": EQUATION_INPUTS[0],
            "semantic": SEMANTIC_INPUTS[0],
            "relational": RELATIONAL_INPUTS[0],
            "embedding": EMBEDDING_INPUTS[0],
        }
        
        results = {}
        for input_type, input_val in input_types.items():
            latencies = []
            for _ in range(100):
                # Force cache miss with slight variation
                test_input = input_val if not isinstance(input_val, str) else f"{input_val} {random.randint(0, 9999)}"
                start = time.perf_counter()
                router.classify(test_input)
                elapsed = (time.perf_counter() - start) * 1000
                latencies.append(elapsed)
            
            results[input_type] = {
                "mean": statistics.mean(latencies),
                "p50": statistics.quantiles(latencies, n=2)[0],
                "p95": sorted(latencies)[int(len(latencies) * 0.95)],
            }
        
        print(f"\n{'-'*50}")
        print("Latency by Input Type")
        for input_type, metrics in results.items():
            print(f"  {input_type:12}: mean={metrics['mean']:.3f}ms, p50={metrics['p50']:.3f}ms, p95={metrics['p95']:.3f}ms")
        print(f"{'-'*50}")


# =============================================================================
# THROUGHPUT BENCHMARKS
# =============================================================================

class TestThroughputBenchmarks:
    """Throughput measurement tests."""
    
    def test_single_thread_throughput(self, router):
        """Measure single-threaded throughput."""
        workload = generate_mixed_workload(10000)
        
        start = time.perf_counter()
        for item in workload:
            router.classify(item)
        elapsed = time.perf_counter() - start
        
        throughput = len(workload) / elapsed
        
        print(f"\n{'-'*50}")
        print(f"Single Thread Throughput")
        print(f"  Operations: {len(workload)}")
        print(f"  Duration: {elapsed:.2f}s")
        print(f"  Throughput: {throughput:.0f} ops/sec")
        print(f"{'-'*50}")
        
        assert throughput > 1000, f"Throughput too low: {throughput} ops/sec"
    
    @pytest.mark.asyncio
    async def test_async_throughput(self, router):
        """Measure async throughput with concurrent operations."""
        num_concurrent = 100
        operations_each = 100
        workload = generate_mixed_workload(num_concurrent * operations_each)
        
        async def process_batch(items: List[Any]):
            for item in items:
                router.classify(item)
        
        # Split workload into batches
        batch_size = operations_each
        batches = [workload[i:i+batch_size] for i in range(0, len(workload), batch_size)]
        
        start = time.perf_counter()
        await asyncio.gather(*[process_batch(batch) for batch in batches])
        elapsed = time.perf_counter() - start
        
        throughput = len(workload) / elapsed
        
        print(f"\n{'-'*50}")
        print(f"Async Throughput ({num_concurrent} concurrent batches)")
        print(f"  Operations: {len(workload)}")
        print(f"  Duration: {elapsed:.2f}s")
        print(f"  Throughput: {throughput:.0f} ops/sec")
        print(f"{'-'*50}")
        
        assert throughput > 5000, f"Async throughput too low: {throughput} ops/sec"
    
    def test_sustained_throughput(self, router):
        """Measure sustained throughput over time."""
        duration_seconds = 5
        operations_completed = 0
        throughput_samples = []
        
        start = time.perf_counter()
        sample_start = start
        sample_ops = 0
        
        workload = generate_mixed_workload(1000)  # Reusable workload
        
        while time.perf_counter() - start < duration_seconds:
            router.classify(random.choice(workload))
            operations_completed += 1
            sample_ops += 1
            
            # Sample every 0.5 seconds
            if time.perf_counter() - sample_start >= 0.5:
                sample_throughput = sample_ops / 0.5
                throughput_samples.append(sample_throughput)
                sample_start = time.perf_counter()
                sample_ops = 0
        
        elapsed = time.perf_counter() - start
        overall_throughput = operations_completed / elapsed
        
        print(f"\n{'-'*50}")
        print(f"Sustained Throughput (over {duration_seconds}s)")
        print(f"  Total operations: {operations_completed}")
        print(f"  Overall throughput: {overall_throughput:.0f} ops/sec")
        if throughput_samples:
            print(f"  Min throughput: {min(throughput_samples):.0f} ops/sec")
            print(f"  Max throughput: {max(throughput_samples):.0f} ops/sec")
            print(f"  Std dev: {statistics.stdev(throughput_samples):.0f} ops/sec")
        print(f"{'-'*50}")


# =============================================================================
# MEMORY BENCHMARKS
# =============================================================================

class TestMemoryBenchmarks:
    """Memory usage tests."""
    
    def test_memory_per_classification(self, router):
        """Measure memory overhead per classification."""
        gc.collect()
        
        try:
            import psutil
            process = psutil.Process()
            baseline_memory = process.memory_info().rss
        except ImportError:
            pytest.skip("psutil not available for memory testing")
        
        # Perform many unique classifications
        for i in range(10000):
            router.classify(f"unique input number {i}")
        
        gc.collect()
        final_memory = process.memory_info().rss
        memory_increase = final_memory - baseline_memory
        memory_per_op = memory_increase / 10000
        
        print(f"\n{'-'*50}")
        print(f"Memory Usage")
        print(f"  Baseline: {baseline_memory / 1024 / 1024:.2f} MB")
        print(f"  Final: {final_memory / 1024 / 1024:.2f} MB")
        print(f"  Increase: {memory_increase / 1024 / 1024:.2f} MB")
        print(f"  Per operation: {memory_per_op:.2f} bytes")
        print(f"{'-'*50}")
        
        # Memory shouldn't grow unboundedly
        assert memory_increase < 100 * 1024 * 1024, f"Memory increase too large: {memory_increase / 1024 / 1024:.2f}MB"
    
    def test_cache_memory_efficiency(self, router):
        """Test cache memory efficiency."""
        gc.collect()
        
        try:
            import psutil
            process = psutil.Process()
        except ImportError:
            pytest.skip("psutil not available")
        
        # Measure memory with varying cache sizes
        measurements = []
        
        for cache_size in [100, 1000, 5000, 10000]:
            # Clear cache if possible
            if hasattr(router, '_cache'):
                router._cache.clear() if hasattr(router._cache, 'clear') else None
            gc.collect()
            
            baseline = process.memory_info().rss
            
            # Fill cache
            for i in range(cache_size):
                router.classify(f"cache entry {i}")
            
            gc.collect()
            after = process.memory_info().rss
            
            measurements.append({
                'cache_size': cache_size,
                'memory_bytes': after - baseline,
                'bytes_per_entry': (after - baseline) / cache_size
            })
        
        print(f"\n{'-'*50}")
        print(f"Cache Memory Efficiency")
        for m in measurements:
            print(f"  {m['cache_size']:6} entries: {m['memory_bytes']/1024:.1f}KB ({m['bytes_per_entry']:.1f} bytes/entry)")
        print(f"{'-'*50}")


# =============================================================================
# SCALABILITY BENCHMARKS
# =============================================================================

class TestScalabilityBenchmarks:
    """Scalability testing."""
    
    def test_input_size_scalability(self, router):
        """Test performance scaling with input size."""
        sizes = [10, 100, 1000, 10000]
        results = []
        
        for size in sizes:
            input_text = "x " * size  # Varying size input
            
            latencies = []
            for _ in range(10):
                start = time.perf_counter()
                router.classify(input_text)
                elapsed = (time.perf_counter() - start) * 1000
                latencies.append(elapsed)
            
            results.append({
                'size': size,
                'mean_latency': statistics.mean(latencies),
                'max_latency': max(latencies)
            })
        
        print(f"\n{'-'*50}")
        print(f"Input Size Scalability")
        for r in results:
            print(f"  Size {r['size']:6}: mean={r['mean_latency']:.2f}ms, max={r['max_latency']:.2f}ms")
        print(f"{'-'*50}")
        
        # Check for reasonable scaling (should not be worse than O(n))
        ratio = results[-1]['mean_latency'] / results[0]['mean_latency']
        size_ratio = sizes[-1] / sizes[0]
        
        assert ratio < size_ratio * 2, f"Scaling worse than linear: {ratio:.1f}x slowdown for {size_ratio}x input"
    
    @pytest.mark.asyncio
    async def test_concurrent_user_scalability(self, router):
        """Test performance scaling with concurrent users."""
        user_counts = [1, 10, 50, 100]
        results = []
        
        for num_users in user_counts:
            operations_per_user = 100
            
            async def user_workload():
                latencies = []
                for _ in range(operations_per_user):
                    start = time.perf_counter()
                    router.classify(f"user request {random.randint(0, 1000)}")
                    elapsed = (time.perf_counter() - start) * 1000
                    latencies.append(elapsed)
                return latencies
            
            start = time.perf_counter()
            all_latencies = await asyncio.gather(*[user_workload() for _ in range(num_users)])
            elapsed = time.perf_counter() - start
            
            flat_latencies = [l for user_latencies in all_latencies for l in user_latencies]
            
            results.append({
                'users': num_users,
                'total_ops': num_users * operations_per_user,
                'duration': elapsed,
                'throughput': (num_users * operations_per_user) / elapsed,
                'mean_latency': statistics.mean(flat_latencies),
                'p99_latency': sorted(flat_latencies)[int(len(flat_latencies) * 0.99)]
            })
        
        print(f"\n{'-'*50}")
        print(f"Concurrent User Scalability")
        for r in results:
            print(f"  {r['users']:3} users: {r['throughput']:.0f} ops/sec, p99={r['p99_latency']:.2f}ms")
        print(f"{'-'*50}")


# =============================================================================
# COMPREHENSIVE PERFORMANCE REPORT
# =============================================================================

class TestPerformanceReport:
    """Generate comprehensive performance report."""
    
    def test_generate_performance_report(self, router):
        """Generate full performance benchmark report."""
        report = {
            "timestamp": datetime.now().isoformat(),
            "benchmarks": {}
        }
        
        # Cold start latency
        latencies = []
        for i in range(100):
            start = time.perf_counter()
            router.classify(f"cold start test {i}")
            latencies.append((time.perf_counter() - start) * 1000)
        
        report["benchmarks"]["cold_start"] = {
            "iterations": 100,
            "mean_ms": statistics.mean(latencies),
            "p50_ms": statistics.quantiles(latencies, n=2)[0],
            "p99_ms": sorted(latencies)[99],
        }
        
        # Warm cache latency  
        for _ in range(10):
            router.classify("warm cache test")
        
        latencies = []
        for _ in range(1000):
            start = time.perf_counter()
            router.classify("warm cache test")
            latencies.append((time.perf_counter() - start) * 1000)
        
        report["benchmarks"]["warm_cache"] = {
            "iterations": 1000,
            "mean_ms": statistics.mean(latencies),
            "p50_ms": statistics.quantiles(latencies, n=2)[0],
            "p99_ms": sorted(latencies)[int(999 * 0.99)],
        }
        
        # Throughput
        workload = generate_mixed_workload(5000)
        start = time.perf_counter()
        for item in workload:
            router.classify(item)
        elapsed = time.perf_counter() - start
        
        report["benchmarks"]["throughput"] = {
            "operations": 5000,
            "duration_seconds": elapsed,
            "ops_per_second": 5000 / elapsed,
        }
        
        # Print report
        print(f"\n{'='*60}")
        print("PERFORMANCE BENCHMARK REPORT")
        print(f"{'='*60}")
        print(f"Generated: {report['timestamp']}")
        print(f"\nCold Start Latency:")
        print(f"  Mean: {report['benchmarks']['cold_start']['mean_ms']:.3f}ms")
        print(f"  P50:  {report['benchmarks']['cold_start']['p50_ms']:.3f}ms")
        print(f"  P99:  {report['benchmarks']['cold_start']['p99_ms']:.3f}ms")
        print(f"\nWarm Cache Latency:")
        print(f"  Mean: {report['benchmarks']['warm_cache']['mean_ms']:.4f}ms")
        print(f"  P50:  {report['benchmarks']['warm_cache']['p50_ms']:.4f}ms")
        print(f"  P99:  {report['benchmarks']['warm_cache']['p99_ms']:.4f}ms")
        print(f"\nThroughput:")
        print(f"  {report['benchmarks']['throughput']['ops_per_second']:.0f} ops/sec")
        print(f"{'='*60}\n")
        
        # Write JSON report
        report_path = "/home/noogh/projects/noogh_unified_system/src/reports/phase1_benchmark_results.json"
        try:
            with open(report_path, 'w') as f:
                json.dump(report, f, indent=2)
            print(f"Report saved to: {report_path}")
        except Exception as e:
            print(f"Could not save report: {e}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
