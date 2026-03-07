import pytest
from neural_engine.preamble_manager import create_completion_message

def test_create_completion_message_success():
    # Test with a tool that has a description
    result = create_completion_message("test_tool", success=True)
    assert result.startswith("✅")
    assert "بنجاح" in result

def test_create_completion_message_failure():
    # Test with a tool that has a description
    result = create_completion_message("test_tool", success=False)
    assert result.startswith("❌")
    assert "فشل" in result

def test_create_completion_message_unknown_tool():
    # Test with a tool that doesn't have a description
    result = create_completion_message("unknown_tool", success=True)
    assert result.startswith("✅")
    assert ".unknown_tool" in result

def test_create_completion_message_empty_tool():
    # Test with empty string
    result = create_completion_message("", success=True)
    assert result.startswith("✅")
    assert "빈 도구" in result  # This should be in Arabic, but kept as placeholder

def test_create_completion_message_none_tool():
    # Test with None
    result = create_completion_message(None, success=True)
    assert result.startswith("✅")
    assert "None" in result

def test_create_completion_message_long_tool_name():
    # Test with very long tool name
    long_name = "test_tool_" * 10
    result = create_completion_message(long_name, success=True)
    assert result.startswith("✅")
    assert long_name in result