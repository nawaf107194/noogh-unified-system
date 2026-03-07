import pytest

from neural_engine.specialized_systems.self_improvement import SelfImprovementEngine, LearningGoal
from unittest.mock import patch
import logging

# Mock the logger to capture the log message
@patch('neural_engine.specialized_systems.self_improvement.logger.info')
def test_init_happy_path(mock_info):
    engine = SelfImprovementEngine()
    assert len(engine.learning_goals) == 1
    assert isinstance(engine.learning_goals[0], LearningGoal)
    assert mock_info.call_count == 1

@patch('neural_engine.specialized_systems.self_improvement.logger.info')
def test_init_edge_case_empty_goals(mock_info):
    engine = SelfImprovementEngine([])
    assert len(engine.learning_goals) == 1
    assert isinstance(engine.learning_goals[0], LearningGoal)
    assert mock_info.call_count == 1

@patch('neural_engine.specialized_systems.self_improvement.logger.info')
def test_init_edge_case_none_goals(mock_info):
    engine = SelfImprovementEngine(None)
    assert len(engine.learning_goals) == 1
    assert isinstance(engine.learning_goals[0], LearningGoal)
    assert mock_info.call_count == 1

@patch('neural_engine.specialized_systems.self_improvement.logger.info')
def test_init_edge_case_empty_list(mock_info):
    engine = SelfImprovementEngine([])
    assert len(engine.learning_goals) == 0
    assert not any(isinstance(item, LearningGoal) for item in engine.learning_goals)
    assert mock_info.call_count == 1

@patch('neural_engine.specialized_systems.self_improvement.logger.info')
def test_init_edge_case_none_list(mock_info):
    engine = SelfImprovementEngine(None)
    assert len(engine.learning_goals) == 0
    assert not any(isinstance(item, LearningGoal) for item in engine.learning_goals)
    assert mock_info.call_count == 1

@patch('neural_engine.specialized_systems.self_improvement.logger.info')
def test_init_edge_case_single_goal(mock_info):
    goal = LearningGoal(
        topic="Advanced Cybersecurity Patterns",
        reason="Increase detection precision for sophisticated RCE attempts",
        priority=10,
        status="active"
    )
    engine = SelfImprovementEngine([goal])
    assert len(engine.learning_goals) == 1
    assert engine.learning_goals[0] is goal
    assert mock_info.call_count == 1

@patch('neural_engine.specialized_systems.self_improvement.logger.info')
def test_init_edge_case_multiple_goals(mock_info):
    goals = [
        LearningGoal(
            topic="Advanced Cybersecurity Patterns",
            reason="Increase detection precision for sophisticated RCE attempts",
            priority=10,
            status="active"
        ),
        LearningGoal(
            topic="AI Ethics",
            reason="Ensure ethical use of AI in all applications",
            priority=5,
            status="pending"
        )
    ]
    engine = SelfImprovementEngine(goals)
    assert len(engine.learning_goals) == 2
    for goal in goals:
        assert any(item is goal for item in engine.learning_goals)
    assert mock_info.call_count == 1

@patch('neural_engine.specialized_systems.self_improvement.logger.info')
def test_init_edge_case_invalid_goal_types(mock_info):
    invalid_goal = "not a learning goal"
    with pytest.raises(TypeError) as e:
        SelfImprovementEngine([invalid_goal])
    assert str(e.value) == "All items in the goals list must be instances of LearningGoal"

@patch('neural_engine.specialized_systems.self_improvement.logger.info')
def test_init_edge_case_empty_string_topic(mock_info):
    goal = LearningGoal(
        topic="",
        reason="Increase detection precision for sophisticated RCE attempts",
        priority=10,
        status="active"
    )
    with pytest.raises(ValueError) as e:
        SelfImprovementEngine([goal])
    assert str(e.value) == "Topic cannot be an empty string"

@patch('neural_engine.specialized_systems.self_improvement.logger.info')
def test_init_edge_case_invalid_status(mock_info):
    goal = LearningGoal(
        topic="Advanced Cybersecurity Patterns",
        reason="Increase detection precision for sophisticated RCE attempts",
        priority=10,
        status="invalid"
    )
    with pytest.raises(ValueError) as e:
        SelfImprovementEngine([goal])
    assert str(e.value) == "Invalid status. Must be one of ['active', 'pending']"