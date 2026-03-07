import pytest

from unified_core.core.neuron_pulse import NeuronPulse

class MockFabric:
    def __init__(self):
        self.activate_by_query_results = []
        self.get_neurons_by_domain_results = {}
    
    def activate_by_query(self, query, top_k=15):
        return self.activate_by_query_results.pop(0) if self.activate_by_query_results else []
    
    def get_neurons_by_domain(self, domain):
        return self.get_neurons_by_domain_results[domain]
    
    def activate(self, neuron_id, signal=0.6, depth=1):
        return []

@pytest.fixture
def neuron_pulse():
    pulse = NeuronPulse()
    pulse.PULSE_DOMAINS = [
        ("domain1", "query1", 2),
        ("domain2", "query2", 3)
    ]
    pulse._domain_stats = {}
    return pulse

def test_happy_path(neuron_pulse):
    fabric = MockFabric()
    fabric.activate_by_query_results.extend([[1, 2], [3]])
    fabric.get_neurons_by_domain_results = {
        "domain1": [{"neuron_id": 1, "is_alive": True}, {"neuron_id": 2, "is_alive": False}],
        "domain2": [{"neuron_id": 3, "is_alive": True}]
    }
    
    activated_count = neuron_pulse._pulse_domain(4, fabric)
    
    assert activated_count == 4
    assert neuron_pulse._domain_stats == {
        "domain1": 2,
        "domain2": 1
    }

def test_edge_cases(neuron_pulse):
    fabric_empty_queries = MockFabric()
    fabric_empty_queries.activate_by_query_results.extend([[], []])
    fabric_empty_queries.get_neurons_by_domain_results = {
        "domain1": [],
        "domain2": []
    }
    
    activated_count_empty = neuron_pulse._pulse_domain(4, fabric_empty_queries)
    
    assert activated_count_empty == 0
    assert neuron_pulse._domain_stats == {}

def test_error_cases(neuron_pulse):
    fabric_error = MockFabric()
    fabric_error.activate_by_query_results.extend([[1, 2], "error"])
    fabric_error.get_neurons_by_domain_results = {
        "domain1": [{"neuron_id": 1, "is_alive": True}],
        "domain2": [{"neuron_id": 3, "is_alive": True}]
    }
    
    activated_count_error = neuron_pulse._pulse_domain(4, fabric_error)
    
    assert activated_count_error == 2
    assert neuron_pulse._domain_stats == {
        "domain1": 1,
        "domain2": 0
    }

def test_async_behavior(neuron_pulse):
    class AsyncFabric(MockFabric):
        def activate(self, *args, **kwargs):
            import asyncio
            return asyncio.sleep(0.1)
    
    fabric = AsyncFabric()
    fabric.activate_by_query_results.extend([[1, 2], [3]])
    fabric.get_neurons_by_domain_results = {
        "domain1": [{"neuron_id": 1, "is_alive": True}, {"neuron_id": 2, "is_alive": False}],
        "domain2": [{"neuron_id": 3, "is_alive": True}]
    }
    
    activated_count_async = neuron_pulse._pulse_domain(4, fabric)
    
    assert activated_count_async == 4
    assert neuron_pulse._domain_stats == {
        "domain1": 2,
        "domain2": 1
    }