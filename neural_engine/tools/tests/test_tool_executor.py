import pytest
from typing import List, Tuple, Dict, Any
from unittest.mock import patch, MagicMock
from neural_engine.tools.tool_call_parser import ToolCallParser

@pytest.fixture
def mock_logger():
    with patch('neural_engine.tools.tool_executor.logger') as mock_logger:
        yield mock_logger

@pytest.fixture
def mock_tool_executor():
    class MockToolExecutor:
        max_tool_calls = 5

        def __init__(self):
            self._fix_arabic_paths = MagicMock(return_value={})

        def _extract_json_tool_calls(self, response: str) -> List[Tuple[str, Dict[str, Any]]]:
            try:
                import json
                data = json.loads(response)
                return [(data['tool'], data['args'])] if 'tool' in data and 'args' in data else []
            except json.JSONDecodeError:
                return []

        def _extract_regex_tool_calls(self, response: str) -> List[Tuple[str, Dict[str, Any]]]:
            import re
            matches = re.findall(r'\[TOOL: (\w+)\((.*)\)\]', response)
            return [(match[0], {'prompt': match[1]}) for match in matches]

    return MockToolExecutor()

def test_extract_tool_calls_happy_path(mock_tool_executor, mock_logger):
    response = '{"tool": "get_system_status", "args": {"key": "value"}}'
    result = mock_tool_executor.extract_tool_calls(response)
    assert result == [('get_system_status', {})]
    mock_logger.info.assert_called_once_with("🔧 Extracted 1 tool call(s) via JSON parser")

def test_extract_tool_calls_natural_language(mock_tool_executor, mock_logger):
    ToolCallParser.parse_natural_call = MagicMock(return_value=[('generate_image', {'prompt': 'قطة جميلة'})])
    response = "uses tool 'generate_image': {'prompt': 'قطة جميلة'}"
    result = mock_tool_executor.extract_tool_calls(response)
    assert result == [('generate_image', {})]
    mock_logger.info.assert_called_once_with("🔧 Extracted 1 tool call(s) via natural-language parser")

def test_extract_tool_calls_legacy_regex(mock_tool_executor, mock_logger):
    response = "[TOOL: get_system_status()] [TOOL: generate_image(prompt='قطة جميلة')]"
    result = mock_tool_executor.extract_tool_calls(response)
    assert result == [('get_system_status', {}), ('generate_image', {})]
    mock_logger.warning.assert_called_once_with("⚠️ Using legacy regex parser for 2 tool call(s)")

def test_extract_tool_calls_empty_response(mock_tool_executor, mock_logger):
    response = ""
    result = mock_tool_executor.extract_tool_calls(response)
    assert result == []
    mock_logger.info.assert_not_called()
    mock_logger.warning.assert_not_called()

def test_extract_tool_calls_none_response(mock_tool_executor, mock_logger):
    response = None
    result = mock_tool_executor.extract_tool_calls(response)
    assert result == []
    mock_logger.info.assert_not_called()
    mock_logger.warning.assert_not_called()

def test_extract_tool_calls_invalid_json(mock_tool_executor, mock_logger):
    response = '{"tool": "get_system_status", "args": "invalid"}'
    result = mock_tool_executor.extract_tool_calls(response)
    assert result == []
    mock_logger.info.assert_not_called()
    mock_logger.warning.assert_not_called()

def test_extract_tool_calls_max_tool_calls(mock_tool_executor, mock_logger):
    mock_tool_executor.max_tool_calls = 2
    response = '[TOOL: get_system_status()] [TOOL: generate_image(prompt="قطة جميلة")] [TOOL: another_tool(args="more")]'
    result = mock_tool_executor.extract_tool_calls(response)
    assert len(result) == 2
    mock_logger.warning.assert_called_once_with("⚠️ Using legacy regex parser for 3 tool call(s)")

def test_extract_tool_calls_async_behavior(mock_tool_executor, mock_logger):
    # Assuming async behavior is not implemented in this version of the function
    pass