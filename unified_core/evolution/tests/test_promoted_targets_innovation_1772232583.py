import pytest

from unified_core.evolution.promoted_targets import PromotedTargets

class TestPromotedTargets:

    @pytest.fixture
    def promoted_targets_empty(self):
        return PromotedTargets([])

    @pytest.fixture
    def promoted_targets_single(self):
        return PromotedTargets(['single_target'])

    @pytest.fixture
    def promoted_targets_multiple(self):
        return PromotedTargets(['target1', 'target2', 'target3'])

    def test_count_happy_path(self, promoted_targets_multiple):
        assert promoted_targets_multiple.count() == 3

    def test_count_empty(self, promoted_targets_empty):
        assert promoted_targets_empty.count() == 0

    def test_count_single(self, promoted_targets_single):
        assert promoted_targets_single.count() == 1