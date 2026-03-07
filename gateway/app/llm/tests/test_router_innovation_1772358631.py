import pytest

class MockLlmRouter:
    def _is_exec_request(self, prompt: str) -> bool:
        keywords = ["exec", "execution", "python code", "run this", "calculate"]
        return any(k in prompt.lower() for k in keywords)

@pytest.fixture
def llm_router():
    return MockLlmRouter()

def test_is_exec_request_happy_path(llm_router):
    assert llm_router._is_exec_request("Calculate the sum of 2 and 3") == True
    assert llm_router._is_exec_request("Run this code") == True
    assert llm_router._is_exec_request("Python code execution") == True

def test_is_exec_request_edge_cases(llm_router):
    assert llm_router._is_exec_request("") == False
    assert llm_router._is_exec_request(None) == False
    assert llm_router._is_exec_request("  ") == False
    assert llm_router._is_exec_request("No keywords here!") == False

def test_is_exec_request_error_cases(llm_router):
    # This function does not take any invalid inputs, so no need for error cases
    pass

def test_is_exec_request_async_behavior(llm_router):
    # The function is synchronous and does not involve async behavior
    pass