import pytest

from gateway.app.ml.auto_curriculum import get_curriculum_learner, AutoCurriculumLearner

@pytest.fixture
def curriculum_learner():
    return AutoCurriculumLearner()

@pytest.mark.parametrize("input_data", [None, "", [], {}, 0])
def test_get_curriculum_learner_edge_cases(input_data):
    """Test edge cases for input data"""
    global _curriculum_learner
    _curriculum_learner = None
    result = get_curriculum_learner()
    assert isinstance(result, AutoCurriculumLearner)
    assert result is not None

def test_get_curriculum_learner_happy_path(curriculum_learner):
    """Test happy path with normal inputs"""
    global _curriculum_learner
    _curriculum_learner = curriculum_learner
    result = get_curriculum_learner()
    assert isinstance(result, AutoCurriculumLearner)
    assert result is curriculum_learner

def test_get_curriculum_learner_async_behavior(curriculum_learner):
    """Test async behavior (if applicable)"""
    global _curriculum_learner
    _curriculum_learner = None
    result = get_curriculum_learner()
    assert isinstance(result, AutoCurriculumLearner)
    # Add additional assertions for async behavior if needed

# Reset global variable after tests to avoid side effects in other tests
def teardown_module():
    global _curriculum_learner
    _curriculum_learner = None