import pytest

from neural_engine.specialized_systems.model_manager import ModelManager, SystemType

@pytest.fixture
def model_manager():
    return ModelManager(name="test_model", type=SystemType.INTENT_RECOGNITION)

def test_get_stats_happy_path(model_manager):
    # Set up the model manager with some data
    model_manager.total_inference_time = 100
    model_manager.usage_count = 5
    model_manager.metadata = {"version": "1.0"}

    expected_stats = {
        "name": "test_model",
        "type": "INTENT_RECOGNITION",
        "usage_count": 5,
        "total_time": 100,
        "avg_inference_time": 20,
        "metadata": {"version": "1.0"}
    }

    assert model_manager.get_stats() == expected_stats

def test_get_stats_empty_usage(model_manager):
    # Set up the model manager with empty usage data
    model_manager.total_inference_time = 0
    model_manager.usage_count = 0
    model_manager.metadata = {}

    expected_stats = {
        "name": "test_model",
        "type": "INTENT_RECOGNITION",
        "usage_count": 0,
        "total_time": 0,
        "avg_inference_time": 0,
        "metadata": {}
    }

    assert model_manager.get_stats() == expected_stats

def test_get_stats_with_metadata(model_manager):
    # Set up the model manager with metadata
    model_manager.total_inference_time = 250
    model_manager.usage_count = 10
    model_manager.metadata = {"version": "2.0", "author": "noogh"}

    expected_stats = {
        "name": "test_model",
        "type": "INTENT_RECOGNITION",
        "usage_count": 10,
        "total_time": 250,
        "avg_inference_time": 25,
        "metadata": {"version": "2.0", "author": "noogh"}
    }

    assert model_manager.get_stats() == expected_stats

def test_get_stats_no_metadata(model_manager):
    # Set up the model manager without metadata
    model_manager.total_inference_time = 300
    model_manager.usage_count = 6
    model_manager.metadata = {}

    expected_stats = {
        "name": "test_model",
        "type": "INTENT_RECOGNITION",
        "usage_count": 6,
        "total_time": 300,
        "avg_inference_time": 50,
        "metadata": {}
    }

    assert model_manager.get_stats() == expected_stats

def test_get_stats_zero_avg_time(model_manager):
    # Set up the model manager with zero usage count
    model_manager.total_inference_time = 150
    model_manager.usage_count = 0
    model_manager.metadata = {}

    expected_stats = {
        "name": "test_model",
        "type": "INTENT_RECOGNITION",
        "usage_count": 0,
        "total_time": 150,
        "avg_inference_time": 0,
        "metadata": {}
    }

    assert model_manager.get_stats() == expected_stats