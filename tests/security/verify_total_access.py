import asyncio
import os
import sys
from unified_core.core.actuators import get_actuator_hub
from unified_core.core.amla_enforcer import AMLAEnforcer

async def verify_total_access():
    print("🔓 STARTING TOTAL ACCESS VERIFICATION...")
    hub = get_actuator_hub()
    enforcer = AMLAEnforcer(strict_mode=False)
    
    # 1. Test Root Filesystem Read
    print("\n📂 Testing Root Filesystem Access (/etc/hostname)...")
    try:
        # We simulate an auth context for scope requirements
        class MockAuth:
            def require_scope(self, scope): pass
            def has_scope(self, scope): return True

        auth = MockAuth()
        action = await hub.filesystem.read_file("/etc/hostname", auth)
        if action.result.value == "success":
            print(f"✅ Root Read Success: {action.result_data['content'].strip()}")
        else:
            print(f"❌ Root Read Failed/Blocked: {action.result} - {action.result_data.get('error')}")
    except Exception as e:
        print(f"❌ Root Read Exception: {e}")

    # 2. Test System Command (systemctl)
    print("\n⚙️ Testing System Command (systemctl --version)...")
    try:
        action = await hub.process.spawn(["systemctl", "--version"], auth)
        if action.result.value == "success":
            print(f"✅ Systemctl Exec Success: {action.result_data['stdout'].splitlines()[0]}")
        else:
            print(f"❌ Systemctl Exec Blocked/Failed: {action.result} - {action.result_data.get('error')}")
    except Exception as e:
        print(f"❌ Systemctl Exec Exception: {e}")

    # 3. Test AMLA Friction (Should be low)
    print("\n🧠 Testing AMLA Friction & Sovereignty...")
    from unified_core.core.amla import AdversarialMilitaryAuditAgent, AMLAActionRequest
    amla = AdversarialMilitaryAuditAgent()
    
    # High impact action that previously would have 30s delay
    req = AMLAActionRequest(
        action_type="system_update",
        params={"package": "security-core"},
        source_beliefs=["belief_1"],
        confidence=0.9,
        impact_level=0.9
    )
    
    start_time = asyncio.get_event_loop().time()
    audit = amla.evaluate(req, beliefs=[])
    end_time = asyncio.get_event_loop().time()
    
    print(f"✅ AMLA Verdict: {audit.verdict.value}")
    print(f"✅ Friction Delay: {audit.friction_delay_seconds}s")
    print(f"✅ Audit took: {end_time - start_time:.4f}s")
    
    if audit.friction_delay_seconds <= 5.0:
        print("✅ Friction within Sovereign limits.")
    else:
        print(f"❌ Friction too high: {audit.friction_delay_seconds}s")

if __name__ == "__main__":
    # Ensure src is in path
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
    asyncio.run(verify_total_access())
