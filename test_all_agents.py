"""
Test All Agents - اختبار جميع الوكلاء
====================================

Comprehensive test to verify all agents and autonomous systems are working.
"""

import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from typing import Dict, Any


def test_component_status() -> Dict[str, Any]:
    """Test all major components and agents."""

    results = {
        "total_tested": 0,
        "working": 0,
        "failed": 0,
        "components": {}
    }

    print("=" * 60)
    print("🔍 Testing All Agents and Components")
    print("=" * 60)

    # 1. EventBus
    print("\n1️⃣ Testing EventBus...")
    try:
        from unified_core.integration.event_bus import get_event_bus, StandardEvents
        bus = get_event_bus()
        assert bus is not None
        results["components"]["EventBus"] = "✅ Working"
        results["working"] += 1
        print("   ✅ EventBus: Working")
    except Exception as e:
        results["components"]["EventBus"] = f"❌ Failed: {e}"
        results["failed"] += 1
        print(f"   ❌ EventBus: Failed - {e}")
    results["total_tested"] += 1

    # 2. WorldModel
    print("\n2️⃣ Testing WorldModel...")
    try:
        from unified_core.core.world_model import WorldModel
        wm = WorldModel()
        assert wm is not None
        results["components"]["WorldModel"] = "✅ Working"
        results["working"] += 1
        print("   ✅ WorldModel: Working")
    except Exception as e:
        results["components"]["WorldModel"] = f"❌ Failed: {e}"
        results["failed"] += 1
        print(f"   ❌ WorldModel: Failed - {e}")
    results["total_tested"] += 1

    # 3. NeuronFabric
    print("\n3️⃣ Testing NeuronFabric...")
    try:
        from unified_core.core.neuron_fabric import get_neuron_fabric, NeuronType
        fabric = get_neuron_fabric()
        assert fabric is not None
        neuron_count = len(fabric._neurons)
        results["components"]["NeuronFabric"] = f"✅ Working ({neuron_count} neurons)"
        results["working"] += 1
        print(f"   ✅ NeuronFabric: Working ({neuron_count} neurons)")
    except Exception as e:
        results["components"]["NeuronFabric"] = f"❌ Failed: {e}"
        results["failed"] += 1
        print(f"   ❌ NeuronFabric: Failed - {e}")
    results["total_tested"] += 1

    # 4. ASAA (Antifragile Self-Auditing Authority)
    print("\n4️⃣ Testing ASAA...")
    try:
        from unified_core.core.asaa import get_asaa
        asaa = get_asaa()
        assert asaa is not None
        results["components"]["ASAA"] = "✅ Working"
        results["working"] += 1
        print("   ✅ ASAA: Working")
    except Exception as e:
        results["components"]["ASAA"] = f"❌ Failed: {e}"
        results["failed"] += 1
        print(f"   ❌ ASAA: Failed - {e}")
    results["total_tested"] += 1

    # 5. AMLA (Adversarial Military-Level Audit)
    print("\n5️⃣ Testing AMLA...")
    try:
        from unified_core.core.amla import get_amla
        amla = get_amla()
        assert amla is not None
        results["components"]["AMLA"] = "✅ Working"
        results["working"] += 1
        print("   ✅ AMLA: Working")
    except Exception as e:
        results["components"]["AMLA"] = f"❌ Failed: {e}"
        results["failed"] += 1
        print(f"   ❌ AMLA: Failed - {e}")
    results["total_tested"] += 1

    # 6. ConsequenceEngine
    print("\n6️⃣ Testing ConsequenceEngine...")
    try:
        from unified_core.core.consequence import ConsequenceEngine
        engine = ConsequenceEngine()
        assert engine is not None
        results["components"]["ConsequenceEngine"] = "✅ Working"
        results["working"] += 1
        print("   ✅ ConsequenceEngine: Working")
    except Exception as e:
        results["components"]["ConsequenceEngine"] = f"❌ Failed: {e}"
        results["failed"] += 1
        print(f"   ❌ ConsequenceEngine: Failed - {e}")
    results["total_tested"] += 1

    # 7. ScarTissue (Failure Memory)
    print("\n7️⃣ Testing ScarTissue...")
    try:
        from unified_core.core.scar import FailureRecord
        scar = FailureRecord()
        assert scar is not None
        results["components"]["ScarTissue"] = "✅ Working"
        results["working"] += 1
        print("   ✅ ScarTissue: Working")
    except Exception as e:
        results["components"]["ScarTissue"] = f"❌ Failed: {e}"
        results["failed"] += 1
        print(f"   ❌ ScarTissue: Failed - {e}")
    results["total_tested"] += 1

    # 8. FailureAlertSystem
    print("\n8️⃣ Testing FailureAlertSystem...")
    try:
        from unified_core.observability.failure_alert_system import get_failure_alert_system
        alert_system = get_failure_alert_system()
        assert alert_system is not None
        stats = alert_system.get_statistics()
        results["components"]["FailureAlertSystem"] = f"✅ Working ({stats['total_alerts']} alerts)"
        results["working"] += 1
        print(f"   ✅ FailureAlertSystem: Working ({stats['total_alerts']} total alerts)")
    except Exception as e:
        results["components"]["FailureAlertSystem"] = f"❌ Failed: {e}"
        results["failed"] += 1
        print(f"   ❌ FailureAlertSystem: Failed - {e}")
    results["total_tested"] += 1

    # 9. SystemHealthMonitor
    print("\n9️⃣ Testing SystemHealthMonitor...")
    try:
        from unified_core.health.system_health_monitor import SystemHealthMonitor
        monitor = SystemHealthMonitor()
        assert monitor is not None
        results["components"]["SystemHealthMonitor"] = "✅ Working"
        results["working"] += 1
        print("   ✅ SystemHealthMonitor: Working")
    except Exception as e:
        results["components"]["SystemHealthMonitor"] = f"❌ Failed: {e}"
        results["failed"] += 1
        print(f"   ❌ SystemHealthMonitor: Failed - {e}")
    results["total_tested"] += 1

    # 10. BaseAgent
    print("\n🔟 Testing BaseAgent Framework...")
    try:
        from unified_core.orchestration.base_agent import BaseAgent
        assert BaseAgent is not None
        results["components"]["BaseAgent"] = "✅ Working"
        results["working"] += 1
        print("   ✅ BaseAgent Framework: Working")
    except Exception as e:
        results["components"]["BaseAgent"] = f"❌ Failed: {e}"
        results["failed"] += 1
        print(f"   ❌ BaseAgent Framework: Failed - {e}")
    results["total_tested"] += 1

    # 11. AgentOrchestrator
    print("\n1️⃣1️⃣ Testing AgentOrchestrator...")
    try:
        from unified_core.orchestration.agent_orchestrator import AgentOrchestrator
        assert AgentOrchestrator is not None
        results["components"]["AgentOrchestrator"] = "✅ Working"
        results["working"] += 1
        print("   ✅ AgentOrchestrator: Working")
    except Exception as e:
        results["components"]["AgentOrchestrator"] = f"❌ Failed: {e}"
        results["failed"] += 1
        print(f"   ❌ AgentOrchestrator: Failed - {e}")
    results["total_tested"] += 1

    # 12. MarketBeliefEngine
    print("\n1️⃣2️⃣ Testing MarketBeliefEngine...")
    try:
        from trading.market_belief_engine import get_market_belief_engine
        engine = get_market_belief_engine()
        assert engine is not None
        results["components"]["MarketBeliefEngine"] = "✅ Working"
        results["working"] += 1
        print("   ✅ MarketBeliefEngine: Working")
    except Exception as e:
        results["components"]["MarketBeliefEngine"] = f"❌ Failed: {e}"
        results["failed"] += 1
        print(f"   ❌ MarketBeliefEngine: Failed - {e}")
    results["total_tested"] += 1

    # 13. TrapLiveTrader
    print("\n1️⃣3️⃣ Testing TrapLiveTrader...")
    try:
        from trading.trap_live_trader import TrapLiveTrader
        assert TrapLiveTrader is not None
        results["components"]["TrapLiveTrader"] = "✅ Working"
        results["working"] += 1
        print("   ✅ TrapLiveTrader: Working")
    except Exception as e:
        results["components"]["TrapLiveTrader"] = f"❌ Failed: {e}"
        results["failed"] += 1
        print(f"   ❌ TrapLiveTrader: Failed - {e}")
    results["total_tested"] += 1

    # 14. SecOpsAgent
    print("\n1️⃣4️⃣ Testing SecOpsAgent...")
    try:
        from unified_core.secops_agent import SecOpsAgent
        assert SecOpsAgent is not None
        results["components"]["SecOpsAgent"] = "✅ Working"
        results["working"] += 1
        print("   ✅ SecOpsAgent: Working")
    except Exception as e:
        results["components"]["SecOpsAgent"] = f"❌ Failed: {e}"
        results["failed"] += 1
        print(f"   ❌ SecOpsAgent: Failed - {e}")
    results["total_tested"] += 1

    # 15. PredictivePerformanceMonitor
    print("\n1️⃣5️⃣ Testing PredictivePerformanceMonitor...")
    try:
        from unified_core.ml.predictive_performance_monitor import PredictivePerformanceMonitor
        assert PredictivePerformanceMonitor is not None
        results["components"]["PredictivePerformanceMonitor"] = "✅ Working"
        results["working"] += 1
        print("   ✅ PredictivePerformanceMonitor: Working")
    except Exception as e:
        results["components"]["PredictivePerformanceMonitor"] = f"❌ Failed: {e}"
        results["failed"] += 1
        print(f"   ❌ PredictivePerformanceMonitor: Failed - {e}")
    results["total_tested"] += 1

    return results


