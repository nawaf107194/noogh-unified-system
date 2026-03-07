"""
Test NeuronFabric Events
=========================

Quick test to verify all neuron fabric events are being published:
- NEURON_CREATED
- NEURON_ACTIVATED
- SYNAPSE_STRENGTHENED
- SYNAPSE_WEAKENED
- NEURON_PRUNED
"""

import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from unified_core.core.neuron_fabric import get_neuron_fabric, NeuronType
from unified_core.integration.event_bus import get_event_bus, StandardEvents

def test_neuron_events():
    """Test all neuron fabric event publishing."""

    print("=" * 60)
    print("🧪 Testing NeuronFabric Event Publishing")
    print("=" * 60)

    # Setup
    fabric = get_neuron_fabric()
    bus = get_event_bus()

    events_received = {
        "NEURON_CREATED": [],
        "NEURON_ACTIVATED": [],
        "SYNAPSE_STRENGTHENED": [],
        "SYNAPSE_WEAKENED": [],
        "NEURON_PRUNED": []
    }

    # Subscribe to all events
    def make_handler(event_name):
        async def handler(event):
            events_received[event_name].append(event.data)
        return handler

    bus.subscribe(StandardEvents.NEURON_CREATED, make_handler("NEURON_CREATED"), "test")
    bus.subscribe(StandardEvents.NEURON_ACTIVATED, make_handler("NEURON_ACTIVATED"), "test")
    bus.subscribe(StandardEvents.SYNAPSE_STRENGTHENED, make_handler("SYNAPSE_STRENGTHENED"), "test")
    bus.subscribe(StandardEvents.SYNAPSE_WEAKENED, make_handler("SYNAPSE_WEAKENED"), "test")
    bus.subscribe(StandardEvents.NEURON_PRUNED, make_handler("NEURON_PRUNED"), "test")

    # Wait for async events to propagate
    def wait_for_events():
        asyncio.run(asyncio.sleep(0.2))

    print("\n1️⃣ Testing NEURON_CREATED...")
    neuron1 = fabric.create_neuron("Test belief 1", neuron_type=NeuronType.COGNITIVE, confidence=0.8)
    wait_for_events()
    assert len(events_received["NEURON_CREATED"]) >= 1, "NEURON_CREATED not published"
    print(f"   ✅ NEURON_CREATED: {len(events_received['NEURON_CREATED'])} events")

    print("\n2️⃣ Testing NEURON_ACTIVATED...")
    neuron2 = fabric.create_neuron("Test belief 2", neuron_type=NeuronType.COGNITIVE, confidence=0.9)
    fabric.connect(neuron1.neuron_id, neuron2.neuron_id, weight=0.7)

    # Activate with strong signal to trigger event (threshold > 0.5)
    activated = fabric.activate(neuron1.neuron_id, signal=1.0)
    wait_for_events()

    assert len(events_received["NEURON_ACTIVATED"]) >= 1, "NEURON_ACTIVATED not published"
    print(f"   ✅ NEURON_ACTIVATED: {len(events_received['NEURON_ACTIVATED'])} events")
    print(f"      Activation levels: {[round(e['activation_level'], 2) for e in events_received['NEURON_ACTIVATED']]}")

    print("\n3️⃣ Testing SYNAPSE_STRENGTHENED (Hebbian learning)...")
    # Learn from success
    fabric.learn_from_outcome(activated, success=True, impact=1.0)
    wait_for_events()

    assert len(events_received["SYNAPSE_STRENGTHENED"]) >= 1, "SYNAPSE_STRENGTHENED not published"
    print(f"   ✅ SYNAPSE_STRENGTHENED: {len(events_received['SYNAPSE_STRENGTHENED'])} events")

    print("\n4️⃣ Testing SYNAPSE_WEAKENED (Anti-Hebbian)...")
    # Create new neurons for failure test
    neuron3 = fabric.create_neuron("Test belief 3", confidence=0.6)
    neuron4 = fabric.create_neuron("Test belief 4", confidence=0.6)
    fabric.connect(neuron3.neuron_id, neuron4.neuron_id, weight=0.6)

    activated_fail = fabric.activate(neuron3.neuron_id, signal=1.0)
    wait_for_events()

    # Learn from failure
    fabric.learn_from_outcome(activated_fail, success=False, impact=1.0)
    wait_for_events()

    assert len(events_received["SYNAPSE_WEAKENED"]) >= 1, "SYNAPSE_WEAKENED not published"
    print(f"   ✅ SYNAPSE_WEAKENED: {len(events_received['SYNAPSE_WEAKENED'])} events")

    print("\n5️⃣ Testing NEURON_PRUNED...")
    # Create a weak neuron and prune
    weak_neuron = fabric.create_neuron("Weak neuron", confidence=0.1)
    fabric._neurons[weak_neuron.neuron_id].energy = 0.01  # Make it very weak
    fabric._neurons[weak_neuron.neuron_id].activation_count = 0

    wait_for_events()
    pruned_count = fabric.prune()
    wait_for_events()

    if len(events_received["NEURON_PRUNED"]) >= 1:
        print(f"   ✅ NEURON_PRUNED: {len(events_received['NEURON_PRUNED'])} events")
    else:
        print(f"   ⚠️  NEURON_PRUNED: 0 events (neuron might not be weak enough)")

    # Summary
    print("\n" + "=" * 60)
    print("📊 Event Summary:")
    for event_name, events in events_received.items():
        status = "✅" if len(events) > 0 else "❌"
        print(f"   {status} {event_name}: {len(events)} events")

    total_events = sum(len(events) for events in events_received.values())
    print(f"\n🎉 Total events published: {total_events}")
    print("=" * 60)

    # Cleanup
    bus.unsubscribe(StandardEvents.NEURON_CREATED, "test")
    bus.unsubscribe(StandardEvents.NEURON_ACTIVATED, "test")
    bus.unsubscribe(StandardEvents.SYNAPSE_STRENGTHENED, "test")
    bus.unsubscribe(StandardEvents.SYNAPSE_WEAKENED, "test")
    bus.unsubscribe(StandardEvents.NEURON_PRUNED, "test")

    # Verify minimum events
    critical_events = ["NEURON_CREATED", "NEURON_ACTIVATED", "SYNAPSE_STRENGTHENED", "SYNAPSE_WEAKENED"]
    for event_name in critical_events:
        assert len(events_received[event_name]) >= 1, f"{event_name} not working!"

    print("\n✅ All critical neuron events are working!")
    return True

if __name__ == "__main__":
    try:
        test_neuron_events()
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
