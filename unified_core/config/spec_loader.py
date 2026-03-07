"""
Tool Mapping Spec Loader - Reads canonical spec and generates validators

This module:
- Loads tool_mapping_spec.json (SOURCE OF TRUTH)
- Validates tool calls against schemas
- Generates dataset samples that comply with spec
- Prevents hallucination at training time

NO tool outside this spec is valid.
"""

import json
import re
from pathlib import Path
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

# Load spec on import
_SPEC_PATH = Path(__file__).parent / "tool_mapping_spec.json"
_SPEC: Optional[Dict] = None


def load_spec() -> Dict:
    """Load the canonical tool mapping spec."""
    global _SPEC
    if _SPEC is None:
        with open(_SPEC_PATH) as f:
            _SPEC = json.load(f)
    return _SPEC


def get_tool_names() -> List[str]:
    """Get all valid tool names from spec."""
    spec = load_spec()
    return list(spec["tools"].keys())


def get_tool_schema(tool_name: str) -> Optional[Dict]:
    """Get schema for a tool."""
    spec = load_spec()
    tool = spec["tools"].get(tool_name)
    if tool:
        return tool.get("schema", {})
    return None


def get_tool_category(tool_name: str) -> Optional[str]:
    """Get category for a tool."""
    spec = load_spec()
    tool = spec["tools"].get(tool_name)
    if tool:
        return tool.get("category")
    return None


def get_allowed_paths(tool_name: str) -> List[str]:
    """Get allowed paths for a filesystem tool."""
    spec = load_spec()
    tool = spec["tools"].get(tool_name)
    if tool:
        return tool.get("allow_paths", [])
    return []


def get_allowed_urls(tool_name: str) -> List[str]:
    """Get allowed URLs for a network tool."""
    spec = load_spec()
    tool = spec["tools"].get(tool_name)
    if tool:
        return tool.get("allow_urls", [])
    return []


def is_pure_function(tool_name: str) -> bool:
    """Check if tool is a pure function (no actuator needed)."""
    spec = load_spec()
    tool = spec["tools"].get(tool_name)
    if tool:
        return tool.get("pure", False) or "implementation" in tool
    return False


def is_valid_tool(tool_name: str) -> bool:
    """Check if tool name is in the spec."""
    spec = load_spec()
    return tool_name in spec["tools"]


@dataclass
class ValidationResult:
    """Result of validating a tool call."""
    valid: bool
    tool_name: str
    errors: List[str]
    warnings: List[str]
    
    def to_dict(self) -> Dict:
        return {
            "valid": self.valid,
            "tool_name": self.tool_name,
            "errors": self.errors,
            "warnings": self.warnings
        }


def validate_tool_call(tool_name: str, arguments: Dict[str, Any]) -> ValidationResult:
    """
    Validate a tool call against the spec.
    
    Returns ValidationResult with errors if invalid.
    """
    errors = []
    warnings = []
    
    # 1. Check tool exists
    if not is_valid_tool(tool_name):
        return ValidationResult(
            valid=False,
            tool_name=tool_name,
            errors=[f"HALLUCINATION: Tool '{tool_name}' not in spec"],
            warnings=[]
        )
    
    schema = get_tool_schema(tool_name)
    if not schema:
        # noop and similar have empty schema
        return ValidationResult(valid=True, tool_name=tool_name, errors=[], warnings=[])
    
    # 2. Check required arguments
    for arg_name, arg_spec in schema.items():
        if arg_spec.get("required", False) and arg_name not in arguments:
            errors.append(f"Missing required argument: {arg_name}")
    
    # 3. Check argument types
    for arg_name, value in arguments.items():
        if arg_name not in schema:
            warnings.append(f"Unknown argument: {arg_name}")
            continue
        
        expected_type = schema[arg_name].get("type")
        if expected_type == "string" and not isinstance(value, str):
            errors.append(f"Argument '{arg_name}' must be string, got {type(value).__name__}")
        elif expected_type == "number" and not isinstance(value, (int, float)):
            errors.append(f"Argument '{arg_name}' must be number, got {type(value).__name__}")
        elif expected_type == "object" and not isinstance(value, dict):
            errors.append(f"Argument '{arg_name}' must be object, got {type(value).__name__}")
        elif expected_type == "array" and not isinstance(value, list):
            errors.append(f"Argument '{arg_name}' must be array, got {type(value).__name__}")
    
    # 4. Check path allowlist for filesystem tools
    if tool_name.startswith("filesystem.") and "path" in arguments:
        allowed = get_allowed_paths(tool_name)
        if allowed:
            path = arguments["path"]
            if not any(path.startswith(a) for a in allowed):
                errors.append(f"Path '{path}' not in allowlist: {allowed}")
    
    # 5. Check URL allowlist for network tools
    if tool_name.startswith("http.") and "url" in arguments:
        allowed = get_allowed_urls(tool_name)
        if allowed:
            url = arguments["url"]
            if not any(url.startswith(a) for a in allowed):
                errors.append(f"URL '{url}' not in allowlist: {allowed}")
    
    # 6. Check expression safety for calculator.compute
    if tool_name == "calculator.compute" and "expression" in arguments:
        expr = arguments["expression"]
        if not re.match(r'^[\d\s\+\-\*/\(\)\.\,a-z]+$', str(expr).lower()):
            errors.append(f"Unsafe expression: {expr}")
    
    return ValidationResult(
        valid=len(errors) == 0,
        tool_name=tool_name,
        errors=errors,
        warnings=warnings
    )


