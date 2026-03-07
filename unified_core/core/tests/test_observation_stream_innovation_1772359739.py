import pytest
from unified_core.core.observation_stream import ObservationStream

@pytest.fixture
def observation_stream():
    return ObservationStream(window=60)  # Set a small window for testing purposes

def test_prune_old_happy_path(observation_stream):
    """Test happy path with normal inputs."""
    observation_stream._errors = [time.time() - 59, time.time() - 100]
    observation_stream._successes = [time.time() - 59, time.time() - 100]
    observation_stream._prune_old()
    assert len(observation_stream._errors) == 1
    assert len(observation_stream._successes) == 1

def test_prune_old_empty_lists(observation_stream):
    """Test edge case with empty lists."""
    observation_stream._errors = []
    observation_stream._successes = []
    observation_stream._prune_old()
    assert not observation_stream._errors
    assert not observation_stream._successes

def test_prune_old_none_values(observation_stream):
    """Test edge case with None values."""
    observation_stream._errors = [None, time.time() - 59]
    observation_stream._successes = [None, time.time() - 59]
    observation_stream._prune_old()
    assert len(observation_stream._errors) == 1
    assert len(observation_stream._successes) == 1

def test_prune_old_boundary_values(observation_stream):
    """Test edge case with boundary values."""
    cutoff = time.time() - 60
    observation_stream._errors = [cutoff, cutoff + 1]
    observation_stream._successes = [cutoff, cutoff + 1]
    observation_stream._prune_old()
    assert len(observation_stream._errors) == 1
    assert len(observation_stream._successes) == 1

def test_prune_old_invalid_input(observation_stream):
    """Test error case with invalid input (should not happen as the function does not explicitly raise exceptions)."""
    observation_stream._errors = [time.time() - 59, 'invalid']
    observation_stream._successes = [time.time() - 59, 'invalid']
    observation_stream._prune_old()
    assert len(observation_stream._errors) == 1
    assert len(observation_stream._successes) == 1