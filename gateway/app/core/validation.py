"""
Input validation utilities for NOOGH Gateway.
Provides decorators and validators to prevent crashes from invalid inputs.
"""

import logging
from functools import wraps
from typing import Any, Callable

from gateway.app.core.auth import AuthContext
from gateway.app.core.constants import APIConfig

logger = logging.getLogger(__name__)


class ValidationError(Exception):
    """Raised when input validation fails"""



# ============================================================================
# Validators
# ============================================================================


def validate_task(task: str) -> None:
    """
    Validate a task string.

    Args:
        task: Task string to validate

    Raises:
        ValidationError: If task is invalid
    """
    if not task:
        raise ValidationError("Task cannot be empty")

    if not isinstance(task, str):
        raise ValidationError(f"Task must be string, got {type(task).__name__}")

    task_len = len(task)
    if task_len < APIConfig.MIN_TASK_LENGTH:
        raise ValidationError(f"Task too short (minimum {APIConfig.MIN_TASK_LENGTH} characters)")

    if task_len > APIConfig.MAX_TASK_LENGTH:
        raise ValidationError(f"Task too long (maximum {APIConfig.MAX_TASK_LENGTH} characters)")

    # Check for null bytes
    if "\x00" in task:
        raise ValidationError("Task contains null bytes")


def validate_auth_context(auth: Any) -> None:
    """
    Validate an AuthContext object.

    Args:
        auth: AuthContext to validate

    Raises:
        ValidationError: If auth context is invalid
    """
    if not auth:
        raise ValidationError("AuthContext cannot be None")

    if not isinstance(auth, AuthContext):
        raise ValidationError(f"auth must be AuthContext, got {type(auth).__name__}")

    if not hasattr(auth, "scopes"):
        raise ValidationError("AuthContext missing 'scopes' attribute")

    if not isinstance(auth.scopes, set):
        raise ValidationError("AuthContext.scopes must be a set")


def validate_tool_args(tool_name: str, args: dict) -> None:
    """Validate tool arguments."""
    if not isinstance(args, dict):
        raise ValidationError(f"Tool args must be dict, got {type(args).__name__}")

    # Validator mapping
    validators = {
        "exec_python": _validate_exec_python,
        "read_file": _validate_file_op,
        "write_file": _validate_write_file,
    }

    validator = validators.get(tool_name)
    if validator:
        validator(args, tool_name)


def _validate_exec_python(args: dict, _: str):
    """Specific validation for exec_python."""
    if "code" not in args:
        raise ValidationError("exec_python requires 'code' argument")
    if not isinstance(args["code"], str) or not args["code"].strip():
        raise ValidationError("exec_python 'code' must be a non-empty string")


def _validate_file_op(args: dict, tool_name: str):
    """Shared validation for file operations (read/write)."""
    if "path" not in args:
        raise ValidationError(f"{tool_name} requires 'path' argument")
    path = args["path"]
    if not isinstance(path, str) or not path.strip():
        raise ValidationError(f"{tool_name} 'path' must be a non-empty string")

    # Enhanced path traversal and security checks
    import os.path

    # Check for absolute paths (not allowed)
    if os.path.isabs(path):
        raise ValidationError("Absolute paths are not allowed")

    # Check for path traversal patterns
    normalized_path = os.path.normpath(path)
    if normalized_path.startswith("..") or ".." in normalized_path:
        raise ValidationError("Path contains '..' (potential traversal attack)")

    # Check for null bytes
    if "\x00" in path:
        raise ValidationError("Path contains null bytes")

    # Check for suspicious characters
    suspicious_chars = ["<", ">", "|", "*", "?", '"', "'", "`", "$", ";", "&", "(", ")"]
    if any(char in path for char in suspicious_chars):
        raise ValidationError("Path contains suspicious characters")


def _validate_write_file(args: dict, tool_name: str):
    """Specific validation for write_file."""
    _validate_file_op(args, tool_name)
    if "content" not in args:
        raise ValidationError("write_file requires 'content' argument")


# ============================================================================
# Decorators
# ============================================================================


def validate_task_input(func: Callable) -> Callable:
    """
    Decorator to validate task input for process methods.

    Usage:
        @validate_task_input
        def process(self, task: str, auth: AuthContext, ...):
            ...
    """

    @wraps(func)
    def wrapper(self, task: str, auth: AuthContext, *args, **kwargs):
        try:
            validate_task(task)
            validate_auth_context(auth)
        except ValidationError as e:
            logger.error(f"Input validation failed: {e}")
            # Return error result instead of raising
            from gateway.app.core.agent_kernel import AgentResult

            return AgentResult(
                success=False,
                answer=f"Invalid input: {str(e)}",
                steps=0,
                error=str(e),
                metadata={"error_type": "VALIDATION_ERROR"},
            )

        return func(self, task, auth, *args, **kwargs)

    return wrapper


def validate_tool_execution(func: Callable) -> Callable:
    """
    Decorator to validate tool execution arguments.

    Usage:
        @validate_tool_execution
        def execute_tool(self, tool_name: str, **kwargs):
            ...
    """

    @wraps(func)
    def wrapper(self, tool_name: str, *args, **kwargs):
        try:
            # Extract auth if present
            auth = kwargs.get("auth")
            if auth:
                validate_auth_context(auth)

            # Validate tool-specific args
            tool_args = {k: v for k, v in kwargs.items() if k != "auth"}
            validate_tool_args(tool_name, tool_args)

        except ValidationError as e:
            logger.error(f"Tool validation failed for {tool_name}: {e}")
            return {"success": False, "error": f"Validation error: {str(e)}", "output": ""}

        return func(self, tool_name, *args, **kwargs)

    return wrapper


def validate_not_none(*param_names: str):
    """
    Decorator to validate that specified parameters are not None.

    Usage:
        @validate_not_none('task', 'auth')
        def process(self, task, auth):
            ...
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Get function signature
            import inspect

            sig = inspect.signature(func)
            bound_args = sig.bind(*args, **kwargs)
            bound_args.apply_defaults()

            # Check specified params
            for param_name in param_names:
                if param_name in bound_args.arguments:
                    value = bound_args.arguments[param_name]
                    if value is None:
                        raise ValidationError(f"Parameter '{param_name}' cannot be None")

            return func(*args, **kwargs)

        return wrapper

    return decorator


# ============================================================================
# Type validators
# ============================================================================


def ensure_type(value: Any, expected_type: type, param_name: str = "value") -> None:
    """
    Ensure a value is of expected type.

    Args:
        value: Value to check
        expected_type: Expected type
        param_name: Parameter name for error message

    Raises:
        ValidationError: If type doesn't match
    """
    if not isinstance(value, expected_type):
        raise ValidationError(f"{param_name} must be {expected_type.__name__}, " f"got {type(value).__name__}")


def ensure_string_not_empty(value: str, param_name: str = "value") -> None:
    """
    Ensure a string is not empty.

    Args:
        value: String to check
        param_name: Parameter name for error message

    Raises:
        ValidationError: If string is empty
    """
    ensure_type(value, str, param_name)
    if not value.strip():
        raise ValidationError(f"{param_name} cannot be empty")


def ensure_in_range(value: int, min_val: int, max_val: int, param_name: str = "value") -> None:
    """
    Ensure a value is within a range.

    Args:
        value: Value to check
        min_val: Minimum allowed value
        max_val: Maximum allowed value
        param_name: Parameter name for error message

    Raises:
        ValidationError: If value is out of range
    """
    if not (min_val <= value <= max_val):
        raise ValidationError(f"{param_name} must be between {min_val} and {max_val}, got {value}")
