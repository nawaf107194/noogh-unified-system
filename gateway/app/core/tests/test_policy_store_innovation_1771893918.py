import pytest
from unittest.mock import patch, MagicMock

from gateway.app.core.policy_store import PolicyStore, PolicySnapshot

class TestPolicyStore:

    @pytest.fixture
    def policy_store(self):
        return PolicyStore()

    def test_patch_happy_path(self, policy_store):
        initial_policy = {
            "a": 1,
            "b": {
                "c": 2
            }
        }
        patch = {
            "b": {
                "d": 3
            },
            "e": 4
        }
        expected_result = {
            "a": 1,
            "b": {
                "c": 2,
                "d": 3
            },
            "e": 4
        }

        with patch.object(policy_store, '_lock'), \
             patch.object(policy_store, '_deep_merge', return_value=expected_result), \
             patch.object(policy_store, 'update', return_value=PolicySnapshot()):
            
            result = policy_store.patch(patch)

            assert isinstance(result, PolicySnapshot)
           .policy_store._deep_merge.assert_called_once_with(initial_policy, patch)
            policy_store.update.assert_called_once_with(expected_result)

    def test_patch_empty_patch(self, policy_store):
        initial_policy = {
            "a": 1,
            "b": {
                "c": 2
            }
        }
        patch = {}
        expected_result = {
            "a": 1,
            "b": {
                "c": 2
            }
        }

        with patch.object(policy_store, '_lock'), \
             patch.object(policy_store, '_deep_merge', return_value=expected_result), \
             patch.object(policy_store, 'update', return_value=PolicySnapshot()):
            
            result = policy_store.patch(patch)

            assert isinstance(result, PolicySnapshot)
            .policy_store._deep_merge.assert_called_once_with(initial_policy, patch)
            policy_store.update.assert_called_once_with(expected_result)

    def test_patch_none_patch(self, policy_store):
        initial_policy = {
            "a": 1,
            "b": {
                "c": 2
            }
        }
        expected_result = {
            "a": 1,
            "b": {
                "c": 2
            }
        }

        with patch.object(policy_store, '_lock'), \
             patch.object(policy_store, '_deep_merge', return_value=expected_result), \
             patch.object(policy_store, 'update', return_value=PolicySnapshot()):
            
            result = policy_store.patch(None)

            assert isinstance(result, PolicySnapshot)
            .policy_store._deep_merge.assert_called_once_with(initial_policy, None)
            policy_store.update.assert_called_once_with(expected_result)

    def test_patch_boundary_conditions(self, policy_store):
        initial_policy = {
            "a": 1,
            "b": {
                "c": [2, 3, 4]
            }
        }
        patch = {
            "b": {
                "c": []
            }
        }
        expected_result = {
            "a": 1,
            "b": {
                "c": []
            }
        }

        with patch.object(policy_store, '_lock'), \
             patch.object(policy_store, '_deep_merge', return_value=expected_result), \
             patch.object(policy_store, 'update', return_value=PolicySnapshot()):
            
            result = policy_store.patch(patch)

            assert isinstance(result, PolicySnapshot)
            .policy_store._deep_merge.assert_called_once_with(initial_policy, patch)
            policy_store.update.assert_called_once_with(expected_result)

    def test_patch_invalid_input(self, policy_store):
        initial_policy = {
            "a": 1,
            "b": {
                "c": 2
            }
        }

        with pytest.raises(TypeError) as exc_info:
            policy_store.patch("not a dict")

        assert str(exc_info.value) == "Input must be a dictionary"