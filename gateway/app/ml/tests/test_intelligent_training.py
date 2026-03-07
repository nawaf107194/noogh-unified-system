import pytest
from datetime import datetime
from typing import Dict, Any
from gateway.app.ml.intelligent_training import TrainingConfig, TrainingResult, IntelligentTrainingClass

class MockIntelligentTrainingClass(IntelligentTrainingClass):
    async def _evaluate_and_learn(self, config, metrics, hw_config, training_time):
        return await super()._evaluate_and_learn(config, metrics, hw_config, training_time)

@pytest.fixture
def mock_intelligent_training_class():
    return MockIntelligentTrainingClass()

@pytest.fixture
def sample_config():
    return TrainingConfig(output_dir="model_output")

@pytest.fixture
def sample_metrics():
    return {"eval_loss": 0.1, "train_loss": 0.09}

@pytest.fixture
def sample_hw_config():
    return {"gpu_available": True, "gpu_name": "NVIDIA RTX 3080"}

@pytest.fixture
def sample_training_time():
    return 250.0

@pytest.mark.asyncio
async def test_evaluate_and_learn_happy_path(mock_intelligent_training_class, sample_config, sample_metrics, sample_hw_config, sample_training_time):
    result = await mock_intelligent_training_class._evaluate_and_learn(sample_config, sample_metrics, sample_hw_config, sample_training_time)
    assert result.metrics == sample_metrics
    assert result.hardware_used == sample_hw_config
    assert result.training_time == sample_training_time
    assert "✅ Good generalization (no overfitting)" in result.improvements
    assert "✅ Fast training" in result.improvements
    assert f"✅ Used GPU: {sample_hw_config['gpu_name']}" in result.improvements
    assert result.timestamp is not None

@pytest.mark.asyncio
async def test_evaluate_and_learn_edge_cases(mock_intelligent_training_class, sample_config, sample_metrics, sample_hw_config):
    # Empty metrics
    empty_metrics = {}
    with pytest.raises(KeyError):
        await mock_intelligent_training_class._evaluate_and_learn(sample_config, empty_metrics, sample_hw_config, 250.0)

    # None metrics
    none_metrics = None
    with pytest.raises(TypeError):
        await mock_intelligent_training_class._evaluate_and_learn(sample_config, none_metrics, sample_hw_config, 250.0)

    # Boundary training time (exactly 5 minutes)
    boundary_training_time = 300.0
    result = await mock_intelligent_training_class._evaluate_and_learn(sample_config, sample_metrics, sample_hw_config, boundary_training_time)
    assert "⏱️ Consider smaller model or dataset" in result.improvements

@pytest.mark.asyncio
async def test_evaluate_and_learn_error_cases(mock_intelligent_training_class, sample_config, sample_metrics, sample_hw_config):
    # Invalid training time (negative value)
    invalid_training_time = -100.0
    with pytest.raises(ValueError):
        await mock_intelligent_training_class._evaluate_and_learn(sample_config, sample_metrics, sample_hw_config, invalid_training_time)

    # Overfitting case
    overfitting_metrics = {"eval_loss": 0.2, "train_loss": 0.09}
    result = await mock_intelligent_training_class._evaluate_and_learn(sample_config, overfitting_metrics, sample_hw_config, 250.0)
    assert "⚠️ Possible overfitting detected" in result.improvements

@pytest.mark.asyncio
async def test_evaluate_and_learn_async_behavior(mock_intelligent_training_class, sample_config, sample_metrics, sample_hw_config, sample_training_time):
    # Ensure the method is awaited and behaves asynchronously
    loop = asyncio.get_event_loop()
    start_time = loop.time()
    result = await mock_intelligent_training_class._evaluate_and_learn(sample_config, sample_metrics, sample_hw_config, sample_training_time)
    end_time = loop.time()
    assert result.timestamp is not None
    assert abs(float(result.timestamp) - start_time) < 0.01  # Assuming timestamp is captured at the beginning of the method