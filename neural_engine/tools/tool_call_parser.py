"""
Canonical Tool Call Format - JSON-based (Phase 2.C)
Standardizes tool call format for easier parsing
"""

import json
import re
from typing import Dict, List, Tuple, Any, Optional


class ToolCallParser:
    """Parse tool calls in canonical JSON format"""
    
    # Primary format: {"tool":"name","args":{...}} - Supports multi-line and whitespace
    JSON_PATTERN = re.compile(r'\{\s*\"(?:tool|tool_name)\"\s*:\s*\"([^\"]+)\"\s*,\s*\"(?:args|arguments)\"\s*:\s*(\{.*?\})\s*\}', re.DOTALL)
    
    # Legacy format: [TOOL: name(args)] for backward compatibility
    LEGACY_PATTERN = re.compile(r'\[TOOL:\s*(\w+)\s*\((.*?)\)\]')
    
    # Natural language format: uses tool 'name': {"key":"val"} or يستخدم أداة name: {"key":"val"}
    NATURAL_PATTERN = re.compile(
        r"""(?:uses?\s+tool|يستخدم\s+(?:أداة|اداة))\s*['\"]?(\w[\w.]*)['\"]?\s*:\s*(\{[^}]*\})""",
        re.IGNORECASE
    )
    
    @staticmethod
    def parse_json_call(text: str) -> List[Tuple[str, Dict[str, Any]]]:
        """
        Parse JSON tool calls
        Format: {"tool":"read_file","args":{"path":"/tmp/a.txt"}}
        
        Returns:
            List of (tool_name, args_dict) tuples
        """
        calls = []
        
        for match in ToolCallParser.JSON_PATTERN.finditer(text):
            try:
                tool_name = match.group(1)
                args_json = match.group(2)
                args = json.loads(args_json)
                calls.append((tool_name, args))
            except json.JSONDecodeError:
                continue
        
        return calls
    
    @staticmethod
    def parse_natural_call(text: str) -> List[Tuple[str, Dict[str, Any]]]:
        """
        Parse natural language tool calls from the model.
        Format: uses tool 'sys.execute': {"command": "ls -la"}
        """
        calls = []
        
        for match in ToolCallParser.NATURAL_PATTERN.finditer(text):
            try:
                tool_name = match.group(1)
                args_json = match.group(2)
                args = json.loads(args_json)
                calls.append((tool_name, args))
            except json.JSONDecodeError:
                continue
        
        return calls
    
    @staticmethod
    def parse_legacy_call(text: str) -> List[Tuple[str, Dict[str, Any]]]:
        """
        Parse legacy tool calls for backward compatibility
        Format: [TOOL: read_file(path='/tmp/a.txt')]
        """
        calls = []
        
        for match in ToolCallParser.LEGACY_PATTERN.finditer(text):
            tool_name = match.group(1)
            args_str = match.group(2)
            
            # Simple key=value parsing
            args = {}
            if args_str:
                for part in args_str.split(','):
                    if '=' in part:
                        key, val = part.split('=', 1)
                        key = key.strip()
                        val = val.strip().strip('\'"')
                        args[key] = val
            
            calls.append((tool_name, args))
        
        return calls
    
    @staticmethod
    def parse(text: str) -> List[Tuple[str, Dict[str, Any]]]:
        """
        Parse tool calls in any supported format
        Tries JSON first, then natural language, falls back to legacy
        """
        # Try JSON format first (preferred)
        json_calls = ToolCallParser.parse_json_call(text)
        if json_calls:
            return json_calls
        
        # Try natural language format
        natural_calls = ToolCallParser.parse_natural_call(text)
        if natural_calls:
            return natural_calls
        
        # Fallback to legacy
        return ToolCallParser.parse_legacy_call(text)
    
    @staticmethod
    def format_call(tool_name: str, args: Dict[str, Any]) -> str:
        """
        Format a tool call in canonical JSON format
        
        Args:
            tool_name: Name of the tool
            args: Arguments dictionary
            
        Returns:
            JSON-formatted tool call string
        """
        return json.dumps({"tool": tool_name, "args": args}, ensure_ascii=False)
    
    @staticmethod
    def extract_and_validate(text: str) -> Tuple[List[Tuple[str, Dict]], List[str]]:
        """
        Extract tool calls and validate them
        
        Returns:
            (valid_calls, errors)
        """
        calls = ToolCallParser.parse(text)
        valid_calls = []
        errors = []
        
        for tool_name, args in calls:
            # Basic validation
            if not tool_name or not isinstance(tool_name, str):
                errors.append(f"Invalid tool name: {tool_name}")
                continue
            
            if not isinstance(args, dict):
                errors.append(f"Invalid args for {tool_name}: {args}")
                continue
            
            valid_calls.append((tool_name, args))
        
        return valid_calls, errors


# Example usage in training data format — aligned with identity v13.0
CANONICAL_EXAMPLES = [
    {
        "user": "اقرأ ملف config.json",
        "assistant": '{"tool":"fs.read","args":{"path":"config.json"}}'
    },
    {
        "user": "نفّذ الأمر ls",
        "assistant": '{"tool":"sys.execute","args":{"command":"ls -la"}}'
    },
    {
        "user": "احصل على حالة النظام",
        "assistant": '{"tool":"sys.info","args":{}}'
    },
    {
        "user": "اكتب ملف /tmp/test.txt بالمحتوى hello",
        "assistant": '{"tool":"fs.write","args":{"path":"/tmp/test.txt","content":"hello"}}'
    },
    {
        "user": "ابحث عن docker في الذاكرة",
        "assistant": '{"tool":"mem.search","args":{"query":"docker"}}'
    }
]
