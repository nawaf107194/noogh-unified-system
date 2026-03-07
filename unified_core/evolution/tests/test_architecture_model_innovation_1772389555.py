import pytest
from unified_core.evolution.architecture_model import ArchitectureModel, Node, Edge

def create_test_architecture():
    model = ArchitectureModel()
    
    # Create nodes with different properties
    node1 = Node(path="module1.py", classes=3, functions=8, out_degree=5)
    node2 = Node(path="module2.py", classes=6, functions=25, out_degree=12)
    node3 = Node(path="module3.py", classes=4, functions=10, out_degree=7)
    
    # Create edges with different properties
    edge1 = Edge(source=node1, target=node2)
    edge2 = Edge(source=node3, target=node1)
    edge3 = Edge(source=node2, target=node3)
    
    model.nodes[node1.module] = node1
    model.nodes[node2.module] = node2
    model.nodes[node3.module] = node3
    
    model.edges.add(edge1)
    model.edges.add(edge2)
    model.edges.add(edge3)
    
    # Reverse index for circular dependencies
    model._reverse_index[node1.module] = {node2.module}
    model._reverse_index[node2.module] = {node1.module, node3.module}
    model._reverse_index[node3.module] = {node2.module}
    
    return model

def test_detect_smells_happy_path():
    model = create_test_architecture()
    smells = model.detect_smells()
    
    assert len(smells) == 4
    
    # Check for circular dependency smell
    circular_dependency = next((s for s in smells if s["type"] == "circular_dependency"), None)
    assert circular_dependency is not None
    
    # Check for god file smell
    god_file = next((s for s in smells if s["type"] == "god_file" and s["file"] == "module2.py"), None)
    assert god_file is not None
    
    # Check for high coupling smell
    high_coupling = next((s for s in smells if s["type"] == "high_coupling" and s["file"] == "module3.py"), None)
    assert high_coupling is not None
    
    # Check for layer violation smell
    layer_violation = next((s for s in smells if s["type"] == "layer_violation"), None)
    assert layer_violation is not None

def test_detect_smells_empty_input():
    model = ArchitectureModel()
    smells = model.detect_smells()
    
    assert len(smells) == 0

def test_detect_smells_none_input():
    with pytest.raises(AttributeError):
        ArchitectureModel().detect_smells()

# Add more tests as needed for edge cases and error handling