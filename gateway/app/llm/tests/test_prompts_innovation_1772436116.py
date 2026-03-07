import pytest

from gateway.app.llm.prompts import get_persona_prompt, PERSONA_ARCHITECT, PERSONA_CLI, PERSONA_HUNTER, SYSTEM_BASE

def test_get_persona_prompt_happy_path():
    assert get_persona_prompt("architect") == PERSONA_ARCHITECT
    assert get_persona_prompt("CLI") == PERSONA_CLI
    assert get_persona_prompt("hunter") == PERSONA_HUNTER

def test_get_persona_prompt_edge_cases():
    assert get_persona_prompt("") is None
    assert get_persona_prompt(None) is None
    assert get_persona_prompt(" ") is None
    assert get_persona_prompt("\t") is None
    assert get_persona_prompt("\n") is None

def test_get_persona_prompt_error_cases():
    assert get_persona_prompt("invalid_personas") == SYSTEM_BASE
    assert get_persona_prompt("  invalid personas  ") == SYSTEM_BASE

# If the function is supposed to handle async behavior, tests would go here
# However, based on the provided code snippet, there's no indication of async handling.