def validate_dataset_sample(sample: Dict[str, Any]) -> ValidationResult:
    """
    Validate a training dataset sample.
    
    Sample must have 'tool_name' and 'arguments' keys.
    """
    if "tool_name" not in sample:
        return ValidationResult(
            valid=False,
            tool_name="MISSING",
            errors=["Sample missing 'tool_name' key"],
            warnings=[]
        )
    
    if "arguments" not in sample:
        return ValidationResult(
            valid=False,
            tool_name=sample["tool_name"],
            errors=["Sample missing 'arguments' key"],
            warnings=[]
        )
    
    return validate_tool_call(sample["tool_name"], sample["arguments"])


def generate_tool_call_template(tool_name: str) -> Optional[Dict[str, Any]]:
    """
    Generate a template tool call for dataset generation.
    
    Returns dict with placeholders.
    """
    if not is_valid_tool(tool_name):
        return None
    
    schema = get_tool_schema(tool_name)
    arguments = {}
    
    for arg_name, arg_spec in schema.items():
        arg_type = arg_spec.get("type", "string")
        if arg_type == "string":
            arguments[arg_name] = f"<{arg_name}>"
        elif arg_type == "number":
            arguments[arg_name] = 0
        elif arg_type == "object":
            arguments[arg_name] = {}
        elif arg_type == "array":
            arguments[arg_name] = []
    
    return {
        "tool_name": tool_name,
        "arguments": arguments
    }


def export_for_training() -> Dict[str, Any]:
    """
    Export spec in format suitable for training prompt engineering.
    
    Returns simplified tool list for system prompts.
    """
    spec = load_spec()
    tools = []
    
    for name, config in spec["tools"].items():
        schema = config.get("schema", {})
        args = []
        for arg_name, arg_spec in schema.items():
            arg_type = arg_spec.get("type", "string")
            required = "required" if arg_spec.get("required") else "optional"
            args.append(f"{arg_name}: {arg_type} ({required})")
        
        tools.append({
            "name": name,
            "category": config.get("category", "unknown"),
            "arguments": args,
            "pure": config.get("pure", False)
        })
    
    return {
        "version": spec["_meta"]["version"],
        "tools": tools,
        "output_format": spec["output_contract"]["format"]
    }


def print_spec_summary():
    """Print human-readable spec summary."""
    spec = load_spec()
    print("=" * 60)
    print("NOOGH GLOBAL TOOL MAPPING SPEC")
    print(f"Version: {spec['_meta']['version']}")
    print(f"Status: {spec['_meta']['status']}")
    print("=" * 60)
    print()
    
    by_category = {}
    for name, config in spec["tools"].items():
        cat = config.get("category", "unknown")
        if cat not in by_category:
            by_category[cat] = []
        by_category[cat].append(name)
    
    for cat, tools in sorted(by_category.items()):
        print(f"📁 {cat.upper()}")
        for tool in tools:
            cfg = spec["tools"][tool]
            pure = "⚡" if cfg.get("pure") else "🔧"
            print(f"   {pure} {tool}")
        print()
    
    print("=" * 60)
    print(f"Total tools: {len(spec['tools'])}")
    print("=" * 60)


if __name__ == "__main__":
    print_spec_summary()
