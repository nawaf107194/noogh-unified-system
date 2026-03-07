import pytest
from unittest.mock import patch, MagicMock
from unified_core.tool_registry import get_unified_registry

@pytest.fixture
def mock_registry():
    with patch('unified_core.tool_registry.get_unified_registry') as mock_get_registry:
        yield mock_get_registry()

def test_check_registry_loaded_happy_path(mock_registry):
    # Mock the registry to return a non-empty list of tools
    mock_registry.list_tools.return_value = ['tool1', 'tool2']
    assert check_registry_loaded() == True

def test_check_registry_loaded_empty_list(mock_registry):
    # Mock the registry to return an empty list of tools
    mock_registry.list_tools.return_value = []
    assert check_registry_loaded() == False

def test_check_registry_loaded_exception_raised():
    # Mock the import to raise an exception
    with patch('unified_core.tool_registry.get_unified_registry', side_effect=Exception):
        assert check_registry_loaded() == False

def test_check_registry_loaded_list_tools_exception(mock_registry):
    # Mock the list_tools method to raise an exception
    mock_registry.list_tools.side_effect = Exception
    assert check_registry_loaded() == False

# Since the function does not involve async operations, no need to test async behavior.