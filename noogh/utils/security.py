"""
NOOGH Security Utilities

Safe math evaluation and other security-critical utilities.
This module replaces all dangerous eval() calls.

Created: 2026-01-30 (Post-Audit Hotfix v12.5.19)
Reference: Adversarial Audit v2.0 - P0 Remediation
"""

import ast
import operator
import logging
from typing import Union

logger = logging.getLogger("noogh.utils.security")


class MathSecurityError(ValueError):
    """Raised when unsafe math patterns are detected."""
    pass


def safe_math_eval(expression: str, max_len: int = 300) -> Union[float, int, str]:
    """
    Safely evaluates math expressions using AST parsing.
    
    Replaces: eval() in tool_executor.py and agent_kernel.py
    
    Security Controls:
    - Only allows numeric constants
    - Only allows basic math operators (+, -, *, /, //, %, **)
    - Blocks: imports, function calls, attribute access
    - Limits: expression length, exponent size
    
    Args:
        expression: Mathematical expression string
        max_len: Maximum allowed expression length (DoS prevention)
        
    Returns:
        Calculated result as int/float, or error string on failure
        
    Raises:
        MathSecurityError: On security violations (logged and converted to string)
    """
    if not expression or not isinstance(expression, str):
        return "Calculation Failed: Empty or invalid expression"
    
    expression = expression.strip()
    
    if len(expression) > max_len:
        logger.warning(f"SECURITY: Math expression exceeds length limit ({len(expression)} > {max_len})")
        return f"Calculation Failed: Expression exceeds safety length limit ({max_len} chars)"
    
    # Strictly allowed operators
    _OPERATORS = {
        ast.Add: operator.add,
        ast.Sub: operator.sub,
        ast.Mult: operator.mul,
        ast.Div: operator.truediv,
        ast.FloorDiv: operator.floordiv,
        ast.Pow: operator.pow,
        ast.Mod: operator.mod,
        ast.USub: operator.neg,
        ast.UAdd: operator.pos,
    }
    
    def _eval_node(node) -> Union[int, float]:
        """Recursively evaluate AST node with strict type checking."""
        
        # 1. Handle Literals (Numbers only)
        if isinstance(node, ast.Constant):
            if isinstance(node.value, (int, float)):
                return node.value
            raise MathSecurityError(f"Invalid type in expression: {type(node.value).__name__}")
        
        # Legacy Python 3.7 compatibility
        if isinstance(node, ast.Num):
            return node.n
        
        # 2. Handle Binary Operations (e.g., 1 + 2)
        if isinstance(node, ast.BinOp):
            op_type = type(node.op)
            if op_type not in _OPERATORS:
                raise MathSecurityError(f"Security Block: Operator {op_type.__name__} not allowed")
            
            left = _eval_node(node.left)
            right = _eval_node(node.right)
            
            # DoS Mitigation: Prevent massive exponentiation (e.g., 9**9**9)
            if op_type == ast.Pow:
                if abs(left) > 10000 or abs(right) > 100:
                    raise MathSecurityError(
                        f"Math safety: Exponent/Base too large (base={left}, exp={right})"
                    )
            
            # Division by zero check
            if op_type in (ast.Div, ast.FloorDiv, ast.Mod) and right == 0:
                raise MathSecurityError("Division by zero")
            
            return _OPERATORS[op_type](left, right)
        
        # 3. Handle Unary Operations (e.g., -5)
        if isinstance(node, ast.UnaryOp):
            op_type = type(node.op)
            if op_type not in _OPERATORS:
                raise MathSecurityError(f"Security Block: Unary operator {op_type.__name__} not allowed")
            return _OPERATORS[op_type](_eval_node(node.operand))
        
        # 4. Block everything else (Calls, Attributes, Names, Imports)
        raise MathSecurityError(f"Security Block: {type(node).__name__} not allowed in math expression")
    
    try:
        # Parse mode='eval' ensures only expressions, not statements
        node = ast.parse(expression, mode='eval')
        result = _eval_node(node.body)
        
        # Return integer if whole number
        if isinstance(result, float) and result.is_integer():
            return int(result)
        return result
        
    except MathSecurityError as e:
        logger.warning(f"SECURITY: Math eval blocked - {e}")
        return f"Calculation Failed: {e}"
        
    except SyntaxError as e:
        logger.debug(f"Math syntax error: {e}")
        return f"Calculation Failed: Invalid syntax"
        
    except Exception as e:
        logger.error(f"Unexpected math eval error: {e}")
        return f"Calculation Failed: {e}"



# Convenience alias for Arabic responses
def حساب_آمن(expression: str) -> Union[float, int, str]:
    """Arabic alias for safe_math_eval."""
    return safe_math_eval(expression)


# =============================================================================
# SECURE SHELL EXECUTION UTILITIES (P1 Fix - removes shell=True)
# =============================================================================

import subprocess
import shlex
import os
from typing import Tuple, Optional


