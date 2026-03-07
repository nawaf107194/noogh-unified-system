import pytest

from gateway.app.core.system_introspector import SystemIntrospector

@pytest.fixture
def system_introspector():
    return SystemIntrospector()

def test_discover_relationships_happy_path(system_introspector):
    concepts = {
        'concept1': {'source1'},
        'concept2': {'source1', 'source2'},
        'concept3': {'source3'}
    }
    expected = [('concept1', 'related_to', 'concept2')]
    result = system_introspector._discover_relationships(concepts)
    assert result == expected

def test_discover_relationships_edge_case_empty(system_introspector):
    concepts = {}
    expected = []
    result = system_introspector._discover_relationships(concepts)
    assert result == expected

def test_discover_relationships_edge_case_none(system_introspector):
    concepts = None
    expected = []
    result = system_introspector._discover_relationships(concepts)
    assert result == expected

def test_discover_relationships_boundary_max_checks(system_introspector):
    concepts = {
        f'concept{i}': {f'source{i}' for _ in range(10)} for i in range(21)
    }
    expected = [('concept0', 'related_to', 'concept1')]
    result = system_introspector._discover_relationships(concepts)
    assert result == expected

def test_discover_relationships_error_case_invalid_input(system_introspector):
    concepts = 'not a dict'
    expected = []
    result = system_introspector._discover_relationships(concepts)
    assert result == expected