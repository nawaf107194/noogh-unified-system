import pytest
from pathlib import Path
from typing import Dict

class MockSecrets:
    def __getitem__(self, key):
        return f"secret_{key}"

def create_brain(secrets: Dict[str, str]):
    return MockSecrets()

def test_init_happy_path():
    secrets = {"api_key": "abc123", "model_name": "test_model"}
    data_dir = "/tmp/evaluations"
    evaluator = __init__(secrets, data_dir)
    assert isinstance(evaluator.output_dir, Path)
    assert evaluator.output_dir == Path(data_dir) / "evaluations"
    assert evaluator.secrets == secrets
    assert evaluator.evaluator_llm is not None

def test_init_edge_case_empty_data_dir():
    secrets = {"api_key": "abc123", "model_name": "test_model"}
    data_dir = ""
    with pytest.raises(ValueError) as exc_info:
        __init__(secrets, data_dir)
    assert str(exc_info.value) == "data_dir is required for ModelEvaluator"

def test_init_edge_case_none_data_dir():
    secrets = {"api_key": "abc123", "model_name": "test_model"}
    data_dir = None
    with pytest.raises(ValueError) as exc_info:
        __init__(secrets, data_dir)
    assert str(exc_info.value) == "data_dir is required for ModelEvaluator"

def test_init_async_behavior(mocker):
    secrets = {"api_key": "abc123", "model_name": "test_model"}
    data_dir = "/tmp/evaluations"
    create_brain_mocker = mocker.patch('path_to_create_brain.create_brain', return_value=MockSecrets())
    evaluator = __init__(secrets, data_dir)
    create_brain_mocker.assert_called_once_with(secrets=secrets)