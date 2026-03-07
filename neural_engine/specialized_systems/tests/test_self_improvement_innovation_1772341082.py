import pytest

from neural_engine.specialized_systems.self_improvement import create_learning_goal, LearningGoal

@pytest.fixture
def system():
    from neural_engine.system import NeuralSystem  # Adjust the import as needed
    return NeuralSystem()

def test_happy_path(system):
    goal = create_learning_goal(system, "Mathematics", "To improve problem-solving skills", 5)
    assert isinstance(goal, LearningGoal)
    assert goal.topic == "Mathematics"
    assert goal.reason == "To improve problem-solving skills"
    assert goal.priority == 5
    assert system.learning_goals == [goal]

def test_edge_case_empty_topic(system):
    with pytest.raises(ValueError):
        create_learning_goal(system, "", "Reason", 5)

def test_edge_case_none_reason(system):
    with pytest.raises(ValueError):
        create_learning_goal(system, "Topic", None, 5)

def test_edge_case_min_priority(system):
    goal = create_learning_goal(system, "Topic", "Reason", 1)
    assert isinstance(goal, LearningGoal)
    assert goal.priority == 1

def test_edge_case_max_priority(system):
    system.config.max_priority = 10
    goal = create_learning_goal(system, "Topic", "Reason", 10)
    assert isinstance(goal, LearningGoal)
    assert goal.priority == 10

def test_error_case_invalid_priority_high(system):
    with pytest.raises(ValueError):
        create_learning_goal(system, "Topic", "Reason", 20)

def test_error_case_invalid_priority_low(system):
    with pytest.raises(ValueError):
        create_learning_goal(system, "Topic", "Reason", -1)