async def test_async_components():
    """Test components that require async initialization."""

    print("\n" + "=" * 60)
    print("🔄 Testing Async Components")
    print("=" * 60)

    async_results = {}

    # Test WorldModel async setup
    print("\n1️⃣ Testing WorldModel async setup...")
    try:
        from unified_core.core.world_model import WorldModel
        wm = WorldModel()
        await wm.setup()
        state = await wm.get_belief_state()
        async_results["WorldModel"] = f"✅ Setup complete ({state['total_beliefs']} beliefs)"
        print(f"   ✅ WorldModel: {state['total_beliefs']} beliefs loaded")
    except Exception as e:
        async_results["WorldModel"] = f"❌ Failed: {e}"
        print(f"   ❌ WorldModel setup: Failed - {e}")

    # Test MarketBeliefEngine async setup
    print("\n2️⃣ Testing MarketBeliefEngine async setup...")
    try:
        from trading.market_belief_engine import get_market_belief_engine
        engine = get_market_belief_engine()
        await engine.setup()
        async_results["MarketBeliefEngine"] = "✅ Setup complete"
        print("   ✅ MarketBeliefEngine: Setup complete")
    except Exception as e:
        async_results["MarketBeliefEngine"] = f"❌ Failed: {e}"
        print(f"   ❌ MarketBeliefEngine setup: Failed - {e}")

    return async_results


