import pytest

class MockPolicyStore:
    def _validate(self, p: Dict[str, Any]) -> None:
        raise NotImplementedError("This method should be overridden")

@pytest.mark.parametrize("policy", [
    {"thresholds": {"min_confidence": 0.5}},
    {"allow_actions": ["action1", "action2"]},
    {"block_actions": ["action3", "action4"]}
])
def test_happy_path(policy: Dict[str, Any]):
    policy_store = MockPolicyStore()
    result = policy_store._validate(policy)
    assert result is None

@pytest.mark.parametrize("policy, expected_error", [
    ({"thresholds": {"min_confidence": 1.5}}, "thresholds.min_confidence must be between 0 and 1"),
    ({"thresholds": {"min_confidence": -0.5}}, "thresholds.min_confidence must be between 0 and 1"),
    ({}, "allow_actions must be list"),
    ({}, "block_actions must be list"),
    ({"allow_actions": "not a list"}, "allow_actions must be list"),
    ({"block_actions": "not a list"}, "block_actions must be list")
])
def test_error_cases(policy: Dict[str, Any], expected_error: str):
    policy_store = MockPolicyStore()
    with pytest.raises(ValueError) as exc_info:
        policy_store._validate(policy)
    assert str(exc_info.value) == expected_error