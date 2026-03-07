import pytest

# Assuming the constants are defined somewhere in the module
from gateway.app.llm.prompts import PERSONA_ARCHITECT, PERSONA_CLI, PERSONA_HUNTER, SYSTEM_BASE

@pytest.fixture
def setup_constants():
    global PERSONA_ARCHITECT, PERSONA_CLI, PERSONA_HUNTER, SYSTEM_BASE
    PERSONA_ARCHITECT = "You are an Architect."
    PERSONA_CLI = "You are a CLI tool."
    PERSONA_HUNTER = "You are a Hunter."
    SYSTEM_BASE = "You are the System Base."

def test_get_persona_prompt_architect(setup_constants):
    assert get_persona_prompt("Architect") == "You are an Architect."

def test_get_persona_prompt_cli(setup_constants):
    assert get_persona_prompt("CLI") == "You are a CLI tool."

def test_get_persona_prompt_hunter(setup_constants):
    assert get_persona_prompt("Hunter") == "You are a Hunter."

def test_get_persona_prompt_unknown(setup_constants):
    assert get_persona_prompt("unknown") == "You are the System Base."

def test_get_persona_prompt_empty_string(setup_constants):
    assert get_persona_prompt("") == "You are the System Base."

def test_get_persona_prompt_none(setup_constants):
    assert get_persona_prompt(None) == "You are the System Base."

def test_get_persona_prompt_case_insensitive(setup_constants):
    assert get_persona_prompt("ARCHITECT") == "You are an Architect."

def test_get_persona_prompt_with_spaces(setup_constants):
    assert get_persona_prompt("  hunter  ") == "You are a Hunter."

def test_get_persona_prompt_special_characters(setup_constants):
    assert get_persona_prompt("!@#$%^&*()") == "You are the System Base."

def test_get_persona_prompt_numeric_input(setup_constants):
    assert get_persona_prompt("12345") == "You are the System Base."