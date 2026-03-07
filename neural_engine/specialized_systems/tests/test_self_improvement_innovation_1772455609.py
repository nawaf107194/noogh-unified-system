import pytest

class MockLogger:
    def info(self, message):
        pass

class LearningGoal:
    def __init__(self, topic: str, reason: str, priority: int):
        self.topic = topic
        self.reason = reason
        self.priority = priority

class NeuralEngine:
    def __init__(self):
        self.learning_goals = []
        self.logger = MockLogger()

    def create_learning_goal(self, topic: str, reason: str, priority: int) -> LearningGoal:
        """Register a new autonomous learning target."""
        goal = LearningGoal(topic=topic, reason=reason, priority=priority)
        self.learning_goals.append(goal)
        self.logger.info(f"New learning goal created: {topic}")
        return goal

@pytest.fixture
def neural_engine():
    return NeuralEngine()

def test_happy_path(neural_engine):
    """Test creating a learning goal with valid inputs."""
    result = neural_engine.create_learning_goal("Python", "To improve my programming skills", 1)
    assert isinstance(result, LearningGoal)
    assert result.topic == "Python"
    assert result.reason == "To improve my programming skills"
    assert result.priority == 1
    assert len(neural_engine.learning_goals) == 1

def test_edge_cases(neural_engine):
    """Test creating a learning goal with edge cases (empty, None, boundaries)."""
    # Empty topic
    result = neural_engine.create_learning_goal("", "To learn about empty strings", 2)
    assert result is None
    assert len(neural_engine.learning_goals) == 1

    # None topic
    result = neural_engine.create_learning_goal(None, "To learn about None values", 3)
    assert result is None
    assert len(neural_engine.learning_goals) == 1

    # Boundary priority (0)
    result = neural_engine.create_learning_goal("Boundary", "To test boundary values", 0)
    assert isinstance(result, LearningGoal)
    assert result.priority == 0
    assert len(neural_engine.learning_goals) == 2

def test_error_cases(neural_engine):
    """Test creating a learning goal with error cases (invalid inputs)."""
    # Negative priority
    result = neural_engine.create_learning_goal("Negative Priority", "To test negative values", -1)
    assert result is None
    assert len(neural_engine.learning_goals) == 2

def test_async_behavior(neural_engine):
    """Test async behavior (if applicable)."""
    # Since the function doesn't have any async operations, this test is placeholder
    pass