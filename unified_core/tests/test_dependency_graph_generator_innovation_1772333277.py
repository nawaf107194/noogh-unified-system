import os
from unittest.mock import patch, MagicMock
import pytest

# Assuming DependencyGraphGenerator is in the current module or accessible via __name__
from unified_core.dependency_graph_generator import DependencyGraphGenerator

def test_build_graph_happy_path():
    # Set up
    root_dir = '/path/to/root'
    generator = DependencyGraphGenerator(root_dir)
    
    with patch.object(generator, 'parse_module', return_value=['dep1.py', 'dep2.py']):
        with patch.object(generator.graph, 'add_edge') as mock_add_edge:
            generator.build_graph()
            
    # Asserts
    assert os.path.join(root_dir, 'file.py') in mock_add_edge.call_args_list[0]
    assert 'dep1.py' in mock_add_edge.call_args_list[1]
    assert 'dep2.py' in mock_add_edge.call_args_list[2]

def test_build_graph_empty_directory():
    # Set up
    root_dir = '/path/to/empty'
    generator = DependencyGraphGenerator(root_dir)
    
    with patch('os.walk', return_value=[(root_dir, [], [])]):
        with patch.object(generator.graph, 'add_edge') as mock_add_edge:
            generator.build_graph()
            
    # Asserts
    assert not mock_add_edge.called

def test_build_graph_with_none_root():
    # Set up
    root_dir = None
    generator = DependencyGraphGenerator(root_dir)
    
    with patch('os.walk', return_value=[(root_dir, [], [])]):
        with patch.object(generator.graph, 'add_edge') as mock_add_edge:
            result = generator.build_graph()
            
    # Asserts
    assert result is None

def test_build_graph_with_invalid_root():
    # Set up
    root_dir = '/path/to/invalid/root'
    generator = DependencyGraphGenerator(root_dir)
    
    with patch('os.walk', side_effect=FileNotFoundError):
        with patch.object(generator.graph, 'add_edge') as mock_add_edge:
            result = generator.build_graph()
            
    # Asserts
    assert not mock_add_edge.called

def test_build_graph_async_behavior():
    async def parse_module_mock(full_path):
        return ['dep1.py', 'dep2.py']
    
    # Set up
    root_dir = '/path/to/root'
    generator = DependencyGraphGenerator(root_dir)
    
    with patch.object(generator, 'parse_module', side_effect=parse_module_mock):
        with patch.object(generator.graph, 'add_edge') as mock_add_edge:
            asyncio.run(generator.build_graph())
            
    # Asserts
    assert os.path.join(root_dir, 'file.py') in mock_add_edge.call_args_list[0]
    assert 'dep1.py' in mock_add_edge.call_args_list[1]
    assert 'dep2.py' in mock_add_edge.call_args_list[2]

# Run the tests
if __name__ == "__main__":
    pytest.main()