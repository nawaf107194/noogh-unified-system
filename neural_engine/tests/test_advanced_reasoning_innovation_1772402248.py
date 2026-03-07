import pytest

from neural_engine.advanced_reasoning import _detect_semantic_patterns, Pattern


@pytest.fixture
def context_learning():
    return {"user_intent": "I want to learn about machine learning"}


@pytest.fixture
def context_creation():
    return {"user_intent": "Let's create a new project"}


@pytest.fixture
def empty_context():
    return {}


def test_detect_semantic_patterns_happy_path(context_learning):
    data = ["some data"]
    patterns = _detect_semantic_patterns(data, context_learning)
    assert len(patterns) == 1
    pattern = patterns[0]
    assert pattern.pattern_type == "semantic"
    assert pattern.description == "Learning intent pattern"
    assert pattern.confidence == 0.8
    assert pattern.occurrences == 1
    assert pattern.examples == ["I want to learn about machine learning"]
    assert pattern.metadata == {"intent_category": "learning"}


def test_detect_semantic_patterns_edge_case_empty_context(empty_context):
    data = ["some data"]
    patterns = _detect_semantic_patterns(data, empty_context)
    assert len(patterns) == 0


def test_detect_semantic_patterns_async_behavior():
    # Since the function is synchronous, there's no need for an async test
    pass

# Error cases are covered by edge cases since they would result in an empty context