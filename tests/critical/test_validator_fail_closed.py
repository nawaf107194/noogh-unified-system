"""
Test Tool Validator Fail-Closed Enforcement
Critical security test: Verify system crashes if validator unavailable.
"""
import pytest
import sys
from unittest.mock import patch


def test_tool_executor_crashes_without_validator():
    """
    CRITICAL SECURITY TEST:
    Verify that ToolExecutor refuses to parse tool calls if validator is missing.
    
    This prevents the dangerous fail-open behavior where tools would
    execute with unvalidated, potentially malicious arguments.
    """
    # Simulate validator import failure
    with patch.dict(sys.modules, {'neural_engine.tools.tool_validator': None}):
        with pytest.raises(ImportError) as exc_info:
            # Force reload to trigger import
            if 'neural_engine.tools.tool_executor' in sys.modules:
                del sys.modules['neural_engine.tools.tool_executor']
            
            from neural_engine.tools.tool_executor import ToolExecutor
            
            # Try to extract tool calls (should crash during import)
            executor = ToolExecutor()
            executor.extract_tool_calls('{"tool_name": "test", "arguments": {}}')
        
        # Verify error message is clear
        error_msg = str(exc_info.value).lower()
        assert "validator" in error_msg or "tool_validator" in error_msg, \
            f"Expected validator-related ImportError, got: {exc_info.value}"


def test_tool_executor_works_with_validator():
    """
    Verify that ToolExecutor works normally when validator is available.
    """
    try:
        from neural_engine.tools.tool_executor import ToolExecutor
        from neural_engine.tools.tool_validator import validate_tool_args
        
        # Should work fine
        executor = ToolExecutor()
        
        # Validate function should exist
        assert validate_tool_args is not None
        
    except ImportError as e:
        pytest.fail(f"ToolExecutor should work when validator is available: {e}")


def test_validator_enforcement_is_mandatory():
    """
    Verify validator is always imported unconditionally.
    """
    from neural_engine.tools.tool_validator import (
        validate_tool_args,
        ValidationError,
    )
    
    # Should always be available
    assert validate_tool_args is not None
    assert ValidationError is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
