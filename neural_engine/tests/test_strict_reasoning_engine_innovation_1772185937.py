import pytest

class MockStrictReasoningEngine:
    def _extract_assumptions(self, response): return []
    def _extract_steps(self, response): return []
    def _extract_final_answer(self, response): return ""

def test_happy_path():
    engine = MockStrictReasoningEngine()
    response = "Success: N/A"
    result = engine._parse_response(response)
    assert result == {
        "assumptions": [],
        "steps": [],
        "final_answer": "N/A",
        "is_valid": False,
        "failure_reason": "Success: "
    }

def test_empty_response():
    engine = MockStrictReasoningEngine()
    response = ""
    result = engine._parse_response(response)
    assert result == {
        "assumptions": [],
        "steps": [],
        "final_answer": "",
        "is_valid": False,
        "failure_reason": ""
    }

def test_none_response():
    engine = MockStrictReasoningEngine()
    response = None
    result = engine._parse_response(response)
    assert result is None

def test_boundary_case():
    engine = MockStrictReasoningEngine()
    response = "N/A"
    result = engine._parse_response(response)
    assert result == {
        "assumptions": [],
        "steps": [],
        "final_answer": "N/A",
        "is_valid": False,
        "failure_reason": ""
    }

def test_extract_assumptions_error():
    engine = MockStrictReasoningEngine()
    response = "Error in assumptions"
    with pytest.raises(Exception) as e:
        engine._extract_assumptions(response)

def test_extract_steps_error():
    engine = MockStrictReasoningEngine()
    response = "Error in steps"
    with pytest.raises(Exception) as e:
        engine._extract_steps(response)

def test_extract_final_answer_error():
    engine = MockStrictReasoningEngine()
    response = "Error in final answer"
    with pytest.raises(Exception) as e:
        engine._extract_final_answer(response)