import asyncio
import logging
import json
import os
from pathlib import Path

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

def repair_system():
    print("=" * 60)
    print("🛠️ NOOGH System Repair (Memory & Neurons)")
    print("=" * 60)
    
    data_dir = Path.home() / ".noogh" / "evolution"
    
    # 1. Clean EvolutionMemory (Fragile Flags)
    mem_file = data_dir / "evolution_memory.json"
    if mem_file.exists():
        try:
            with open(mem_file, 'r') as f:
                memory_data = json.load(f)
                
            fragile_count = len(memory_data.get('fragile_paths', {}))
            
            # Remove any path starting with src/test_target or src/imaginary
            keys_to_remove = [
                k for k in memory_data.get('fragile_paths', {}).keys() 
                if "test_target" in k or "imaginary_test" in k or "database.py" in k
            ]
            
            for k in keys_to_remove:
                del memory_data['fragile_paths'][k]
                
            if keys_to_remove:
                with open(mem_file, 'w') as f:
                    json.dump(memory_data, f, indent=2)
                print(f"✅ Removed {len(keys_to_remove)} test targets from Fragile list.")
            else:
                print("✅ EvolutionMemory Fragile list is already clean.")
                
        except Exception as e:
            print(f"❌ Failed to clean memory: {e}")
            
    # 2. Reset Ledger Safe Mode (Kill Switch)
    ledger_file = data_dir / "evolution_ledger.jsonl"
    if ledger_file.exists():
        try:
            # We add a safe_mode_exit event
            import time
            from unified_core.evolution.ledger import EvolutionLedger
            ledger = EvolutionLedger()
            if ledger.safe_mode:
                ledger.exit_safe_mode(reason="Manual reset post testing")
                print("✅ Exited Safe Mode (Kill Switch deactivated).")
            else:
                print("✅ Ledger is already out of safe mode.")
        except Exception as e:
            print(f"❌ Failed to exit safe mode: {e}")

    # 3. Heal NeuronFabric (Strengthen recently weakened test neurons)
    try:
        from unified_core.evolution.neuron_learning import get_neuron_learning_bridge
        from unified_core.core.neuron_fabric import get_neuron_fabric
        
        fabric = get_neuron_fabric()
        
        # We can simulate a promotion for the failed tests to restore their weights
        found_test_neurons = 0
        for neuron_id, neuron in fabric._neurons.items():
            if "EVO-TEST" in neuron.metadata.get("proposal_id", "") or "B-Tree" in neuron.proposition:
                # Add back the strength that was penalized
                neuron.reinforce(amount=0.15)
                found_test_neurons += 1
                
        if found_test_neurons > 0:
            fabric._save_fabric()
            print(f"✅ Restored strength to {found_test_neurons} test-related neurons.")
        else:
            print("✅ Neurons seem healthy. No test neurons needed repairing.")
            
    except Exception as e:
        print(f"❌ Could not repair Neurons: {e}")
        
    print("\n🚀 Repair complete! The system is clean and ready for real operation.")

if __name__ == "__main__":
    repair_system()
