import pytest
import os
from unittest.mock import patch

from gateway.app.core.policy_store import get_policy_store, PolicyStore

@pytest.fixture
def mock_policy_store():
    with patch('gateway.app.core.policy_store.PolicyStore') as MockPolicyStore:
        yield MockPolicyStore

def test_happy_path(mock_policy_store):
    with patch.dict('os.environ', {'NOOGH_POLICY_FILE': '/path/to/test/policy.json'}):
        policy_store = get_policy_store()
        mock_policy_store.assert_called_once_with('/path/to/test/policy.json')
        assert policy_store == mock_policy_store.return_value

def test_edge_case_none(mock_policy_store):
    with patch.dict('os.environ', {'NOOGH_POLICY_FILE': None}):
        policy_store = get_policy_store()
        mock_policy_store.assert_called_once_with('/home/noogh/projects/noogh_unified_system/runtime/policy.json')
        assert policy_store == mock_policy_store.return_value

def test_edge_case_empty(mock_policy_store):
    with patch.dict('os.environ', {'NOOGH_POLICY_FILE': ''}):
        policy_store = get_policy_store()
        mock_policy_store.assert_called_once_with('/home/noogh/projects/noogh_unified_system/runtime/policy.json')
        assert policy_store == mock_policy_store.return_value

def test_edge_case_boundary(mock_policy_store):
    with patch.dict('os.environ', {'NOOGH_POLICY_FILE': '/home/noogh/projects/noogh_unified_system/runtime/policy.json'}), \
         patch('gateway.app.core.policy_store.os.path.exists') as mock_exists:
        mock_exists.return_value = False
        policy_store = get_policy_store()
        mock_policy_store.assert_called_once_with('/home/noogh/projects/noogh_unified_system/runtime/policy.json')
        assert policy_store == mock_policy_store.return_value

def test_error_case_invalid_path(mock_policy_store):
    with patch.dict('os.environ', {'NOOGH_POLICY_FILE': '/invalid/path'}), \
         pytest.raises(FileNotFoundError):
        policy_store = get_policy_store()