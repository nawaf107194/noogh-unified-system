import pytest
from unittest.mock import patch, MagicMock
from pathlib import Path
from datetime import datetime
import time
import json

from eval_student import evaluate_model

# Mock constants and variables
EVAL_PROMPTS = [
    {"category": "code", "prompt": "def add(a, b): return a + b", "criteria": ["correct"]},
    {"category": "design", "prompt": "What is the purpose of OOP?", "criteria": ["define_oop"]}
]

EVAL_DIR = Path("/home/noogh/projects/noogh_unified_system/eval_results")

# Mocking NeuralEngineClient
class MockNeuralEngineClient:
    def __init__(self, *args, **kwargs):
        pass

    async def complete(self, messages, max_tokens=1024):
        return {"success": True, "content": "Correct response"}

@pytest.fixture
def mock_client():
    with patch('eval_student.NeuralEngineClient', new_callable=MockNeuralEngineClient) as mock:
        yield mock

# Happy path test (normal inputs)
def test_evaluate_model_happy_path(mock_client):
    result = evaluate_model(model_url="http://test-model.com", model_mode="api")
    assert "error" not in result
    assert len(result["categories"]) == 2
    assert result["overall_score"] >= 0 and result["overall_score"] <= 1

# Edge case test (empty EVAL_PROMPTS)
def test_evaluate_model_empty_prompts(mock_client):
    global EVAL_PROMPTS
    original_eval_prompts = EVAL_PROMPTS
    EVAL_PROMPTS = []
    with pytest.raises(Exception) as exc_info:
        evaluate_model()
    assert "No evaluation prompts specified" in str(exc_info.value)
    EVAL_PROMPTS = original_eval_prompts

# Edge case test (None model_url and model_mode)
def test_evaluate_model_none_inputs(mock_client):
    result = evaluate_model(model_url=None, model_mode=None)
    assert "error" not in result
    assert result["model_url"] == os.getenv("NEURAL_ENGINE_URL", "http://localhost:8080")
    assert result["model_mode"] == os.getenv("NEURAL_ENGINE_MODE", "local")

# Error case test (client creation fails)
def test_evaluate_model_client_creation_error():
    with patch('eval_student.NeuralEngineClient', side_effect=Exception("Failed to create client")) as mock:
        result = evaluate_model()
        assert "error" in result
        assert result["error"] == "Cannot create client: Failed to create client"

# Async behavior test (mocking asyncio.get_event_loop)
def test_evaluate_model_async_behavior(mock_client):
    with patch('eval_student.asyncio.get_event_loop') as mock_get_event_loop:
        mock_get_event_loop.return_value.run_until_complete = MagicMock(return_value={"success": True, "content": "Correct response"})
        result = evaluate_model()
        assert "error" not in result
        assert len(result["categories"]) == 2

# Test saving results to file
def test_evaluate_model_saving_results(mock_client):
    result = evaluate_model(model_url="http://test-model.com", model_mode="api")
    eval_file = EVAL_DIR / f"eval_{int(time.time())}.json"
    assert eval_file.exists()
    with open(eval_file, 'r', encoding='utf-8') as f:
        saved_result = json.load(f)
    assert result == saved_result