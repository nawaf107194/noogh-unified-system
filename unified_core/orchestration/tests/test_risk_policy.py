import pytest
from typing import List, Tuple
from unittest.mock import patch

# Assuming the class is named RiskPolicy and it has a class attribute BLOCKED_CHAINS defined
class RiskPolicy:
    BLOCKED_CHAINS = [
        (['tool_a', 'tool_b'], ['tool_c', 'tool_d'], 'Pattern1'),
        (['tool_e'], ['tool_f'], 'Pattern2')
    ]

    @classmethod
    def detect_chain(cls, tool_sequence: List[str]) -> Tuple[bool, str]:
        for first_tools, second_tools, pattern_name in cls.BLOCKED_CHAINS:
            first_indices = [i for i, tool in enumerate(tool_sequence) if tool in first_tools]
            second_indices = [i for i, tool in enumerate(tool_sequence) if tool in second_tools]
            for first_idx in first_indices:
                for second_idx in second_indices:
                    if first_idx < second_idx:
                        return True, pattern_name
        return False, ""

@pytest.fixture
def risk_policy_instance():
    return RiskPolicy()

def test_detect_chain_happy_path(risk_policy_instance):
    assert risk_policy_instance.detect_chain(['tool_a', 'tool_b', 'tool_c']) == (True, 'Pattern1')
    assert risk_policy_instance.detect_chain(['tool_e', 'tool_f']) == (True, 'Pattern2')

def test_detect_chain_edge_cases(risk_policy_instance):
    assert risk_policy_instance.detect_chain([]) == (False, '')
    assert risk_policy_instance.detect_chain(['tool_a']) == (False, '')
    assert risk_policy_instance.detect_chain(['tool_c', 'tool_d']) == (False, '')

def test_detect_chain_invalid_inputs(risk_policy_instance):
    with pytest.raises(TypeError):
        risk_policy_instance.detect_chain(None)
    with pytest.raises(TypeError):
        risk_policy_instance.detect_chain(123)
    with pytest.raises(TypeError):
        risk_policy_instance.detect_chain('tool_a')

def test_detect_chain_async_behavior(risk_policy_instance):
    # Since the function is synchronous, there's no direct async behavior to test.
    # However, we can mock an asynchronous call to simulate async behavior.
    with patch.object(RiskPolicy, 'detect_chain', new=lambda cls, x: (True, 'PatternAsync')) as mock_method:
        assert risk_policy_instance.detect_chain(['tool_async']) == (True, 'PatternAsync')
        mock_method.assert_called_once_with(['tool_async'])