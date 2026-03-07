import pytest

class CreativeAgent:
    def set_failure_record(self, fr):
        self._failure_record = fr

def test_set_failure_record_happy_path():
    agent = CreativeAgent()
    fr = {"error": "SyntaxError", "message": "Invalid syntax"}
    agent.set_failure_record(fr)
    assert agent._failure_record == fr

def test_set_failure_record_empty_input():
    agent = CreativeAgent()
    fr = {}
    agent.set_failure_record(fr)
    assert agent._failure_record == fr

def test_set_failure_record_none_input():
    agent = CreativeAgent()
    agent.set_failure_record(None)
    assert agent._failure_record is None

def test_set_failure_record_boundary_input():
    agent = CreativeAgent()
    fr = {"error": "EOFError", "message": "End of file reached"}
    agent.set_failure_record(fr)
    assert agent._failure_record == fr

# Test with invalid input types
def test_set_failure_record_invalid_type_list():
    agent = CreativeAgent()
    fr = ["SyntaxError", "Invalid syntax"]
    agent.set_failure_record(fr)
    assert agent._failure_record is None

def test_set_failure_record_invalid_type_string():
    agent = CreativeAgent()
    fr = "SyntaxError: Invalid syntax"
    agent.set_failure_record(fr)
    assert agent._failure_record is None

def test_set_failure_record_invalid_type_int():
    agent = CreativeAgent()
    fr = 404
    agent.set_failure_record(fr)
    assert agent._failure_record is None

# Test with large input to ensure it handles memory efficiently
def test_set_failure_record_large_input():
    agent = CreativeAgent()
    fr = {"error": "MemoryError", "message": "Out of memory", "data": [i for i in range(10**6)]}
    agent.set_failure_record(fr)
    assert agent._failure_record == fr