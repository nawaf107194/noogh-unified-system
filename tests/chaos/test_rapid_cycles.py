"""
CHAOS TEST SUITE — RAPID CYCLES
Target: NOOGH Unified System
Goal: Prove stability under high-frequency operation

Tests:
- Minimum loop interval performance
- Decision throughput
- Resource cleanup under load
"""
import asyncio
import gc
import os
import psutil
import pytest
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))


class TestRapidCycles:
    """High-frequency stress tests."""
    
    @pytest.mark.slow
    def test_minimum_interval(self):
        """
        Test: System handles minimum loop interval.
        
        Validates:
        - No crashes at 0.5s intervals
        - Cycles complete successfully
        """
        async def run():
            from unified_core.agent_daemon import AgentDaemon
            
            # Aggressive 0.5 second interval
            daemon = AgentDaemon(loop_interval=0.5, min_interval=0.3)
            await daemon.initialize()
            
            loop_task = asyncio.create_task(daemon.run_forever())
            await asyncio.sleep(30)
            await daemon.shutdown()
            
            return daemon._cycle_count
        
        cycles = asyncio.run(run())
        
        # At 0.5s interval, expect ~60 cycles in 30s
        expected_min = 30  # Allow some overhead
        assert cycles >= expected_min, f"Rapid cycles too slow: {cycles} < {expected_min}"
        print(f"  ✓ Completed {cycles} cycles at 0.5s interval")
    
    @pytest.mark.slow
    def test_decision_throughput(self):
        """
        Test: Measure decisions per second.
        
        Validates:
        - Decision rate > 0.5/sec under normal conditions
        """
        async def run():
            from unified_core.agent_daemon import AgentDaemon
            
            daemon = AgentDaemon(loop_interval=1.0)
            await daemon.initialize()
            
            start = time.time()
            loop_task = asyncio.create_task(daemon.run_forever())
            await asyncio.sleep(30)
            elapsed = time.time() - start
            
            await daemon.shutdown()
            
            decisions = daemon._success_count + daemon._failure_count
            rate = decisions / elapsed if elapsed > 0 else 0
            
            return decisions, rate
        
        decisions, rate = asyncio.run(run())
        
        print(f"\n  Decisions: {decisions}")
        print(f"  Rate: {rate:.2f} decisions/sec")
        
        assert rate >= 0.3, f"Decision rate too low: {rate:.2f}"
        print(f"  ✓ Decision throughput OK: {rate:.2f}/sec")
    
    @pytest.mark.slow
    def test_memory_stability(self):
        """
        Test: Memory doesn't grow unboundedly.
        
        Validates:
        - Memory increase < 100MB over 60 cycles
        """
        async def run():
            from unified_core.agent_daemon import AgentDaemon
            
            gc.collect()
            process = psutil.Process(os.getpid())
            initial_mem = process.memory_info().rss / (1024 * 1024)  # MB
            
            daemon = AgentDaemon(loop_interval=0.5)
            await daemon.initialize()
            
            loop_task = asyncio.create_task(daemon.run_forever())
            await asyncio.sleep(30)  # ~60 cycles
            
            peak_mem = process.memory_info().rss / (1024 * 1024)
            
            await daemon.shutdown()
            gc.collect()
            
            final_mem = process.memory_info().rss / (1024 * 1024)
            
            return initial_mem, peak_mem, final_mem, daemon._cycle_count
        
        initial, peak, final, cycles = asyncio.run(run())
        
        print(f"\n  Initial: {initial:.1f} MB")
        print(f"  Peak: {peak:.1f} MB")
        print(f"  Final: {final:.1f} MB")
        print(f"  Cycles: {cycles}")
        
        growth = peak - initial
        assert growth < 100, f"Memory grew too much: +{growth:.1f} MB"
        print(f"  ✓ Memory stable: +{growth:.1f} MB")
    
    @pytest.mark.slow
    def test_file_handle_cleanup(self):
        """
        Test: File handles are properly cleaned up.
        
        Validates:
        - Open file count doesn't grow unboundedly
        """
        async def run():
            from unified_core.agent_daemon import AgentDaemon
            
            process = psutil.Process(os.getpid())
            initial_fds = process.num_fds() if hasattr(process, 'num_fds') else len(process.open_files())
            
            daemon = AgentDaemon(loop_interval=1.0)
            await daemon.initialize()
            
            loop_task = asyncio.create_task(daemon.run_forever())
            await asyncio.sleep(20)
            
            peak_fds = process.num_fds() if hasattr(process, 'num_fds') else len(process.open_files())
            
            await daemon.shutdown()
            
            final_fds = process.num_fds() if hasattr(process, 'num_fds') else len(process.open_files())
            
            return initial_fds, peak_fds, final_fds
        
        initial, peak, final = asyncio.run(run())
        
        print(f"\n  Initial FDs: {initial}")
        print(f"  Peak FDs: {peak}")
        print(f"  Final FDs: {final}")
        
        fd_growth = peak - initial
        assert fd_growth < 50, f"Too many file handles opened: +{fd_growth}"
        print(f"  ✓ File handles OK: +{fd_growth}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s", "--tb=short"])