# Whitelisted commands for secure execution
ALLOWED_COMMANDS = {
    'find', 'grep', 'ls', 'cat', 'wc', 'head', 'tail', 'git', 
    'df', 'free', 'ps', 'uptime', 'uname', 'date', 'ip', 'ss'
}


def secure_find(
    search_path: str,
    name_pattern: str,
    max_results: int = 20,
    timeout: int = 5
) -> Tuple[bool, str]:
    """
    Securely execute find command without shell=True.
    
    Security Controls:
    - No shell expansion (prevents ; && || injection)
    - Path traversal check
    - Timeout enforcement
    - Result limiting
    
    Args:
        search_path: Directory to search in
        name_pattern: File name pattern (literal, no shell glob expansion in dangerous ways)
        max_results: Maximum number of results to return
        timeout: Execution timeout in seconds
        
    Returns:
        Tuple of (success, output)
    """
    # Security: Block path traversal
    if ".." in name_pattern or name_pattern.startswith("/"):
        logger.warning(f"SECURITY: Path traversal blocked in find: {name_pattern}")
        return False, "Security Error: Invalid filename - path traversal detected"
    
    # Security: Sanitize search path
    if not os.path.isdir(search_path):
        return False, f"Error: Directory not found: {search_path}"
    
    # Build command as list (NO shell=True)
    cmd = [
        "find", 
        search_path,
        "-name", name_pattern,
        "-type", "f"
    ]
    
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
            shell=False  # SECURITY: Critical
        )
        
        # Limit results
        lines = result.stdout.strip().split('\n')[:max_results]
        output = '\n'.join(lines)
        
        if result.returncode != 0 and result.stderr:
            return False, f"Find error: {result.stderr[:200]}"
        
        return True, output or "No files found"
        
    except subprocess.TimeoutExpired:
        return False, "Timeout: Find command took too long"
    except Exception as e:
        logger.error(f"Secure find error: {e}")
        return False, f"Error: {str(e)}"


def secure_grep(
    pattern: str,
    search_path: str,
    include_pattern: str = "*.py",
    max_results: int = 15,
    timeout: int = 10
) -> Tuple[bool, str]:
    """
    Securely execute grep command without shell=True.
    
    Security Controls:
    - No shell expansion
    - Pattern sanitization
    - Timeout enforcement
    - Result limiting
    
    Args:
        pattern: Search pattern (literal string, not regex)
        search_path: Directory or file to search
        include_pattern: File extension filter
        max_results: Maximum results
        timeout: Execution timeout
        
    Returns:
        Tuple of (success, output)
    """
    # Security: Block obviously malicious patterns
    if any(c in pattern for c in [';', '&&', '||', '`', '$(']):
        logger.warning(f"SECURITY: Shell metacharacter blocked in grep: {pattern}")
        return False, "Security Error: Invalid pattern"
    
    # Security: Limit pattern length
    if len(pattern) > 200:
        return False, "Security Error: Pattern too long"
    
    # Build command as list (NO shell=True)
    cmd = [
        "grep",
        "-rn",            # Recursive with line numbers
        "--include", include_pattern,
        pattern,
        search_path
    ]
    
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
            shell=False  # SECURITY: Critical
        )
        
        # Limit results
        lines = result.stdout.strip().split('\n')[:max_results]
        output = '\n'.join(lines)
        
        return True, output or "No matches found"
        
    except subprocess.TimeoutExpired:
        return False, "Timeout: Grep command took too long"
    except Exception as e:
        logger.error(f"Secure grep error: {e}")
        return False, f"Error: {str(e)}"


def secure_command(
    command_parts: list,
    timeout: int = 10,
    allowed_commands: Optional[set] = None
) -> Tuple[bool, str]:
    """
    Execute a pre-validated command list without shell=True.
    
    This is for executing commands that have already been built 
    as argument lists (not user-controlled strings).
    
    Args:
        command_parts: List of command and arguments (must be list, not string)
        timeout: Execution timeout
        allowed_commands: Set of allowed base commands
        
    Returns:
        Tuple of (success, output)
    """
    if not isinstance(command_parts, list) or not command_parts:
        return False, "Security Error: Command must be a non-empty list"
    
    base_cmd = os.path.basename(command_parts[0])
    allowed = allowed_commands or ALLOWED_COMMANDS
    
    if base_cmd not in allowed:
        logger.warning(f"SECURITY: Command not whitelisted: {base_cmd}")
        return False, f"Security Error: Command '{base_cmd}' not allowed"
    
    try:
        result = subprocess.run(
            command_parts,
            capture_output=True,
            text=True,
            timeout=timeout,
            shell=False  # SECURITY: Critical
        )
        
        output = result.stdout.strip() or result.stderr.strip()
        return True, output or "No output"
        
    except subprocess.TimeoutExpired:
        return False, "Timeout: Command took too long"
    except Exception as e:
        logger.error(f"Secure command error: {e}")
        return False, f"Error: {str(e)}"


__all__ = [
    'safe_math_eval', 
    'MathSecurityError', 
    'حساب_آمن',
    'secure_find',
    'secure_grep',
    'secure_command',
    'ALLOWED_COMMANDS'
]
