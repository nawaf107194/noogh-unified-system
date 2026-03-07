import pytest
from gateway.app.core.agent_kernel import AgentKernel

def test_sanitize_answer_happy_path():
    agent = AgentKernel()
    input_text = "This is a normal text with sudo rm -rf /etc/ and .env file."
    expected_output = "This is a normal text with [Sudo Blocked] and [Secret Blocked] file."
    assert agent._sanitize_answer(input_text) == expected_output

def test_sanitize_answer_empty_string():
    agent = AgentKernel()
    input_text = ""
    expected_output = ""
    assert agent._sanitize_answer(input_text) == expected_output

def test_sanitize_answer_none_input():
    agent = AgentKernel()
    input_text = None
    expected_output = None
    assert agent._sanitize_answer(input_text) == expected_output

def test_sanitize_answer_patterns_at_boundaries():
    agent = AgentKernel()
    input_text = "Edge case: /etc/passwd and .env at boundaries"
    expected_output = "Edge case: [System Path Blocked] and [Secret Blocked] at boundaries"
    assert agent._sanitize_answer(input_text) == expected_output

def test_sanitize_answer_no_patterns():
    agent = AgentKernel()
    input_text = "No patterns here."
    expected_output = "No patterns here."
    assert agent._sanitize_answer(input_text) == expected_output

def test_sanitize_answer_with_newlines():
    agent = AgentKernel()
    input_text = "This is a normal text\nwith sudo rm -rf /etc/ and .env file.\n"
    expected_output = "This is a normal text\nwith [Sudo Blocked] and [Secret Blocked] file.\n"
    assert agent._sanitize_answer(input_text) == expected_output

def test_sanitize_answer_with_tabs():
    agent = AgentKernel()
    input_text = "This is a normal text\twith sudo rm -rf /etc/ and .env file."
    expected_output = "This is a normal text\twith [Sudo Blocked] and [Secret Blocked] file."
    assert agent._sanitize_answer(input_text) == expected_output