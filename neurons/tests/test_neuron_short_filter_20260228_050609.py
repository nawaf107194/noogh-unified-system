import pytest

def neuron_short_filter(setup):
    if setup.get('volume', 0) < 2500000: return False, 0, 'Low volume'
    return True, 0.8, 'Good'

def test_neuron_short_filter_happy_path():
    setup = {'volume': 3000000}
    result = neuron_short_filter(setup)
    assert result == (True, 0.8, 'Good')

def test_neuron_short_filter_edge_case_empty():
    setup = {}
    result = neuron_short_filter(setup)
    assert result == (False, 0, 'Low volume')

def test_neuron_short_filter_edge_case_none():
    setup = None
    result = neuron_short_filter(setup)
    assert result == (False, 0, 'Low volume')

def test_neuron_short_filter_boundary_low_volume():
    setup = {'volume': 2500000}
    result = neuron_short_filter(setup)
    assert result == (False, 0, 'Low volume')

def test_neuron_short_filter_boundary_high_volume():
    setup = {'volume': 2500001}
    result = neuron_short_filter(setup)
    assert result == (True, 0.8, 'Good')