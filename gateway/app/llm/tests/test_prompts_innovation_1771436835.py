import pytest

# Mocking the constants used in the function
PERSONA_ARCHITECT = "Architect Persona"
PERSONA_CLI = "CLI Persona"
PERSONA_HUNTER = "Hunter Persona"
SYSTEM_BASE = "System Base"

def get_persona_prompt(persona_name: str) -> str:
    persona_map = {"architect": PERSONA_ARCHITECT, "cli": PERSONA_CLI, "hunter": PERSONA_HUNTER}
    return persona_map.get(persona_name.lower(), SYSTEM_BASE)

# Test cases
def test_get_persona_prompt_architect():
    assert get_persona_prompt("architect") == PERSONA_ARCHITECT

def test_get_persona_prompt_cli():
    assert get_persona_prompt("cli") == PERSONA_CLI

def test_get_persona_prompt_hunter():
    assert get_persona_prompt("hunter") == PERSONA_HUNTER

def test_get_persona_prompt_case_insensitive():
    assert get_persona_prompt("ArChItEcT") == PERSONA_ARCHITECT

def test_get_persona_prompt_default():
    assert get_persona_prompt("unknown") == SYSTEM_BASE

def test_get_persona_prompt_empty_string():
    assert get_persona_prompt("") == SYSTEM_BASE

def test_get_persona_prompt_none():
    assert get_persona_prompt(None) == SYSTEM_BASE

def test_get_persona_prompt_invalid_type():
    with pytest.raises(AttributeError):
        get_persona_prompt(123)

def test_get_persona_prompt_whitespace_only():
    assert get_persona_prompt("   ") == SYSTEM_BASE

def test_get_persona_prompt_mixed_case():
    assert get_persona_prompt("HuNtEr") == PERSONA_HUNTER