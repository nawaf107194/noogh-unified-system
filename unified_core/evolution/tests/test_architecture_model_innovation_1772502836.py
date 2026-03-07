import pytest
from unified_core.evolution.architecture_model import ArchitectureModel

@pytest.fixture
def empty_architecture():
    model = ArchitectureModel()
    model.nodes = {}
    model.edges = []
    return model

@pytest.fixture
def simple_architecture():
    model = ArchitectureModel()
    node1 = {"module": "node1", "path": "/path/to/node1.py", "classes": 2, "functions": 3, "out_degree": 5}
    node2 = {"module": "node2", "path": "/path/to/node2.py", "classes": 6, "functions": 21, "out_degree": 15}
    edge = {"source": "node1", "target": "node2"}
    model.nodes["/path/to/node1.py"] = node1
    model.nodes["/path/to/node2.py"] = node2
    model.edges.append(edge)
    return model

@pytest.fixture
def circular_dependency_architecture():
    model = ArchitectureModel()
    node1 = {"module": "node1", "path": "/path/to/node1.py", "out_degree": 0}
    node2 = {"module": "node2", "path": "/path/to/node2.py", "out_degree": 0}
    edge1 = {"source": "node1", "target": "node2"}
    edge2 = {"source": "node2", "target": "node1"}
    model.nodes["/path/to/node1.py"] = node1
    model.nodes["/path/to/node2.py"] = node2
    model.edges.extend([edge1, edge2])
    return model

@pytest.fixture
def high_coupling_architecture():
    model = ArchitectureModel()
    node1 = {"module": "node1", "path": "/path/to/node1.py", "out_degree": 20}
    node2 = {"module": "node2", "path": "/path/to/node2.py", "out_degree": 5}
    edge = {"source": "node1", "target": "node2"}
    model.nodes["/path/to/node1.py"] = node1
    model.nodes["/path/to/node2.py"] = node2
    model.edges.append(edge)
    return model

@pytest.fixture
def layer_violation_architecture():
    model = ArchitectureModel()
    layer_order = {"TOOLS": 0, "SKILLS": 1}
    node1 = {"module": "node1", "path": "/path/to/node1.py", "layer": "TOOLS", "out_degree": 5}
    node2 = {"module": "node2", "path": "/path/to/node2.py", "layer": "SKILLS", "out_degree": 2}
    edge = {"source": "node1", "target": "node2"}
    model.nodes["/path/to/node1.py"] = node1
    model.nodes["/path/to/node2.py"] = node2
    model.edges.append(edge)
    return model

def test_happy_path(simple_architecture):
    smells = simple_architecture.detect_smells()
    assert len(smells) == 3
    assert any(s["type"] == "god_file" for s in smells)
    assert any(s["type"] == "high_coupling" for s in smells)
    assert any(s["type"] == "layer_violation" for s in smells)

def test_empty_architecture(empty_architecture):
    smells = empty_architecture.detect_smells()
    assert len(smells) == 0

def test_circular_dependency(circular_dependency_architecture):
    smells = circular_dependency_architecture.detect_smells()
    assert len(smells) == 1
    assert smells[0]["type"] == "circular_dependency"

def test_high_coupling(high_coupling_architecture):
    smells = high_coupling_architecture.detect_smells()
    assert len(smells) == 1
    assert smells[0]["type"] == "high_coupling"

def test_layer_violation(layer_violation_architecture):
    smells = layer_violation_architecture.detect_smells()
    assert len(smells) == 1
    assert smells[0]["type"] == "layer_violation"