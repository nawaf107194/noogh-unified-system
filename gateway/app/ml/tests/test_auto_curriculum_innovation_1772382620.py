import pytest

from gateway.app.ml.auto_curriculum import get_curriculum_learner, AutoCurriculumLearner

@pytest.fixture(scope="module")
def curriculum_learner():
    return AutoCurriculumLearner()

def test_get_curriculum_learner_happy_path(curriculum_learner):
    """Test the happy path where the learner is successfully retrieved."""
    global _curriculum_learner
    _curriculum_learner = None

    learner = get_curriculum_learner()
    assert isinstance(learner, AutoCurriculumLearner)
    assert learner == curriculum_learner

def test_get_curriculum_learner_cache(curriculum_learner):
    """Test that the same learner is returned on subsequent calls."""
    global _curriculum_learner
    _curriculum_learner = None

    learner1 = get_curriculum_learner()
    learner2 = get_curriculum_learner()
    assert learner1 == learner2
    assert isinstance(learner1, AutoCurriculumLearner)

def test_get_curriculum_learner_no_global_cache():
    """Test that a new learner is created if no global cache exists."""
    global _curriculum_learner
    _curriculum_learner = None

    learner = get_curriculum_learner()
    assert isinstance(learner, AutoCurriculumLearner)
    assert _curriculum_learner == learner