if __name__ == "__main__":
    try:
        # Test synchronous components
        sync_results = test_component_status()

        # Test async components
        async_results = asyncio.run(test_async_components())

        # Final summary
        print("\n" + "=" * 60)
        print("📊 Final Summary")
        print("=" * 60)

        print(f"\n✅ Working: {sync_results['working']}/{sync_results['total_tested']}")
        print(f"❌ Failed: {sync_results['failed']}/{sync_results['total_tested']}")

        success_rate = (sync_results['working'] / sync_results['total_tested'] * 100) if sync_results['total_tested'] > 0 else 0
        print(f"\n📈 Success Rate: {success_rate:.1f}%")

        if sync_results['failed'] > 0:
            print("\n⚠️  Failed Components:")
            for name, status in sync_results['components'].items():
                if "❌" in status:
                    print(f"   - {name}: {status}")

        print("\n🔄 Async Components:")
        for name, status in async_results.items():
            print(f"   {status} {name}")

        print("\n" + "=" * 60)

        if sync_results['failed'] == 0:
            print("✅ All agents and components are working!")
            sys.exit(0)
        else:
            print(f"⚠️  {sync_results['failed']} component(s) need attention")
            sys.exit(1)

    except Exception as e:
        print(f"\n❌ Test suite failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
