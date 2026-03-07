import pytest

from gateway.app.ml.intelligent_training import TrainingConfig, TrainingResult

@pytest.fixture
def training_config():
    return TrainingConfig(output_dir="test_output")

@pytest.fixture
def hw_config():
    return {"gpu_available": True, "gpu_name": "RTX 3080"}

def test_happy_path(training_config, hw_config):
    metrics = {
        "eval_loss": 0.5,
        "train_loss": 0.6
    }
    training_time = 250

    result = _evaluate_and_learn(training_config, metrics, hw_config, training_time)

    assert isinstance(result, TrainingResult)
    assert result.model_path == "test_output"
    assert result.metrics == metrics
    assert result.hardware_used == hw_config
    assert result.training_time == training_time
    assert len(result.improvements) == 3
    assert "✅ Good generalization (no overfitting)" in result.improvements
    assert "✅ Fast training" in result.improvements
    assert "✅ Used GPU: RTX 3080" in result.improvements

def test_edge_case_empty_metrics(training_config, hw_config):
    metrics = {}
    training_time = 250

    result = _evaluate_and_learn(training_config, metrics, hw_config, training_time)

    assert isinstance(result, TrainingResult)
    assert result.model_path == "test_output"
    assert result.metrics == {}
    assert result.hardware_used == hw_config
    assert result.training_time == training_time
    assert len(result.improvements) == 1
    assert "⚠️ Possible overfitting detected" in result.improvements

def test_edge_case_none_metrics(training_config, hw_config):
    metrics = None
    training_time = 250

    result = _evaluate_and_learn(training_config, metrics, hw_config, training_time)

    assert isinstance(result, TrainingResult)
    assert result.model_path == "test_output"
    assert result.metrics is None
    assert result.hardware_used == hw_config
    assert result.training_time == training_time
    assert len(result.improvements) == 1
    assert "⚠️ Possible overfitting detected" in result.improvements

def test_edge_case_boundary_training_time(training_config, hw_config):
    metrics = {
        "eval_loss": 0.5,
        "train_loss": 0.6
    }
    training_time = 300

    result = _evaluate_and_learn(training_config, metrics, hw_config, training_time)

    assert isinstance(result, TrainingResult)
    assert result.model_path == "test_output"
    assert result.metrics == metrics
    assert result.hardware_used == hw_config
    assert result.training_time == training_time
    assert len(result.improvements) == 2
    assert "✅ Good generalization (no overfitting)" in result.improvements
    assert "⏱️ Consider smaller model or dataset" in result.improvements

def test_error_case_invalid_input_type(training_config, hw_config):
    metrics = "not a dict"
    training_time = 250

    with pytest.raises(ValueError) as exc_info:
        _evaluate_and_learn(training_config, metrics, hw_config, training_time)

    assert str(exc_info.value) == "Invalid input type for metrics: expected dict, got str"

def test_error_case_invalid_input_value(training_config, hw_config):
    metrics = {
        "eval_loss": -1.0,
        "train_loss": 0.6
    }
    training_time = 250

    with pytest.raises(ValueError) as exc_info:
        _evaluate_and_learn(training_config, metrics, hw_config, training_time)

    assert str(exc_info.value) == "Invalid value for eval_loss: must be >= 0"