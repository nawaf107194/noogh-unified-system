import asyncio
import sys
import os
import unittest
from typing import List

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from unified_core.core.amla import AdversarialMilitaryAuditAgent, AMLAActionRequest
from unified_core.core.observation_stream import ObservationStream, SystemMetricsCollector, AgentHealthCollector

class TestRefactorParity(unittest.TestCase):
    def setUp(self):
        self.amla = AdversarialMilitaryAuditAgent()
        self.obs_stream = ObservationStream()

    def test_amla_modular_methods_exist(self):
        """Verify that the new private methods exist in AMLA."""
        self.assertTrue(hasattr(self.amla, '_perf_baseline_audit'))
        self.assertTrue(hasattr(self.amla, '_perf_extreme_audit'))
        self.assertTrue(hasattr(self.amla, '_perf_adversarial_audit'))
        self.assertTrue(hasattr(self.amla, '_perf_friction_audit'))
        self.assertTrue(hasattr(self.amla, '_get_test_beliefs'))
        self.assertTrue(hasattr(self.amla, '_process_belief_variations'))

    def test_observation_modular_methods_exist(self):
        """Verify that the new private methods exist in collectors."""
        sys_collector = SystemMetricsCollector()
        self.assertTrue(hasattr(sys_collector, '_get_cpu_signals'))
        self.assertTrue(hasattr(sys_collector, '_get_mem_signals'))
        self.assertTrue(hasattr(sys_collector, '_get_disk_signals'))
        
        agent_collector = AgentHealthCollector()
        self.assertTrue(hasattr(agent_collector, '_get_decision_signals'))
        self.assertTrue(hasattr(agent_collector, '_get_scar_signals'))
        self.assertTrue(hasattr(agent_collector, '_get_belief_signals'))

    async def test_amla_evaluate_smoke(self):
        """Simple smoke test for AMLA evaluate after refactor."""
        request = AMLAActionRequest(
            action_type="test_action",
            params={"test": True},
            source_beliefs=[],
            confidence=0.8
        )
        result = self.amla.evaluate(request)
        self.assertTrue(isinstance(result.action_id, str))
        self.assertGreater(len(result.action_id), 0)
        self.assertGreaterEqual(result.fragility_extreme, 0.0)

    async def test_observation_collect_smoke(self):
        """Simple smoke test for ObservationStream after refactor."""
        observations = await self.obs_stream.collect()
        self.assertIsInstance(observations, list)
        self.assertGreater(len(observations), 0)
        
        # Verify specific signals are present
        names = [obs['name'] for obs in observations]
        self.assertIn("cpu_usage", names)
        self.assertIn("memory_usage", names)

def run_async_test(coro):
    return asyncio.get_event_loop().run_until_complete(coro)

if __name__ == "__main__":
    suite = unittest.TestLoader().loadTestsFromTestCase(TestRefactorParity)
    
    # Manual execution for async tests
    tester = TestRefactorParity()
    tester.setUp()
    
    print("Running AMLA smoke test...")
    run_async_test(tester.test_amla_evaluate_smoke())
    print("Running Observation smoke test...")
    run_async_test(tester.test_observation_collect_smoke())
    
    print("Running structural existence tests...")
    unittest.main()
