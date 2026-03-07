"""
JSON Schema Validator for Tool Arguments
Provides strict validation of tool arguments to prevent injection attacks.
"""
import json
import logging
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


# Maximum sizes for security
MAX_STRING_LENGTH = 10000  # 10KB max for any string argument
MAX_DICT_DEPTH = 5  # Prevent deeply nested objects
MAX_ARRAY_LENGTH = 1000  # Prevent huge arrays


class ValidationError(Exception):
    """Raised when tool argument validation fails."""
    pass


def validate_tool_args(
    tool_name: str,
    args: Dict[str, Any],
    max_string_len: int = MAX_STRING_LENGTH,
    max_depth: int = MAX_DICT_DEPTH
) -> Dict[str, Any]:
    """
    Validate and sanitize tool arguments.
    
    Security checks:
    - No excessively long strings (DoS prevention)
    - No deeply nested objects (stack overflow prevention)
    - No unsafe data types (code injection prevention  
    - No null bytes (path traversal prevention)
    
    Args:
        tool_name: Name of the tool being called
        args: Arguments dictionary to validate
        max_string_len: Maximum allowed string length
        max_depth: Maximum nesting depth for dicts/lists
        
    Returns:
        Validated and sanitized args dict
        
    Raises:
        ValidationError: If validation fails
    """
    if not isinstance(args, dict):
        raise ValidationError(f"Tool args must be dict, got {type(args).__name__}")
    
    try:
        return _validate_value(args, depth=0, max_depth=max_depth, max_string_len=max_string_len)
    except RecursionError:
        raise ValidationError(f"Tool args exceed maximum nesting depth ({max_depth})")


def _validate_value(value: Any, depth: int, max_depth: int, max_string_len: int) -> Any:
    """
    Recursively validate a value.
    
    Allowed types: str, int, float, bool, None, dict, list
    Disallowed: functions, classes, modules, etc.
    """
    # Depth check
    if depth > max_depth:
        raise ValidationError(f"Nesting depth {depth} exceeds maximum {max_depth}")
    
    # None is safe
    if value is None:
        return None
    
    # Primitives
    if isinstance(value, bool):  # Check bool before int (bool is subclass of int)
        return value
    
    if isinstance(value, int):
        # Sanity check for integer size
        if abs(value) > 2**53:  # JavaScript MAX_SAFE_INTEGER
            raise ValidationError(f"Integer too large: {value}")
        return value
    
    if isinstance(value, float):
        # Check for special values
        import math
        if math.isnan(value) or math.isinf(value):
            raise ValidationError(f"Invalid float value: {value}")
        return value
    
    if isinstance(value, str):
        # String security checks
        if len(value) > max_string_len:
            raise ValidationError(
                f"String length {len(value)} exceeds maximum {max_string_len}"
            )
        
        # Check for null bytes (path traversal attack)
        if '\x00' in value:
            raise ValidationError("Null byte detected in string (security violation)")
        
        # Check for suspicious control characters
        control_chars = ['\x01', '\x02', '\x03', '\x04', '\x05', '\x06', '\x07',
                        '\x08', '\x0b', '\x0c', '\x0e', '\x0f']
        if any(char in value for char in control_chars):
            logger.warning(f"Suspicious control characters in string, sanitizing")
            # Remove control chars
            value = ''.join(c for c in value if c not in control_chars)
        
        return value
    
    if isinstance(value, dict):
        # Recursively validate dict
        validated = {}
        
        # Check dict size
        if len(value) > 100:  # Max 100 keys per dict
            raise ValidationError(f"Dictionary too large: {len(value)} keys")
        
        for key, val in value.items():
            # Keys must be strings
            if not isinstance(key, str):
                raise ValidationError(f"Dictionary key must be string, got {type(key).__name__}")
            
            # Validate key length
            if len(key) > 100:
                raise ValidationError(f"Dictionary key too long: {len(key)}")
            
            # Recursively validate value
            validated[key] = _validate_value(val, depth + 1, max_depth, max_string_len)
        
        return validated
    
    if isinstance(value, list):
        # Check array size
        if len(value) > MAX_ARRAY_LENGTH:
            raise ValidationError(f"Array too large: {len(value)} items")
        
        # Recursively validate list
        return [_validate_value(item, depth + 1, max_depth, max_string_len) for item in value]
    
    # Disallow all other types (functions, classes, etc.)
    raise ValidationError(
        f"Unsafe argument type: {type(value).__name__}. "
        f"Allowed types: str, int, float, bool, None, dict, list"
    )


def sanitize_path(path: str) -> str:
    """
    Sanitize file path to prevent directory traversal attacks.
    
    Security checks:
    - Remove null bytes
    - No parent directory references (..)
    - No absolute paths outside allowed roots
    
    Args:
        path: File path to sanitize
        
    Returns:
        Sanitized path
        
    Raises:
        ValidationError: If path contains dangerous patterns
    """
    import os
    
    # Remove null bytes
    if '\x00' in path:
        raise ValidationError("Null byte in path (security violation)")
    
    # Resolve to canonical form
    try:
        canonical = os.path.normpath(path)
    except Exception as e:
        raise ValidationError(f"Invalid path: {e}")
    
    # Check for parent directory traversal
    if '..' in canonical:
        raise ValidationError("Parent directory references not allowed (..)")
    
    # Check for absolute paths
    if os.path.isabs(canonical):
        # Only allow specific roots
        allowed_roots = [
            '/home/noogh',
            '/tmp/noogh',
            '/var/noogh'
        ]
        
        if not any(canonical.startswith(root) for root in allowed_roots):
            raise ValidationError(
                f"Absolute path not in allowed roots: {canonical}"
            )
    
    return canonical


def validate_url(url: str) -> str:
    """
    Validate URL to prevent SSRF attacks.
    
    Args:
        url: URL to validate
        
    Returns:
        Validated URL
        
    Raises:
        ValidationError: If URL is unsafe
    """
    from urllib.parse import urlparse
    
    try:
        parsed = urlparse(url)
    except Exception as e:
        raise ValidationError(f"Invalid URL: {e}")
    
    # Check scheme
    if parsed.scheme not in ['http', 'https']:
        raise ValidationError(f"Unsafe URL scheme: {parsed.scheme}")
    
    # Check for localhost/internal IPs (SSRF prevention)
    hostname = parsed.hostname
    if not hostname:
        raise ValidationError("URL missing hostname")
    
    # Block internal IPs
    blocked_patterns = [
        '127.',      # localhost
        '10.',       # Private class A
        '172.16.',   # Private class B start
        '192.168.',  # Private class C
        'localhost',
        '0.0.0.0',
        '[::]',      # IPv6 localhost
    ]
    
    for pattern in blocked_patterns:
        if hostname.startswith(pattern):
            raise ValidationError(
                f"URL points to internal network: {hostname} "
                f"(SSRF prevention)"
            )
    
    return url


# Export
__all__ = [
    'validate_tool_args',
    'sanitize_path',
    'validate_url',
    'ValidationError',
    'MAX_STRING_LENGTH',
    'MAX_DICT_DEPTH',
    'MAX_ARRAY_LENGTH',
]
