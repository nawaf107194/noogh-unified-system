import pytest
import os
import tempfile
import networkx as nx
from dependency_graph_generator import DependencyGraphGenerator

def test_init_happy_path():
    # Test with valid root directory
    with tempfile.TemporaryDirectory() as temp_dir:
        dgg = DependencyGraphGenerator(temp_dir)
        assert dgg.root_dir == temp_dir
        assert isinstance(dgg.graph, nx.DiGraph)
        assert len(dgg.graph.nodes) == 0
        assert len(dgg.graph.edges) == 0

def test_init_edge_cases():
    # Test with empty string
    dgg = DependencyGraphGenerator("")
    assert dgg.root_dir == ""
    assert isinstance(dgg.graph, nx.DiGraph)
    
    # Test with None
    dgg = DependencyGraphGenerator(None)
    assert dgg.root_dir is None
    assert isinstance(dgg.graph, nx.DiGraph)
    
    # Test with root directory that doesn't exist
    dgg = DependencyGraphGenerator("/nonexistent/path")
    assert dgg.root_dir == "/nonexistent/path"
    assert isinstance(dgg.graph, nx.DiGraph)

def test_init_error_cases():
    # Test with invalid directory type
    with pytest.raises(TypeError):
        DependencyGraphGenerator(123)
        
    # Test with invalid directory path
    with pytest.raises(OSError):
        DependencyGraphGenerator("invalid://path")