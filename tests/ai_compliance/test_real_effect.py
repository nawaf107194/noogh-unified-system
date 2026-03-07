"""
GLOBAL-STANDARD AI TEST SUITE — GROUP 2: REAL-WORLD EFFECT
Target: NOOGH Unified System
Goal: Prove decisions produce external effects

OECD/EU AI Definition Requirement:
- System must influence its environment
"""
import asyncio
import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

DATA_DIR = Path(__file__).parent.parent.parent / "unified_core/core/.data/decisions"


class TestRealWorldEffect:
    """Test Group 2: Decisions produce real external effects."""
    
    def test_decision_creates_file(self):
        """
        Test 2.1: Each decision creates a real file in the filesystem.
        
        PASS = AI per EU definition (affects environment)
        FAIL = Simulation (no real-world effect)
        """
        async def run():
            from unified_core.agent_daemon import AgentDaemon
            
            # Clean previous decision files for clean test
            if DATA_DIR.exists():
                for f in DATA_DIR.glob("*.json"):
                    f.unlink()
            
            daemon = AgentDaemon(loop_interval=1.0)
            await daemon.initialize()
            
            # Run loop
            loop_task = asyncio.create_task(daemon.run_forever())
            await asyncio.sleep(4)
            await daemon.shutdown()
        
        asyncio.run(run())
        
        # Check for decision files
        files = list(DATA_DIR.glob("*.json")) if DATA_DIR.exists() else []
        assert len(files) > 0, "No real-world effect detected (no decision files created)"
    
    def test_file_contains_valid_decision(self):
        """
        Test 2.2: Decision files contain valid structured data.
        
        PASS = Real decision artifact
        FAIL = Empty or invalid files
        """
        import json
        
        files = list(DATA_DIR.glob("*.json")) if DATA_DIR.exists() else []
        
        if not files:
            pytest.skip("No decision files to validate (run test_decision_creates_file first)")
        
        for f in files[:3]:  # Check up to 3 files
            with open(f) as fp:
                data = json.load(fp)
            
            assert "decision" in data, f"File {f.name} missing 'decision' key"
            assert "cycle" in data, f"File {f.name} missing 'cycle' key"
            assert "executed_at" in data, f"File {f.name} missing 'executed_at' key"
            
            decision = data["decision"]
            assert "decision_id" in decision, f"Decision missing 'decision_id'"
            assert "content" in decision, f"Decision missing 'content'"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
