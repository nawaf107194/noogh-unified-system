"""
Code Applier — File manipulation utilities for evolution proposals.

Extracted from EvolutionController v3.3 for modularity.
Contains AST-based function finding/replacing and indentation utilities.
"""
import ast
import logging
from typing import Optional

logger = logging.getLogger("unified_core.evolution.code_applier")


def detect_indent(code: str) -> int:
    """Detect indentation level of the first def/async def line."""
    for line in code.split('\n'):
        stripped = line.lstrip()
        if stripped.startswith('def ') or stripped.startswith('async def '):
            return len(line) - len(stripped)
    return 0


def reindent(code: str, target_indent: int) -> str:
    """Re-indent code to match target indentation level."""
    current = detect_indent(code)
    if current == target_indent:
        return code
    delta = target_indent - current
    lines = []
    for line in code.split('\n'):
        if not line.strip():
            lines.append(line)
        elif delta > 0:
            lines.append(' ' * delta + line)
        else:
            lines.append(line[abs(delta):] if len(line) >= abs(delta) else line)
    return '\n'.join(lines)


def find_function_in_file(file_content: str, func_name: str) -> Optional[str]:
    """Find a function/method body by name using AST.

    Returns the exact source text of the function, or None.
    Handles both top-level functions and class methods.
    """
    try:
        tree = ast.parse(file_content)
    except SyntaxError:
        return None

    lines = file_content.split('\n')

    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if node.name == func_name:
                start = node.lineno - 1
                end = node.end_lineno  # end_lineno is inclusive
                func_lines = lines[start:end]
                return '\n'.join(func_lines)

    return None


def replace_function_in_file(file_content: str, func_name: str,
                             new_code: str) -> Optional[str]:
    """Replace a function/method by name using AST line info.

    Finds the function by AST, replaces its exact lines with new_code,
    and returns the full modified file content. Returns None on failure.
    """
    try:
        tree = ast.parse(file_content)
    except SyntaxError:
        return None

    lines = file_content.split('\n')

    # Find all matching functions
    matches = []
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if node.name == func_name:
                matches.append(node)

    if not matches:
        return None

    # Use first match (most common case)
    node = matches[0]
    start = node.lineno - 1  # 0-indexed
    end = node.end_lineno    # exclusive

    # Build new file
    new_lines = lines[:start] + new_code.split('\n') + lines[end:]
    return '\n'.join(new_lines)
