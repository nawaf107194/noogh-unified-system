import pytest

from unified_core.evolution.promoted_targets import get_all

class TestGetAll:

    def test_happy_path(self, promoted_targets):
        result = get_all(promoted_targets)
        assert isinstance(result, dict)
        assert len(result) == len(promoted_targets._targets)

    def test_empty_dict(self, empty_promoted_targets):
        result = get_all(empty_promoted_targets)
        assert isinstance(result, dict)
        assert len(result) == 0

    @pytest.mark.parametrize("invalid_input", [None, [], "string"])
    def test_invalid_inputs(self, invalid_input):
        with pytest.raises(ValueError):
            get_all(invalid_input)

# Fixtures to create instances of promoted_targets for testing
@pytest.fixture
def promoted_targets():
    from unified_core.evolution.promoted_targets import PromotedTargets
    return PromotedTargets({"key1": {"value": "data"}, "key2": {"value": "more data"}})

@pytest.fixture
def empty_promoted_targets():
    from unified_core.evolution.promoted_targets import PromotedTargets
    return PromotedTargets({})