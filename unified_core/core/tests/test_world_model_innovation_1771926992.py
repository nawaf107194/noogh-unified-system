import pytest

from unified_core.core.world_model import _prediction_from_dict, Prediction

def test_prediction_from_dict_happy_path():
    data = {
        "prediction_id": "123",
        "based_on_beliefs": True,
        "predicted_outcome": "success",
        "confidence": 0.9,
        "created_at": "2023-04-01T12:00:00Z",
        "resolved": False,
        "was_correct": True
    }
    result = _prediction_from_dict(data)
    assert isinstance(result, Prediction)
    assert result.prediction_id == "123"
    assert result.based_on_beliefs is True
    assert result.predicted_outcome == "success"
    assert result.confidence == 0.9
    assert result.created_at == "2023-04-01T12:00:00Z"
    assert result.resolved is False
    assert result.was_correct is True

def test_prediction_from_dict_empty_data():
    data = {}
    result = _prediction_from_dict(data)
    assert isinstance(result, Prediction)
    assert result.prediction_id is None
    # Add assertions for other default values if applicable

def test_prediction_from_dict_none_input():
    result = _prediction_from_dict(None)
    assert isinstance(result, Prediction)
    assert result.prediction_id is None
    # Add assertions for other default values if applicable

def test_prediction_from_dict_missing_keys():
    data = {
        "invalid_key": "value"
    }
    result = _prediction_from_dict(data)
    assert isinstance(result, Prediction)
    assert result.prediction_id is None
    # Add assertions for other default values if applicable

def test_prediction_from_dict_extra_keys():
    data = {
        "prediction_id": "123",
        "based_on_beliefs": True,
        "predicted_outcome": "success",
        "confidence": 0.9,
        "created_at": "2023-04-01T12:00:00Z",
        "resolved": False,
        "was_correct": True,
        "extra_key": "extra_value"
    }
    result = _prediction_from_dict(data)
    assert isinstance(result, Prediction)
    assert result.prediction_id == "123"
    assert result.based_on_beliefs is True
    assert result.predicted_outcome == "success"
    assert result.confidence == 0.9
    assert result.created_at == "2023-04-01T12:00:00Z"
    assert result.resolved is False
    assert result.was_correct is True

def test_prediction_from_dict_invalid_confidence():
    data = {
        "prediction_id": "123",
        "based_on_beliefs": True,
        "predicted_outcome": "success",
        "confidence": 1.5,  # Invalid confidence value
        "created_at": "2023-04-01T12:00:00Z",
        "resolved": False,
        "was_correct": True
    }
    result = _prediction_from_dict(data)
    assert isinstance(result, Prediction)
    assert result.confidence == 1.0  # Assuming default value is 1.0

def test_prediction_from_dict_invalid_created_at():
    data = {
        "prediction_id": "123",
        "based_on_beliefs": True,
        "predicted_outcome": "success",
        "confidence": 0.9,
        "created_at": "invalid-date",  # Invalid date format
        "resolved": False,
        "was_correct": True
    }
    result = _prediction_from_dict(data)
    assert isinstance(result, Prediction)
    assert result.created_at is None  # Assuming default value is None

# Add more tests as needed for edge cases and error handling