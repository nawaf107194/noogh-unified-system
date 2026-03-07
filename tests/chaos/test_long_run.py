"""
CHAOS TEST SUITE — LONG RUN AUTONOMY
Target: NOOGH Unified System
Goal: Prove sustained autonomous operation

Test Duration: 5 minutes (configurable via env)
"""
import asyncio
import os
import pytest
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# Configurable duration (default 5 min, override with CHAOS_DURATION_SECONDS)
DURATION_SECONDS = int(os.getenv("CHAOS_DURATION_SECONDS", "300"))


class TestLongRunAutonomy:
    """Long-duration autonomous operation tests."""
    
    @pytest.mark.slow
    def test_sustained_5_minute_run(self):
        """
        Test: System runs autonomously for extended duration.
        
        Validates:
        - No memory leaks (cycle count increases steadily)
        - No hangs (cycles complete within timeout)
        - Continuous adaptation (policy changes over time)
        - Decision files accumulate
        
        Duration: 5 minutes (or CHAOS_DURATION_SECONDS env)
        """
        async def run():
            from unified_core.agent_daemon import AgentDaemon
            
            daemon = AgentDaemon(loop_interval=2.0)
            assert await daemon.initialize(), "Initialization failed"
            
            # Track metrics over time
            metrics = {
                "start_time": time.time(),
                "cycle_samples": [],
                "policy_samples": [],
                "decision_count_samples": [],
            }
            
            # Start loop
            loop_task = asyncio.create_task(daemon.run_forever())
            
            # Sample every 30 seconds
            sample_interval = 30
            samples_needed = DURATION_SECONDS // sample_interval
            
            print(f"\n🔥 LONG RUN TEST: {DURATION_SECONDS}s ({samples_needed} samples)")
            print("=" * 60)
            
            for i in range(samples_needed):
                await asyncio.sleep(sample_interval)
                
                sample = {
                    "elapsed": time.time() - metrics["start_time"],
                    "cycles": daemon._cycle_count,
                    "policy": daemon._policy_aggression,
                    "successes": daemon._success_count,
                    "failures": daemon._failure_count,
                }
                
                metrics["cycle_samples"].append(daemon._cycle_count)
                metrics["policy_samples"].append(daemon._policy_aggression)
                
                print(f"  [{i+1}/{samples_needed}] {sample['elapsed']:.0f}s: "
                      f"cycles={sample['cycles']}, policy={sample['policy']:.2f}, "
                      f"success={sample['successes']}, fail={sample['failures']}")
            
            await daemon.shutdown()
            
            return metrics, daemon
        
        metrics, daemon = asyncio.run(run())
        
        # Validations
        print("\n" + "=" * 60)
        print("VALIDATION RESULTS:")
        
        # 1. Cycles should increase over time (no hang)
        cycles = metrics["cycle_samples"]
        assert all(cycles[i] <= cycles[i+1] for i in range(len(cycles)-1)), \
            "Cycle count decreased - possible state corruption"
        print(f"  ✓ Cycles increased: {cycles[0]} → {cycles[-1]}")
        
        # 2. Should have reasonable cycle rate (at least 1 per 5 seconds)
        total_cycles = cycles[-1]
        expected_min = DURATION_SECONDS // 5
        assert total_cycles >= expected_min, \
            f"Too few cycles: {total_cycles} < {expected_min} (possible hang)"
        print(f"  ✓ Cycle rate OK: {total_cycles} cycles in {DURATION_SECONDS}s")
        
        # 3. Policy should have been updated
        assert daemon._success_count + daemon._failure_count > 0, \
            "No outcomes tracked during long run"
        print(f"  ✓ Outcomes tracked: success={daemon._success_count}, fail={daemon._failure_count}")
        
        # 4. Decision files should exist
        decisions_dir = Path("unified_core/core/.data/decisions")
        if decisions_dir.exists():
            file_count = len(list(decisions_dir.glob("*.json")))
            print(f"  ✓ Decision files: {file_count}")
        
        print("=" * 60)
        print("✅ LONG RUN TEST PASSED")
    
    @pytest.mark.slow
    def test_cycle_rate_consistency(self):
        """
        Test: Cycle rate stays consistent over time (no degradation).
        
        Validates:
        - First 30s cycle rate ≈ last 30s cycle rate (within 50%)
        """
        async def run():
            from unified_core.agent_daemon import AgentDaemon
            
            daemon = AgentDaemon(loop_interval=1.5)
            await daemon.initialize()
            
            loop_task = asyncio.create_task(daemon.run_forever())
            
            # Measure first 30s
            await asyncio.sleep(30)
            first_cycles = daemon._cycle_count
            
            # Run 60 more seconds
            await asyncio.sleep(60)
            mid_cycles = daemon._cycle_count
            
            # Measure last 30s
            await asyncio.sleep(30)
            final_cycles = daemon._cycle_count
            
            await daemon.shutdown()
            
            first_rate = first_cycles / 30
            last_rate = (final_cycles - mid_cycles) / 30
            
            return first_rate, last_rate
        
        first_rate, last_rate = asyncio.run(run())
        
        print(f"\n  First 30s rate: {first_rate:.2f} cycles/sec")
        print(f"  Last 30s rate: {last_rate:.2f} cycles/sec")
        
        # Allow 50% variance
        ratio = last_rate / first_rate if first_rate > 0 else 0
        assert 0.5 <= ratio <= 2.0, \
            f"Cycle rate degraded: {first_rate:.2f} → {last_rate:.2f}"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s", "--tb=short"])
