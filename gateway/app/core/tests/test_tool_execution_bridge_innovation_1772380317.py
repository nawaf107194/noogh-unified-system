import pytest
import re
from typing import List, Dict, Any

class ToolExecutionBridgeMock:
    def _extract_tool_calls(self, text: str) -> List[Dict[str, Any]]:
        """
        Regex search for tool calls.
        Prioritizes structured formats over plain markers.
        """
        calls = []
        
        # Combined regex to find all ACT: markers and their associated info
        # Format 1: ACT: tool(args)
        # Format 2: ACT: tool {json}
        # Format 3: ACT: tool
        
        # We search once for all ACT: markers and use the most specific match
        # To avoid duplicates, we'll find all ACT: occurrences and then parse them.
        
        marker_matches = list(re.finditer(r"(ACT|ACTION):\s*([a-zA-Z0-9_\.]+)", text, re.IGNORECASE))
        
        for match in marker_matches:
            name = match.group(2)
            start_pos = match.end()
            remaining = text[start_pos:start_pos + 1000].strip() # Look ahead
            
            params = {}
            # Check for immediate (args)
            if remaining.startswith("("):
                # Try to find matching )
                end_paren = remaining.find(")")
                if end_paren != -1:
                    args_raw = remaining[1:end_paren]
                    # Simple k=v parser
                    for pair in args_raw.split(","):
                        if "=" in pair:
                            k, v = pair.split("=", 1)
                            params[k.strip()] = v.strip().strip("'\"")
            
            # Check for immediate {json}
            elif remaining.startswith("{"):
                # Try to find matching }
                end_json = remaining.find("}")
                if end_json != -1:
                    import json
                    try:
                        params = json.loads(remaining[:end_json+1])
                    except:
                        pass
            
            calls.append({"name": name, "params": params})
        
        return calls

def test_extract_tool_calls_happy_path():
    bridge = ToolExecutionBridgeMock()
    text = "ACT: exampleTool(arg1=value1, arg2=value2) ACT: jsonTool {\"key\": \"value\"} ACT: simpleTool"
    expected_output = [
        {"name": "exampleTool", "params": {"arg1": "value1", "arg2": "value2"}},
        {"name": "jsonTool", "params": {"key": "value"}},
        {"name": "simpleTool", "params": {}}
    ]
    assert bridge._extract_tool_calls(text) == expected_output

def test_extract_tool_calls_empty_input():
    bridge = ToolExecutionBridgeMock()
    text = ""
    expected_output = []
    assert bridge._extract_tool_calls(text) == expected_output

def test_extract_tool_calls_none_input():
    bridge = ToolExecutionBridgeMock()
    text = None
    expected_output = []
    assert bridge._extract_tool_calls(text) == expected_output

def test_extract_tool_calls_boundary_case():
    bridge = ToolExecutionBridgeMock()
    text = "ACT:tool(arg1=value1) ACT:tool(arg2=value2) ACT:"
    expected_output = [
        {"name": "tool", "params": {"arg1": "value1"}},
        {"name": "tool", "params": {"arg2": "value2"}}
    ]
    assert bridge._extract_tool_calls(text) == expected_output

def test_extract_tool_calls_invalid_json():
    bridge = ToolExecutionBridgeMock()
    text = "ACT: tool {\"invalid\": json}"
    expected_output = [{"name": "tool", "params": {"invalid": "json"}}]
    assert bridge._extract_tool_calls(text) == expected_output