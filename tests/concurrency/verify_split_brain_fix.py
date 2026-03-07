
import sys
import os
import time
import multiprocessing
import unittest

# Add src to path
sys.path.append("/home/noogh/projects/noogh_unified_system/src")

from unified_core.core.world_model import WorldModel
from unified_core.core.memory_store import UnifiedMemoryStore

def process_a_writer():
    print("[Proc A] Writing belief...")
    wm = WorldModel()
    belief = wm.add_belief("The Sky is Blue")
    print(f"[Proc A] Wrote ID: {belief.belief_id}")
    return belief.belief_id

def process_b_reader(belief_id):
    print(f"[Proc B] Reading belief ID: {belief_id}...")
    wm = WorldModel()
    # Wait for sync if needed (should be near instant with Redis)
    for _ in range(10):
        beliefs = wm.get_usable_beliefs()
        for b in beliefs:
            if b.belief_id == belief_id:
                print(f"[Proc B] Found belief! Proposition: {b.proposition}")
                return True
        time.sleep(0.1)
    print("[Proc B] Belief NOT FOUND.")
    return False

class TestSplitBrainFix(unittest.TestCase):
    
    def test_shared_memory(self):
        print("\n[TEST] Verifying Shared Memory across Processes...")
        
        # 1. Start Proc A to write
        with multiprocessing.Pool(processes=1) as pool:
            result_a = pool.apply(process_a_writer)
            belief_id = result_a
        
        # 2. Start Proc B to read
        with multiprocessing.Pool(processes=1) as pool:
            found = pool.apply(process_b_reader, (belief_id,))
        
        self.assertTrue(found, "Process B failed to see belief written by Process A")
        print("✅ Split-Brain Resolved: Processes share state.")

if __name__ == "__main__":
    unittest.main()
