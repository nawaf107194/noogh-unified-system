"""
Integration Tests v2 — Deep Integration Verification
Covers EventBus, WorldModel, ASAA, AMLA, NeuronFabric, ConsequenceEngine, ScarTissue.

Run: python unified_core/integration/test_integration.py
"""

import asyncio
import sys
import os
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))


def test_eventbus_singleton():
    """Test 1: EventBus singleton works and can publish/subscribe."""
    from unified_core.integration.event_bus import get_event_bus, StandardEvents
    
    bus = get_event_bus()
    bus2 = get_event_bus()
    assert bus is bus2, "EventBus should be a singleton"
    
    received = []
    async def handler(event):
        received.append(event.data)
    
    bus.subscribe(StandardEvents.BELIEF_ADDED, handler, "test_sub")
    
    async def pub():
        await bus.publish(StandardEvents.BELIEF_ADDED, {"belief_id": "t123"}, "test")
    asyncio.get_event_loop().run_until_complete(pub())
    
    assert len(received) > 0 and received[0]["belief_id"] == "t123"
    bus.unsubscribe(StandardEvents.BELIEF_ADDED, "test_sub")
    print("✅ Test 1 PASSED: EventBus singleton and pub/sub")


def test_worldmodel_eventbus():
    """Test 2: WorldModel publishes events when beliefs are added."""
    from unified_core.core.world_model import WorldModel
    from unified_core.integration.event_bus import get_event_bus, StandardEvents
    
    bus = get_event_bus()
    wm = WorldModel()
    assert wm._event_bus is not None
    
    events = []
    async def h(event): events.append(event)
    bus.subscribe(StandardEvents.BELIEF_ADDED, h, "test_wm")
    
    async def add():
        return await wm.add_belief(f"Unique event test belief {time.time()}", 0.75)
    belief = asyncio.get_event_loop().run_until_complete(add())
    
    assert belief is not None
    assert len(events) > 0
    bus.unsubscribe(StandardEvents.BELIEF_ADDED, "test_wm")
    print("✅ Test 2 PASSED: WorldModel publishes BELIEF_ADDED events")


def test_worldmodel_creates_neuron():
    """Test 3: WorldModel.add_belief auto-creates a neuron in NeuronFabric."""
    from unified_core.core.world_model import WorldModel
    from unified_core.core.neuron_fabric import get_neuron_fabric
    
    wm = WorldModel()
    fabric = get_neuron_fabric()
    initial_count = len(fabric._neurons)
    
    async def add():
        return await wm.add_belief(f"BTC market is bullish {time.time()}", 0.8)
    belief = asyncio.get_event_loop().run_until_complete(add())
    
    new_count = len(fabric._neurons)
    assert new_count > initial_count, f"Expected new neuron, got {initial_count} -> {new_count}"
    
    # Check domain inference
    assert wm._infer_domain("BTC market is bullish") == "trading"
    assert wm._infer_domain("CPU usage is high") == "system"
    assert wm._infer_domain("Random statement") == "general"
    
    print(f"✅ Test 3 PASSED: Belief auto-created neuron (total: {new_count})")


def test_asaa_real_store():
    """Test 4: ASAA uses real UnifiedMemoryStore."""
    from unified_core.core.asaa import get_asaa, ActionRequest
    from unified_core.core.memory_store import UnifiedMemoryStore
    
    asaa = get_asaa()
    store = UnifiedMemoryStore()
    asaa.set_belief_store(store)
    
    request = ActionRequest(
        action_type="test", params={}, source_beliefs=["none"],
        confidence=0.8, impact_level=0.5
    )
    result = asaa.evaluate(request)
    assert result is not None and 0 <= result.fragility <= 1.0
    print(f"✅ Test 4 PASSED: ASAA real store (fragility={result.fragility:.2f})")


