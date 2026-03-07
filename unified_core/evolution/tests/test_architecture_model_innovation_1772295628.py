import pytest
from pathlib import Path
from typing import Dict, Any

# Import the real class/function and test its actual outputs
from unified_core.evolution.architecture_model import ArchitectureModel

@pytest.fixture
def architecture_model():
    # Initialize with a simple graph for testing
    nodes = {
        '/path/to/file1.py': {'module': 'file1'},
        '/path/to/file2.py': {'module': 'file2'},
        '/path/to/file3.py': {'module': 'file3'}
    }
    import_index = {
        'file1': {'file2', 'file3'},
        'file2': set(),
        'file3': set()
    }
    return ArchitectureModel(nodes, import_index)

def test_happy_path(architecture_model):
    result = architecture_model.get_impact('/path/to/file1.py')
    assert result == {
        "direct": ['file2', 'file3'],
        "transitive": [],
        "direct_count": 2,
        "transitive_count": 0,
        "impact_score": round(2 / 3, 3)
    }

def test_edge_case_empty_input(architecture_model):
    result = architecture_model.get_impact('')
    assert result == {
        "direct": [],
        "transitive": [],
        "direct_count": 0,
        "transitive_count": 0,
        "impact_score": 0
    }

def test_edge_case_none_input(architecture_model):
    result = architecture_model.get_impact(None)
    assert result == {
        "direct": [],
        "transitive": [],
        "direct_count": 0,
        "transitive_count": 0,
        "impact_score": 0
    }

def test_error_case_invalid_path(architecture_model):
    result = architecture_model.get_impact('/path/to/nonexistent.py')
    assert result == {
        "direct": [],
        "transitive": [],
        "direct_count": 0,
        "transitive_count": 0,
        "impact_score": 0
    }

def test_async_behavior(architecture_model):
    # This function is synchronous, so we don't need to test async behavior here
    pass