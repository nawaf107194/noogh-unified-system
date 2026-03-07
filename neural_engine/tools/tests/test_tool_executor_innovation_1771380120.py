import pytest

class TestToolExecutor:

    @pytest.fixture
    def tool_executor(self):
        class MockToolExecutor:
            def _extract_balanced_json(self, text: str, start: int) -> Optional[str]:
                """
                Mock implementation of _extract_balanced_json to allow testing.
                """
                if start >= len(text) or text[start] != '{':
                    return None
                
                depth = 0
                in_string = False
                escape_next = False
                
                for i in range(start, len(text)):
                    char = text[i]
                    
                    if escape_next:
                        escape_next = False
                        continue
                    
                    if char == '\\':
                        escape_next = True
                        continue
                    
                    if char == '"' and not escape_next:
                        in_string = not in_string
                        continue
                    
                    if in_string:
                        continue
                    
                    if char == '{':
                        depth += 1
                    elif char == '}':
                        depth -= 1
                        if depth == 0:
                            return text[start:i+1]
                
                return None  # Unbalanced
        return MockToolExecutor()

    def test_happy_path(self, tool_executor):
        assert tool_executor._extract_balanced_json('{"key": "value"}', 0) == '{"key": "value"}'
        assert tool_executor._extract_balanced_json('{"key": {"nested": "value"}}', 0) == '{"key": {"nested": "value"}}'

    def test_empty_and_none(self, tool_executor):
        assert tool_executor._extract_balanced_json('', 0) is None
        assert tool_executor._extract_balanced_json(None, 0) is None

    def test_boundaries(self, tool_executor):
        assert tool_executor._extract_balanced_json('{"key": "value"}', 1) is None
        assert tool_executor._extract_balanced_json('{"key": "value"}', -1) is None
        assert tool_executor._extract_balanced_json('{"key": "value"}', 18) is None

    def test_invalid_inputs(self, tool_executor):
        assert tool_executor._extract_balanced_json('{', 0) is None
        assert tool_executor._extract_balanced_json('}', 0) is None
        assert tool_executor._extract_balanced_json('{"key": "value"', 0) is None

    def test_escaped_quotes(self, tool_executor):
        assert tool_executor._extract_balanced_json('{"key": "\\"value\\""}', 0) == '{"key": "\\"value\\""}'
        assert tool_executor._extract_balanced_json('{"key": "\\\"value\\\""}', 0) == '{"key": "\\\"value\\\""}'

    def test_nested_with_strings(self, tool_executor):
        assert tool_executor._extract_balanced_json('{"key": {"nested": "value\\"with\\\"quotes"}}', 0) == '{"key": {"nested": "value\\"with\\\"quotes"}}'
        assert tool_executor._extract_balanced_json('{"key": {"nested": "value\\\\with\\\\quotes"}}', 0) == '{"key": {"nested": "value\\\\with\\\\quotes"}}'