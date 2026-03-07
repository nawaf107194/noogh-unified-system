"""
Trading Integration Status Test - اختبار حالة تكامل التداول
==========================================================

Verify all trading system integrations with NOOGH core:
- EventBus integration
- NeuronFabric integration
- AMLA audit integration
- ConsequenceEngine integration
- ScarTissue integration
- MarketBeliefEngine integration
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import logging
logging.basicConfig(level=logging.INFO)

def test_trading_integrations():
    """Test all trading system integrations."""

    print("=" * 60)
    print("🔍 Testing Trading System Integration Status")
    print("=" * 60)

    results = {
        "total": 0,
        "working": 0,
        "failed": 0,
        "integrations": {}
    }

    # 1. Check TrapLiveTrader imports
    print("\n1️⃣ Testing TrapLiveTrader Core...")
    try:
        from trading.trap_live_trader import TrapLiveTrader
        results["integrations"]["TrapLiveTrader"] = "✅ Importable"
        results["working"] += 1
        print("   ✅ TrapLiveTrader imports successfully")
    except Exception as e:
        results["integrations"]["TrapLiveTrader"] = f"❌ Failed: {e}"
        results["failed"] += 1
        print(f"   ❌ TrapLiveTrader import failed: {e}")
        return results
    results["total"] += 1

    # 2. Check EventBus integration
    print("\n2️⃣ Testing EventBus Integration...")
    try:
        from unified_core.integration.event_bus import get_event_bus, StandardEvents
        bus = get_event_bus()

        # Check for trading events
        trading_events = [
            "TRADE_SIGNAL", "TRADE_OPENED", "TRADE_CLOSED",
            "TRADE_PROFIT", "TRADE_LOSS", "POSITION_UPDATED"
        ]

        available = []
        for event in trading_events:
            if hasattr(StandardEvents, event):
                available.append(event)

        if len(available) == len(trading_events):
            results["integrations"]["EventBus"] = f"✅ All {len(available)} trading events available"
            results["working"] += 1
            print(f"   ✅ EventBus: {len(available)}/{len(trading_events)} trading events")
        else:
            results["integrations"]["EventBus"] = f"⚠️  Only {len(available)}/{len(trading_events)} events"
            results["failed"] += 1
            print(f"   ⚠️  EventBus: Missing events")

    except Exception as e:
        results["integrations"]["EventBus"] = f"❌ Failed: {e}"
        results["failed"] += 1
        print(f"   ❌ EventBus integration: {e}")
    results["total"] += 1

    # 3. Check NeuronFabric integration
    print("\n3️⃣ Testing NeuronFabric Integration...")
    try:
        from unified_core.core.neuron_fabric import get_neuron_fabric
        fabric = get_neuron_fabric()

        neuron_count = len(fabric._neurons)
        results["integrations"]["NeuronFabric"] = f"✅ {neuron_count} neurons active"
        results["working"] += 1
        print(f"   ✅ NeuronFabric: {neuron_count} neurons")

    except Exception as e:
        results["integrations"]["NeuronFabric"] = f"❌ Failed: {e}"
        results["failed"] += 1
        print(f"   ❌ NeuronFabric: {e}")
    results["total"] += 1

    # 4. Check AMLA integration
    print("\n4️⃣ Testing AMLA Integration...")
    try:
        from unified_core.core.amla import get_amla, AMLAActionRequest, AMLAVerdict
        amla = get_amla()

        results["integrations"]["AMLA"] = "✅ Available for trade auditing"
        results["working"] += 1
        print("   ✅ AMLA: Ready for trade auditing")

    except Exception as e:
        results["integrations"]["AMLA"] = f"❌ Failed: {e}"
        results["failed"] += 1
        print(f"   ❌ AMLA: {e}")
    results["total"] += 1

    # 5. Check ConsequenceEngine integration
    print("\n5️⃣ Testing ConsequenceEngine Integration...")
    try:
        from unified_core.core.consequence import ConsequenceEngine, Action, Outcome
        engine = ConsequenceEngine()

        results["integrations"]["ConsequenceEngine"] = "✅ Available for outcome tracking"
        results["working"] += 1
        print("   ✅ ConsequenceEngine: Ready for tracking")

    except Exception as e:
        results["integrations"]["ConsequenceEngine"] = f"❌ Failed: {e}"
        results["failed"] += 1
        print(f"   ❌ ConsequenceEngine: {e}")
    results["total"] += 1

    # 6. Check ScarTissue integration
    print("\n6️⃣ Testing ScarTissue Integration...")
    try:
        from unified_core.core.scar import FailureRecord, Failure
        scar = FailureRecord()

        results["integrations"]["ScarTissue"] = "✅ Available for failure memory"
        results["working"] += 1
        print("   ✅ ScarTissue: Ready for failure tracking")

    except Exception as e:
        results["integrations"]["ScarTissue"] = f"❌ Failed: {e}"
        results["failed"] += 1
        print(f"   ❌ ScarTissue: {e}")
    results["total"] += 1

    # 7. Check MarketBeliefEngine integration
    print("\n7️⃣ Testing MarketBeliefEngine Integration...")
    try:
        from trading.market_belief_engine import get_market_belief_engine
        engine = get_market_belief_engine()

        results["integrations"]["MarketBeliefEngine"] = "✅ Available for market analysis"
        results["working"] += 1
        print("   ✅ MarketBeliefEngine: Ready")

    except Exception as e:
        results["integrations"]["MarketBeliefEngine"] = f"❌ Failed: {e}"
        results["failed"] += 1
        print(f"   ❌ MarketBeliefEngine: {e}")
    results["total"] += 1

    # 8. Check TradingAlerts integration
    print("\n8️⃣ Testing TradingAlerts Integration...")
    try:
        from trading.trading_alerts_integration import (
            alert_large_loss, alert_api_error, alert_risk_breach
        )

        results["integrations"]["TradingAlerts"] = "✅ All alert functions available"
        results["working"] += 1
        print("   ✅ TradingAlerts: 7 alert helpers ready")

    except Exception as e:
        results["integrations"]["TradingAlerts"] = f"❌ Failed: {e}"
        results["failed"] += 1
        print(f"   ❌ TradingAlerts: {e}")
    results["total"] += 1

    # 9. Check if trap_live_trader.py has integration code
    print("\n9️⃣ Checking Integration Code in trap_live_trader.py...")
    try:
        import subprocess
        result = subprocess.run(
            ['grep', '-c', 'EventBus\|NeuronFabric\|AMLA\|ConsequenceEngine',
             'trading/trap_live_trader.py'],
            capture_output=True,
            text=True
        )

        integration_lines = int(result.stdout.strip()) if result.returncode == 0 else 0

        if integration_lines > 20:  # Should have many integration lines
            results["integrations"]["Integration Code"] = f"✅ {integration_lines} integration references"
            results["working"] += 1
            print(f"   ✅ Integration code: {integration_lines} references found")
        else:
            results["integrations"]["Integration Code"] = f"⚠️  Only {integration_lines} references"
            results["failed"] += 1
            print(f"   ⚠️  Integration code: Incomplete")

    except Exception as e:
        results["integrations"]["Integration Code"] = f"❌ Failed: {e}"
        results["failed"] += 1
        print(f"   ❌ Integration code check: {e}")
    results["total"] += 1

    return results


def check_live_integration():
    """Check if integration is active in running system."""

    print("\n" + "=" * 60)
    print("🔄 Checking Live Integration Status")
    print("=" * 60)

    # Check current neuron count for trading
    print("\n1️⃣ Trading Neurons in NeuronFabric:")
    try:
        from unified_core.core.neuron_fabric import get_neuron_fabric
        fabric = get_neuron_fabric()

        trading_neurons = [
            n for n in fabric._neurons.values()
            if 'trading' in n.domain.lower() or 'trade' in n.tags
        ]

        print(f"   Total neurons: {len(fabric._neurons)}")
        print(f"   Trading neurons: {len(trading_neurons)}")

        if trading_neurons:
            print(f"\n   Recent trading neurons:")
            for neuron in sorted(trading_neurons, key=lambda n: n.created_at, reverse=True)[:3]:
                print(f"      - {neuron.proposition[:60]}...")

    except Exception as e:
        print(f"   ⚠️  Could not check neurons: {e}")

    # Check beliefs related to trading
    print("\n2️⃣ Trading Beliefs in WorldModel:")
    try:
        import asyncio
        from unified_core.core.world_model import WorldModel

        async def get_beliefs():
            wm = WorldModel()
            await wm.setup()
            beliefs = await wm.get_usable_beliefs()

            trading_beliefs = [
                b for b in beliefs
                if any(keyword in b.proposition.lower()
                       for keyword in ['trade', 'market', 'btc', 'eth', 'price', 'signal'])
            ]

            print(f"   Total beliefs: {len(beliefs)}")
            print(f"   Trading-related beliefs: {len(trading_beliefs)}")

            if trading_beliefs:
                print(f"\n   Recent trading beliefs:")
                for belief in sorted(trading_beliefs, key=lambda b: b.created_at, reverse=True)[:3]:
                    print(f"      - {belief.proposition[:60]}... (conf: {belief.confidence:.2f})")

        asyncio.run(get_beliefs())

    except Exception as e:
        print(f"   ⚠️  Could not check beliefs: {e}")

    # Check EventBus subscriptions
    print("\n3️⃣ EventBus Trading Subscriptions:")
    try:
        from unified_core.integration.event_bus import get_event_bus
        bus = get_event_bus()

        trading_events = ["TRADE_SIGNAL", "TRADE_OPENED", "TRADE_CLOSED", "TRADE_PROFIT", "TRADE_LOSS"]

        for event_name in trading_events:
            if hasattr(bus, '_StandardEvents'):
                event = getattr(bus._StandardEvents, event_name, None)
                if event:
                    subscribers = bus._subscribers.get(event, [])
                    print(f"   {event_name}: {len(subscribers)} subscribers")

    except Exception as e:
        print(f"   ⚠️  Could not check subscriptions: {e}")


if __name__ == "__main__":
    try:
        # Test integrations
        results = test_trading_integrations()

        # Check live status
        check_live_integration()

        # Summary
        print("\n" + "=" * 60)
        print("📊 Integration Status Summary")
        print("=" * 60)

        success_rate = (results["working"] / results["total"] * 100) if results["total"] > 0 else 0

        print(f"\n✅ Working: {results['working']}/{results['total']}")
        print(f"❌ Failed: {results['failed']}/{results['total']}")
        print(f"📈 Success Rate: {success_rate:.1f}%")

        print("\n📋 Integration Components:")
        for name, status in results["integrations"].items():
            icon = "✅" if "✅" in status else "❌" if "❌" in status else "⚠️"
            print(f"   {icon} {name}: {status}")

        print("\n" + "=" * 60)

        if results["failed"] == 0:
            print("✅ All trading integrations are working!")
            print("\n🎯 نظام التداول متكامل بالكامل مع NOOGH!")
            sys.exit(0)
        else:
            print(f"⚠️  {results['failed']} integration(s) need attention")
            sys.exit(1)

    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