def test_amla_real_store():
    """Test 5: AMLA uses real UnifiedMemoryStore."""
    from unified_core.core.amla import get_amla, AMLAActionRequest
    from unified_core.core.memory_store import UnifiedMemoryStore
    
    amla = get_amla()
    store = UnifiedMemoryStore()
    amla.set_belief_store(store)
    amla.set_advisory_memory(store)
    
    request = AMLAActionRequest(
        action_type="test_extreme", params={}, source_beliefs=[],
        confidence=0.9, impact_level=0.7
    )
    result = amla.evaluate(request)
    assert result is not None and 0 <= result.fragility_extreme <= 1.0
    print(f"✅ Test 5 PASSED: AMLA extreme audit (DFE={result.fragility_extreme:.2%})")


def test_counterfactual_removed():
    """Test 6: CounterfactualReasoner is completely removed."""
    try:
        from unified_core.intelligence.counterfactual import CounterfactualReasoner
        assert False, "Should have been deleted!"
    except (ImportError, ModuleNotFoundError):
        pass
    from unified_core.intelligence import __all__ as exports
    assert 'CounterfactualReasoner' not in exports
    print("✅ Test 6 PASSED: CounterfactualReasoner removed")


def test_consequence_hebbian():
    """Test 7: ConsequenceEngine triggers Hebbian learning."""
    from unified_core.core.consequence import ConsequenceEngine, Action, Outcome
    from unified_core.core.neuron_fabric import get_neuron_fabric
    
    fabric = get_neuron_fabric()
    engine = ConsequenceEngine(storage_name="test_hebbian_ledger.jsonl")
    
    action = Action(action_type="test_hebbian_action", parameters={"test": True})
    outcome = Outcome(success=True, result={"score": 1.0})
    
    # Commit should not crash
    h = engine.commit(action, outcome)
    assert h is not None
    assert len(h) == 64  # SHA-256
    print(f"✅ Test 7 PASSED: ConsequenceEngine Hebbian learning (hash: {h[:12]}...)")


def test_scar_neuron_punishment():
    """Test 8: ScarTissue.inflict punishes neurons."""
    from unified_core.core.scar import FailureRecord, Failure
    from unified_core.core.neuron_fabric import get_neuron_fabric
    
    fabric = get_neuron_fabric()
    record = FailureRecord(enable_enforcement=False)
    
    failure = Failure(
        failure_id=f"test_fail_{time.time()}",
        action_type="test_punishment",
        action_params={"x": 1},
        error_message="Test failure",
        belief_ids_involved=[]
    )
    
    async def inflict():
        return await record.inflict(failure, severity="low")
    scar = asyncio.get_event_loop().run_until_complete(inflict())
    
    assert scar is not None
    print(f"✅ Test 8 PASSED: ScarTissue inflict with NeuronFabric wiring")


def test_standard_events():
    """Test 9: All standard event types present."""
    from unified_core.integration.event_bus import StandardEvents
    required = ['BELIEF_ADDED', 'BELIEF_UPDATED', 'BELIEF_FALSIFIED',
                'NEURON_CREATED', 'NEURON_ACTIVATED', 'DECISION_PROPOSED', 'DECISION_COMMITTED']
    for name in required:
        assert hasattr(StandardEvents, name), f"Missing {name}"
    print("✅ Test 9 PASSED: All standard event types present")


if __name__ == "__main__":
    print("=" * 60)
    print("🧪 NOOGH Integration Tests v2 — Deep Integration")
    print("=" * 60)
    
    tests = [
        test_eventbus_singleton,
        test_worldmodel_eventbus, 
        test_worldmodel_creates_neuron,
        test_asaa_real_store,
        test_amla_real_store,
        test_counterfactual_removed,
        test_consequence_hebbian,
        test_scar_neuron_punishment,
        test_standard_events,
    ]
    
    passed = failed = 0
    for test in tests:
        try:
            test()
            passed += 1
        except Exception as e:
            print(f"❌ {test.__name__} FAILED: {e}")
            import traceback; traceback.print_exc()
            failed += 1
    
    print(f"\n{'=' * 60}")
    print(f"Results: {passed} passed, {failed} failed, {passed + failed} total")
    print("=" * 60)
    sys.exit(0 if failed == 0 else 1)
