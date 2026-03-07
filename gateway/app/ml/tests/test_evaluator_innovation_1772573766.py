import pytest
from pathlib import Path
from typing import Dict
from unittest.mock import patch

@pytest.fixture
def secrets() -> Dict[str, str]:
    return {
        "OPENAI_API_KEY": "fake_key",
        "ANTHROPIC_API_KEY": "fake_anthropic_key"
    }

@pytest.fixture
def data_dir(tmp_path: Path) -> str:
    return str(tmp_path / "data")

def test_happy_path(secrets: Dict[str, str], data_dir: str):
    from evaluator import ModelEvaluator
    evaluator = ModelEvaluator(secrets=secrets, data_dir=data_dir)
    
    assert evaluator.output_dir == Path(data_dir) / "evaluations"
    assert evaluator.output_dir.exists()
    assert evaluator.output_dir.is_dir()
    assert evaluator.evaluator_llm is not None

def test_edge_case_empty_secrets(data_dir: str):
    from evaluator import ModelEvaluator
    evaluator = ModelEvaluator(secrets={}, data_dir=data_dir)
    assert evaluator.output_dir == Path(data_dir) / "evaluations"
    assert evaluator.output_dir.exists()

def test_error_case_empty_data_dir():
    from evaluator import ModelEvaluator
    with pytest.raises(ValueError, match="data_dir is required for ModelEvaluator"):
        ModelEvaluator(secrets={}, data_dir="")

def test_edge_case_data_dir_already_exists(secrets: Dict[str, str], data_dir: str):
    from evaluator import ModelEvaluator
    existing_dir = Path(data_dir) / "evaluations"
    existing_dir.mkdir(parents=True, exist_ok=True)
    
    evaluator = ModelEvaluator(secrets=secrets, data_dir=data_dir)
    assert evaluator.output_dir == existing_dir
    assert evaluator.output_dir.exists()

def test_edge_case_relative_path(secrets: Dict[str, str]):
    from evaluator import ModelEvaluator
    relative_dir = "test_data"
    evaluator = ModelEvaluator(secrets=secrets, data_dir=relative_dir)
    
    assert evaluator.output_dir == Path(relative_dir) / "evaluations"
    assert evaluator.output_dir.exists()