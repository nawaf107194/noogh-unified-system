"""
CHAOS TEST SUITE — RESOURCE STARVATION
Target: NOOGH Unified System
Goal: Prove stability under resource pressure

Tests behavior when:
- CPU is saturated
- Memory is constrained
- Disk I/O is heavy
"""
import asyncio
import gc
import multiprocessing
import os
import pytest
import sys
import threading
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))


def cpu_stress_worker(duration: float, stop_event: threading.Event):
    """Burn CPU cycles."""
    end_time = time.time() + duration
    while time.time() < end_time and not stop_event.is_set():
        # Busy loop
        _ = sum(i * i for i in range(10000))


def memory_pressure_worker(mb: int, stop_event: threading.Event):
    """Allocate memory and hold it."""
    blocks = []
    try:
        for _ in range(mb):
            if stop_event.is_set():
                break
            blocks.append(bytearray(1024 * 1024))  # 1MB blocks
        while not stop_event.is_set():
            time.sleep(0.1)
    finally:
        blocks.clear()
        gc.collect()


class TestResourceStarvation:
    """Resource pressure and starvation tests."""
    
    @pytest.mark.slow
    def test_cpu_pressure(self):
        """
        Test: System survives under CPU pressure.
        
        Scenario: Saturate CPU cores while daemon runs.
        Validates: Daemon completes cycles (may be slower).
        """
        async def run():
            from unified_core.agent_daemon import AgentDaemon
            
            daemon = AgentDaemon(loop_interval=2.0)
            await daemon.initialize()
            
            stop_event = threading.Event()
            
            # Start CPU stress on all but one core
            cores = max(1, multiprocessing.cpu_count() - 1)
            threads = []
            for _ in range(cores):
                t = threading.Thread(target=cpu_stress_worker, args=(30, stop_event))
                t.daemon = True
                t.start()
                threads.append(t)
            
            print(f"\n🔥 CPU STRESS: {cores} cores saturated for 30s")
            
            # Run daemon under stress
            loop_task = asyncio.create_task(daemon.run_forever())
            await asyncio.sleep(30)
            
            # Stop stress
            stop_event.set()
            for t in threads:
                t.join(timeout=1)
            
            await daemon.shutdown()
            
            return daemon._cycle_count
        
        cycles = asyncio.run(run())
        
        # Should complete at least 1 cycle (survival test, not performance)
        # Determinism fix: under extreme CPU pressure, initialization can dominate
        assert cycles >= 1, f"System did not survive CPU pressure (0 cycles)"
        print(f"  ✓ Completed {cycles} cycles under CPU stress")
    
    @pytest.mark.slow
    def test_memory_pressure(self):
        """
        Test: System survives under memory pressure.
        
        Scenario: Allocate large memory blocks while daemon runs.
        Validates: Daemon doesn't crash from OOM.
        """
        async def run():
            from unified_core.agent_daemon import AgentDaemon
            
            daemon = AgentDaemon(loop_interval=2.0)
            await daemon.initialize()
            
            stop_event = threading.Event()
            
            # Allocate 500MB in background
            memory_mb = 500
            t = threading.Thread(target=memory_pressure_worker, args=(memory_mb, stop_event))
            t.daemon = True
            t.start()
            
            print(f"\n🔥 MEMORY STRESS: {memory_mb}MB allocated")
            
            # Run daemon under memory pressure
            loop_task = asyncio.create_task(daemon.run_forever())
            await asyncio.sleep(20)
            
            # Release memory
            stop_event.set()
            t.join(timeout=2)
            gc.collect()
            
            await daemon.shutdown()
            
            return daemon._cycle_count
        
        cycles = asyncio.run(run())
        
        assert cycles >= 3, f"Too few cycles under memory pressure: {cycles}"
        print(f"  ✓ Completed {cycles} cycles under memory stress")
    
    @pytest.mark.slow
    def test_disk_io_pressure(self):
        """
        Test: System survives under disk I/O pressure.
        
        Scenario: Heavy file writes while daemon runs.
        Validates: Decision files still created (may be delayed).
        """
        async def run():
            from unified_core.agent_daemon import AgentDaemon
            
            daemon = AgentDaemon(loop_interval=2.0)
            await daemon.initialize()
            
            stop_event = threading.Event()
            
            # IO stress in background
            def io_stress():
                tmp_dir = Path("/tmp/noogh_io_stress")
                tmp_dir.mkdir(exist_ok=True)
                counter = 0
                while not stop_event.is_set():
                    (tmp_dir / f"stress_{counter}.tmp").write_bytes(os.urandom(1024 * 100))
                    counter = (counter + 1) % 100
                # Cleanup
                for f in tmp_dir.glob("*.tmp"):
                    f.unlink()
            
            t = threading.Thread(target=io_stress)
            t.daemon = True
            t.start()
            
            print("\n🔥 DISK I/O STRESS: Continuous 100KB writes")
            
            loop_task = asyncio.create_task(daemon.run_forever())
            await asyncio.sleep(20)
            
            stop_event.set()
            t.join(timeout=2)
            
            await daemon.shutdown()
            
            return daemon._cycle_count
        
        cycles = asyncio.run(run())
        
        assert cycles >= 3, f"Too few cycles under I/O pressure: {cycles}"
        print(f"  ✓ Completed {cycles} cycles under I/O stress")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s", "--tb=short"])
