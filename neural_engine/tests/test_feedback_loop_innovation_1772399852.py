import pytest

from neural_engine.feedback_loop import FeedbackLoop, LearningInsight

@pytest.fixture
def feedback_loop():
    return FeedbackLoop()

def test_generate_insight_happy_path(feedback_loop):
    pattern = "example_pattern"
    feedback_loop.patterns[pattern] = {"successes": 10, "occurrences": 25}

    insight = feedback_loop._generate_insight(pattern)

    assert isinstance(insight, LearningInsight)
    assert insight.pattern == "example_pattern"
    assert insight.confidence <= 1.0
    assert insight.occurrences == 25
    assert insight.success_rate == 40.0
    assert insight.recommendation == "Pattern 'example_pattern' has mixed results - use with caution"

def test_generate_insight_edge_case_empty_occurrences(feedback_loop):
    pattern = "empty_pattern"
    feedback_loop.patterns[pattern] = {"successes": 0, "occurrences": 0}

    insight = feedback_loop._generate_insight(pattern)

    assert isinstance(insight, LearningInsight)
    assert insight.pattern == "empty_pattern"
    assert insight.confidence <= 1.0
    assert insight.occurrences == 0
    assert insight.success_rate == 0.0
    assert insight.recommendation == "Pattern 'empty_pattern' often fails - consider alternative approach"

def test_generate_insight_edge_case_single_success(feedback_loop):
    pattern = "single_success"
    feedback_loop.patterns[pattern] = {"successes": 1, "occurrences": 1}

    insight = feedback_loop._generate_insight(pattern)

    assert isinstance(insight, LearningInsight)
    assert insight.pattern == "single_success"
    assert insight.confidence <= 1.0
    assert insight.occurrences == 1
    assert insight.success_rate == 100.0
    assert insight.recommendation == "Pattern 'single_success' is highly successful - continue using"

def test_generate_insight_edge_case_single_failure(feedback_loop):
    pattern = "single_failure"
    feedback_loop.patterns[pattern] = {"successes": 0, "occurrences": 1}

    insight = feedback_loop._generate_insight(pattern)

    assert isinstance(insight, LearningInsight)
    assert insight.pattern == "single_failure"
    assert insight.confidence <= 1.0
    assert insight.occurrences == 1
    assert insight.success_rate == 0.0
    assert insight.recommendation == "Pattern 'single_failure' often fails - consider alternative approach"

def test_generate_insight_error_case_invalid_pattern(feedback_loop):
    with pytest.raises(KeyError):
        feedback_loop._generate_insight("nonexistent_pattern")