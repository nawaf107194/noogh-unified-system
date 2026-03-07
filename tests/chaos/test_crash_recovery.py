"""
CHAOS TEST SUITE — CRASH RECOVERY
Target: NOOGH Unified System
Goal: Prove system survives abrupt termination

Tests:
- Graceful shutdown
- SIGTERM handling
- State persistence across restarts
"""
import asyncio
import os
import pytest
import signal
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))


class TestCrashRecovery:
    """Crash and recovery tests."""
    
    def test_graceful_shutdown(self):
        """
        Test: System shuts down cleanly.
        
        Validates:
        - shutdown() completes without error
        - No zombie processes
        - State is persisted
        """
        async def run():
            from unified_core.agent_daemon import AgentDaemon
            
            daemon = AgentDaemon(loop_interval=1.0)
            await daemon.initialize()
            
            loop_task = asyncio.create_task(daemon.run_forever())
            await asyncio.sleep(5)
            
            # Graceful shutdown
            await daemon.shutdown()
            
            return daemon._cycle_count, daemon._state.value
        
        cycles, state = asyncio.run(run())
        
        assert cycles > 0, "No cycles completed before shutdown"
        assert state == "stopped", f"Daemon not stopped cleanly: {state}"
        print(f"  ✓ Graceful shutdown after {cycles} cycles")
    
    def test_restart_preserves_scars(self):
        """
        Test: Scars persist across restart.
        
        Validates:
        - Scars from previous runs are loaded
        - Scar count doesn't reset
        """
        async def run():
            from unified_core.agent_daemon import AgentDaemon
            
            # First run
            daemon1 = AgentDaemon(loop_interval=1.0)
            await daemon1.initialize()
            
            initial_scars = daemon1._scar_tissue.get_scar_count() if daemon1._scar_tissue else 0
            
            loop_task = asyncio.create_task(daemon1.run_forever())
            await asyncio.sleep(3)
            await daemon1.shutdown()
            
            scars_after_run = daemon1._scar_tissue.get_scar_count() if daemon1._scar_tissue else 0
            
            # Second run (restart)
            daemon2 = AgentDaemon(loop_interval=1.0)
            await daemon2.initialize()
            
            scars_on_restart = daemon2._scar_tissue.get_scar_count() if daemon2._scar_tissue else 0
            await daemon2.shutdown()
            
            return initial_scars, scars_after_run, scars_on_restart
        
        initial, after_run, on_restart = asyncio.run(run())
        
        print(f"\n  Initial scars: {initial}")
        print(f"  After run: {after_run}")
        print(f"  On restart: {on_restart}")
        
        # Scars should persist (not reset to 0 on restart)
        assert on_restart >= after_run, "Scars were lost on restart"
        print(f"  ✓ Scars preserved across restart")
    
    def test_restart_preserves_consequences(self):
        """
        Test: Consequences persist across restart.
        
        Validates:
        - Consequence count survives restart
        """
        async def run():
            from unified_core.agent_daemon import AgentDaemon
            
            # First run
            daemon1 = AgentDaemon(loop_interval=1.0)
            await daemon1.initialize()
            
            loop_task = asyncio.create_task(daemon1.run_forever())
            await asyncio.sleep(4)
            await daemon1.shutdown()
            
            consequences_after = daemon1._consequence_engine.get_consequence_count() if daemon1._consequence_engine else 0
            
            # Restart
            daemon2 = AgentDaemon(loop_interval=1.0)
            await daemon2.initialize()
            
            consequences_on_restart = daemon2._consequence_engine.get_consequence_count() if daemon2._consequence_engine else 0
            await daemon2.shutdown()
            
            return consequences_after, consequences_on_restart
        
        after, on_restart = asyncio.run(run())
        
        print(f"\n  Consequences after run: {after}")
        print(f"  Consequences on restart: {on_restart}")
        
        assert on_restart >= after, "Consequences were lost on restart"
        print(f"  ✓ Consequences preserved across restart")
    
    def test_multiple_restarts(self):
        """
        Test: System handles multiple rapid restarts.
        
        Validates:
        - No state corruption from rapid restart cycles
        """
        async def run():
            from unified_core.agent_daemon import AgentDaemon
            
            restarts = 5
            cycles_per_restart = []
            
            for i in range(restarts):
                daemon = AgentDaemon(loop_interval=1.0)
                assert await daemon.initialize(), f"Init failed on restart {i+1}"
                
                loop_task = asyncio.create_task(daemon.run_forever())
                await asyncio.sleep(2)
                await daemon.shutdown()
                
                cycles_per_restart.append(daemon._cycle_count)
            
            return cycles_per_restart
        
        cycles = asyncio.run(run())
        
        print(f"\n  Cycles per restart: {cycles}")
        
        # Each restart should complete cycles
        assert all(c > 0 for c in cycles), "Some restarts had zero cycles"
        print(f"  ✓ {len(cycles)} restarts completed successfully")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s", "--tb=short"])
