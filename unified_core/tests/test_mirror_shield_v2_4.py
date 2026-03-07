import sys
import os
import asyncio
from pathlib import Path

# Add src to path
sys.path.append("/home/noogh/projects/noogh_unified_system/src")

from unified_core.mirror_shield import MirrorShield

async def verify_hardening():
    print("🛡️ Starting Mirror Shield v2.4.2 Verification...")
    shield = MirrorShield()
    
    # 1. Check Connectivity & Space
    status = shield.get_status()
    print(f"Connection Status: {status}")
    
    # 2. Execute Sync
    result = await shield.execute_mirror_sync()
    print(f"Sync Result: {result.get('success')}")
    print(f"Sync Details: {result.get('details')}")
    
    if not result.get('success'):
        print(f"FAIL: Sync failed with error: {result.get('error')}")
        sys.exit(1)
        
    # Determine which tier was used from sync details
    # e.g. "L4_DEEP_SLEEP db updated."
    active_tier = None
    for detail in result.get('details', []):
        if "db updated" in detail:
            active_tier = detail.split(' ')[0]
            break
            
    if active_tier:
        print(f"🔍 Active Tier Detected: {active_tier}")
        target_path = Path(shield.targets[active_tier])
        
        # Verify Files on active tier
        expected_files = ["shared_memory.sqlite.bak", "evolution_ledger.jsonl.bak"]
        for f in expected_files:
            if (target_path / f).exists():
                print(f"✅ Verified {f} on {active_tier}")
            else:
                print(f"❌ Missing {f} on {active_tier}")
    else:
        print("❌ Could not determine active tier from results.")

    # 3. Verify Survival Pulse (L4 Heartbeat or L4 as Target)
    l4_path = Path(shield.targets["L4_DEEP_SLEEP"])
    marker = l4_path / "survival.heartbeat"
    db_marker = l4_path / "shared_memory.sqlite.bak"
    
    if marker.exists() or db_marker.exists():
        print("✅ Verified Survival Signal on L4 (Deep Sleep)")
    else:
        print("❌ Missing Survival Signal on L4")

if __name__ == "__main__":
    asyncio.run(verify_hardening())
