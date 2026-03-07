import pytest

from neural_engine.autonomy.safety_policy import get_safety_policy, SafetyPolicy

@pytest.fixture(autouse=True)
def reset_policy():
    """Reset global policy after each test."""
    global _policy
    _policy = None
    yield
    _policy = None

class TestGetSafetyPolicy:
    def test_happy_path(self):
        """Test normal execution."""
        policy = get_safety_policy()
        assert isinstance(policy, SafetyPolicy)
        assert policy is get_safety_policy()  # Ensure the same instance is returned

    @pytest.mark.parametrize("input_value", [None, "", [], {}])
    def test_edge_cases(self, input_value):
        """Test edge cases where no actual value should be passed."""
        policy = get_safety_policy()
        assert isinstance(policy, SafetyPolicy)
        assert policy is get_safety_policy()

    def test_no_policy_exists(self):
        """Test when no policy exists yet."""
        global _policy
        _policy = None
        policy = get_safety_policy()
        assert isinstance(policy, SafetyPolicy)

    def test_policy_exists(self):
        """Test when a policy already exists."""
        existing_policy = SafetyPolicy()
        global _policy
        _policy = existing_policy
        policy = get_safety_policy()
        assert policy is existing_policy

    # Async behavior not applicable as the function is synchronous