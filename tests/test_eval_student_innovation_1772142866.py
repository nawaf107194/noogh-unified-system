import pytest
from unittest.mock import patch, MagicMock
from eval_student import evaluate_model, EVAL_DIR

# Mocks for testing
EVAL_PROMPTS = [
    {"category": "math", "prompt": "What is 2 + 2?", "criteria": ["accuracy"]},
    {"category": "english", "prompt": "Translate 'Hello' to French.", "criteria": ["correctness"]}
]

class MockNeuralEngineClient:
    def __init__(self, base_url="http://localhost:8080", mode="local"):
        pass
    
    async def complete(self, messages, max_tokens=1024):
        if messages[1]["content"] == "What is 2 + 2?":
            return {"success": True, "content": "4"}
        elif messages[1]["content"] == "Translate 'Hello' to French.":
            return {"success": True, "content": "Bonjour"}
        else:
            return {"success": False}

def test_evaluate_model_happy_path():
    with patch('eval_student.NeuralEngineClient', side_effect=MockNeuralEngineClient):
        result = evaluate_model(model_url="http://localhost:8080", model_mode="local")
        assert "error" not in result
        assert "overall_score" in result
        assert result["categories"]["math"]["score"] == 1.0
        assert result["categories"]["english"]["score"] == 1.0

def test_evaluate_model_empty_prompts():
    with patch('eval_student.NeuralEngineClient', side_effect=MockNeuralEngineClient):
        EVAL_PROMPTS.clear()
        result = evaluate_model(model_url="http://localhost:8080", model_mode="local")
        assert "error" not in result
        assert "overall_score" in result
        assert result["categories"] == {}
        assert result["responses"] == []

def test_evaluate_model_none_inputs():
    with patch('eval_student.NeuralEngineClient', side_effect=MockNeuralEngineClient):
        result = evaluate_model(model_url=None, model_mode=None)
        assert "error" not in result
        assert "overall_score" in result

def test_evaluate_model_invalid_model_mode():
    with patch('eval_student.NeuralEngineClient', side_effect=MockNeuralEngineClient):
        result = evaluate_model(model_url="http://localhost:8080", model_mode="invalid")
        assert "error" in result
        assert result["error"] == "Cannot create client: No module named 'unified_core.neural_bridge'"

def test_evaluate_model_async_behavior():
    with patch('eval_student.NeuralEngineClient', side_effect=MockNeuralEngineClient):
        with patch('asyncio.get_event_loop') as mock_get_event_loop:
            mock_loop = MagicMock()
            mock_loop.run_until_complete.return_value = {"success": True, "content": "4"}
            mock_get_event_loop.return_value = mock_loop
            result = evaluate_model(model_url="http://localhost:8080", model_mode="local")
            assert "error" not in result
            assert result["categories"]["math"]["score"] == 1.0