import pytest
from unified_core.orchestration.agent_worker import AgentWorker, _LLM_MODEL, _VLLM_URL
import urllib.request
import json

@pytest.fixture
def agent_worker():
    return AgentWorker()

def test_ask_brain_happy_path(agent_worker):
    prompt = "Hello, how are you?"
    result = agent_worker._ask_brain(prompt)
    assert isinstance(result, str)

def test_ask_brain_empty_prompt(agent_worker):
    prompt = ""
    result = agent_worker._ask_brain(prompt)
    assert result == ""

def test_ask_brain_none_prompt(agent_worker):
    result = agent_worker._ask_brain(None)
    assert result == ""

def test_ask_brain_large_max_tokens(agent_worker):
    max_tokens = 1000
    result = agent_worker._ask_brain("Prompt", max_tokens=max_tokens)
    assert isinstance(result, str)

def test_ask_brain_invalid_prompt_type(agent_worker):
    prompt = 12345
    result = agent_worker._ask_brain(prompt)
    assert result == ""

def test_ask_brain_large_max_tokens_out_of_range(agent_worker):
    max_tokens = 4097
    result = agent_worker._ask_brain("Prompt", max_tokens=max_tokens)
    assert isinstance(result, str)

def test_ask_brain_request_timeout(mocker, agent_worker):
    mocker.patch('urllib.request.urlopen', side_effect=urllib.error.URLError("timed out"))
    result = agent_worker._ask_brain("Prompt")
    assert result == ""

def test_ask_brain_request_error(mocker, agent_worker):
    mocker.patch('urllib.request.urlopen', side_effect=urllib.error.HTTPError(400, "Bad Request", None, None, None))
    result = agent_worker._ask_brain("Prompt")
    assert result == ""