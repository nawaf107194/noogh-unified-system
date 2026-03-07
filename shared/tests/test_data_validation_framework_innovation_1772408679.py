import pytest

from shared.data_validation_framework import create_schema_example

def test_happy_path():
    result = create_schema_example()
    assert isinstance(result, dict)
    assert result == {
        "type": "object",
        "properties": {
            "name": {"type": "string"},
            "age": {"type": "integer", "minimum": 0},
            "email": {"type": "string", "format": "email"}
        },
        "required": ["name", "age"]
    }

def test_edge_cases():
    result = create_schema_example()
    assert isinstance(result, dict)
    assert result.get("properties") is not None
    assert result["properties"]["name"]["type"] == "string"
    assert result["properties"]["age"]["type"] == "integer" and result["properties"]["age"].get("minimum", -1) == 0
    assert result["properties"]["email"]["type"] == "string" and result["properties"]["email"].get("format") == "email"

def test_error_cases():
    # Since the function does not raise specific exceptions, we cannot write error tests for invalid inputs.
    pass

async def test_async_behavior():
    # The function is synchronous, so there's no async behavior to test.
    pass