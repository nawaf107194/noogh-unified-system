import pytest
from unittest.mock import Mock

def test_happy_path_initialization():
    """Test that __init__ properly initializes with a valid CognitiveCore instance"""
    # Create mock CognitiveCore instance
    mock_cognitive_core = Mock()
    
    # Initialize Architecture with mock
    architecture = Architecture(mock_cognitive_core)
    
    # Assert initialization worked
    assert architecture.cognitive_core == mock_cognitive_core

def test_edge_case_none_initialization():
    """Test that __init__ allows None as cognitive_core"""
    architecture = Architecture(None)
    assert architecture.cognitive_core is None

def test_edge_case_invalid_type():
    """Test __init__ behavior when passed invalid type"""
    # Test with non-CognitiveCore instance
    architecture = Architecture(123)
    assert architecture.cognitive_core == 123