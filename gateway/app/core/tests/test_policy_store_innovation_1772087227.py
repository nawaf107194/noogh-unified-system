import pytest
from unittest.mock import patch, mock_open
from gateway.app.core.policy_store import get_policy_store, PolicyStore

@pytest.fixture(autouse=True)
def reset_policy_store():
    global _policy_store
    _policy_store = None

@patch('os.getenv')
def test_get_policy_store_happy_path(mock_getenv):
    mock_getenv.return_value = "/home/noogh/projects/noogh_unified_system/runtime/policy.json"
    
    # First call should create the policy store
    store1 = get_policy_store()
    assert isinstance(store1, PolicyStore)
    assert store1.path == "/home/noogh/projects/noogh_unified_system/runtime/policy.json"

    # Second call should return the same instance
    store2 = get_policy_store()
    assert store1 is store2

@patch('os.getenv')
def test_get_policy_store_default_path(mock_getenv):
    mock_getenv.return_value = None
    
    # First call should create the policy store with default path
    store1 = get_policy_store()
    assert isinstance(store1, PolicyStore)
    assert store1.path == "/home/noogh/projects/noogh_unified_system/runtime/policy.json"

@patch('os.getenv')
def test_get_policy_store_empty_path(mock_getenv):
    mock_getenv.return_value = ""
    
    # First call should create the policy store with default path
    store1 = get_policy_store()
    assert isinstance(store1, PolicyStore)
    assert store1.path == "/home/noogh/projects/noogh_unified_system/runtime/policy.json"

@patch('os.getenv')
def test_get_policy_store_none_path(mock_getenv):
    mock_getenv.return_value = None
    
    # First call should create the policy store with default path
    store1 = get_policy_store()
    assert isinstance(store1, PolicyStore)
    assert store1.path == "/home/noogh/projects/noogh_unified_system/runtime/policy.json"

@patch('os.getenv')
def test_get_policy_store_boundary_path(mock_getenv):
    mock_getenv.return_value = "/home/noogh/projects/noogh_unified_system/runtime/policy.json"
    
    # First call should create the policy store
    store1 = get_policy_store()
    assert isinstance(store1, PolicyStore)
    assert store1.path == "/home/noogh/projects/noogh_unified_system/runtime/policy.json"

# Error cases are not applicable here as the function does not explicitly raise exceptions for invalid inputs.