import pytest

from unified_core.intelligence.multi_objective import MultiObjectiveOption, Objective

class TestMultiObjectiveDominates:

    @pytest.mark.parametrize("self_scores, other_scores, objectives, expected", [
        (
            {"objective1": 1.0, "objective2": 2.0},
            {"objective1": 0.5, "objective2": 1.5},
            [Objective(name="objective1", minimize=True), Objective(name="objective2", minimize=False)],
            True
        ),
        (
            {"objective1": 1.0, "objective2": 2.0},
            {"objective1": 1.1, "objective2": 1.9},
            [Objective(name="objective1", minimize=True), Objective(name="objective2", minimize=False)],
            False
        ),
        (
            {"objective1": 1.0, "objective2": 2.0},
            {"objective1": 0.5, "objective2": 1.5},
            [Objective(name="objective1", minimize=True), Objective(name="objective2", minimize=False)],
            True
        ),
        (
            {},
            {},
            [],
            False
        ),
        (
            None,
            {"objective1": 1.0},
            [Objective(name="objective1", minimize=True)],
            False
        ),
        (
            {"objective1": 1.0},
            None,
            [Objective(name="objective1", minimize=True)],
            False
        )
    ])
    def test_dominates(self, self_scores, other_scores, objectives, expected):
        self_option = MultiObjectiveOption(scores=self_scores)
        other_option = MultiObjectiveOption(scores=other_scores)
        
        result = self_option.dominates(other_option, objectives)
        assert result == expected