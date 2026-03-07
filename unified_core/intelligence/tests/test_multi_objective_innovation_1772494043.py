import pytest

from unified_core.intelligence.multi_objective import MultiObjectiveOption, select_best_weighted

# Sample data for testing
options = [
    MultiObjectiveOption(normalized_scores={'speed': 0.8, 'cost': 0.2}, objectives=[{'name': 'speed', 'weight': 3}, {'name': 'cost', 'weight': 1}]),
    MultiObjectiveOption(normalized_scores={'speed': 0.7, 'cost': 0.3}, objectives=[{'name': 'speed', 'weight': 3}, {'name': 'cost', 'weight': 1}]),
]

def test_select_best_weighted_happy_path():
    best_option = select_best_weighted(options)
    assert best_option.normalized_scores['_weighted_total'] == pytest.approx(4.0)

def test_select_best_weighted_empty_options():
    empty_options: List[MultiObjectiveOption] = []
    best_option = select_best_weighted(empty_options)
    assert best_option is None

def test_select_best_weighted_none_options():
    best_option = select_best_weighted(None)
    assert best_option is None

def test_select_best_weighted_objectives_boundary():
    options_with_boundaries = [
        MultiObjectiveOption(normalized_scores={'speed': 1.0, 'cost': 0.0}, objectives=[{'name': 'speed', 'weight': 3}, {'name': 'cost', 'weight': 1}]),
        MultiObjectiveOption(normalized_scores={'speed': 0.0, 'cost': 1.0}, objectives=[{'name': 'speed', 'weight': 3}, {'name': 'cost', 'weight': 1}]),
    ]
    best_option = select_best_weighted(options_with_boundaries)
    assert best_option.normalized_scores['_weighted_total'] == pytest.approx(3.0)

def test_select_best_weighted_invalid_objectives():
    invalid_options = [
        MultiObjectiveOption(normalized_scores={'speed': 0.8, 'cost': 0.2}, objectives=[{'name': 'foo', 'weight': 3}]),
    ]
    best_option = select_best_weighted(invalid_options)
    assert best_option is None