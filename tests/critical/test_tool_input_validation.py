"""
Test Tool Argument Validation
Tests the security validation of tool arguments.
"""
import pytest
from neural_engine.tools.tool_validator import (
    validate_tool_args,
    sanitize_path,
    validate_url,
    ValidationError,
    MAX_STRING_LENGTH,
    MAX_DICT_DEPTH,
)


class TestValidateToolArgs:
    """Test tool argument validation."""
    
    def test_valid_simple_args(self):
        """Valid simple arguments should pass."""
        args = {"name": "test", "count": 5, "enabled": True}
        result = validate_tool_args("test_tool", args)
        assert result == args
    
    def test_valid_nested_args(self):
        """Valid nested arguments should pass."""
        args = {
            "config": {
                "server":  "localhost",
                "port": 8080,
                "options": {
                    "retry": True
                }
            }
        }
        result = validate_tool_args("test_tool", args)
        assert result == args
    
    def test_too_deep_nesting(self):
        """Deeply nested objects should be rejected."""
        # Create 10-level deep nesting
        args = {"a": {"b": {"c": {"d": {"e": {"f": {"g": {"h": {"i": {"j": "value"}}}}}}}}}}
        
        with pytest.raises(ValidationError) as exc:
            validate_tool_args("test_tool", args, max_depth=5)
        
        assert "depth" in str(exc.value).lower()
    
    def test_string_too_long(self):
        """Excessively long strings should be rejected."""
        args = {"data": "x" * (MAX_STRING_LENGTH + 1)}
        
        with pytest.raises(ValidationError) as exc:
            validate_tool_args("test_tool", args)
        
        assert "length" in str(exc.value).lower()
    
    def test_null_byte_in_string(self):
        """Null bytes should be rejected (path traversal prevention)."""
        args = {"path": "/etc/passwd\x00.txt"}
        
        with pytest.raises(ValidationError) as exc:
            validate_tool_args("test_tool", args)
        
        assert "null byte" in str(exc.value).lower()
    
    def test_control_characters_sanitized(self):
        """Control characters should be removed."""
        args = {"text": "hello\x01world\x02test"}
        result = validate_tool_args("test_tool", args)
        
        # Control chars should be removed
        assert result["text"] == "helloworldtest"
    
    def test_unsafe_type_rejected(self):
        """Unsafe types (functions, classes) should be rejected."""
        args = {"func": lambda x: x}
        
        with pytest.raises(ValidationError) as exc:
            validate_tool_args("test_tool", args)
        
        assert "unsafe" in str(exc.value).lower()
    
    def test_large_integer(self):
        """Excessively large integers should be rejected."""
        args = {"count": 2**60}  # Way too large
        
        with pytest.raises(ValidationError) as exc:
            validate_tool_args("test_tool", args)
        
        assert "too large" in str(exc.value).lower()
    
    def test_invalid_float(self):
        """NaN and Inf should be rejected."""
        import math
        
        with pytest.raises(ValidationError):
            validate_tool_args("test_tool", {"value": math.nan})
        
        with pytest.raises(ValidationError):
            validate_tool_args("test_tool", {"value": math.inf})
    
    def test_large_array(self):
        """Excessively large arrays should be rejected."""
        from neural_engine.tools.tool_validator import MAX_ARRAY_LENGTH
        
        args = {"items": list(range(MAX_ARRAY_LENGTH + 1))}
        
        with pytest.raises(ValidationError) as exc:
            validate_tool_args("test_tool", args)
        
        assert "array" in str(exc.value).lower()
    
    def test_large_dict(self):
        """Dicts with too many keys should be rejected."""
        args = {f"key_{i}": i for i in range(101)}  # Max is 100
        
        with pytest.raises(ValidationError) as exc:
            validate_tool_args("test_tool", args)
        
        assert "dictionary" in str(exc.value).lower()
    
    def test_non_string_dict_key(self):
        """Dict keys must be strings."""
        # This creates a dict with non-string key (Python allows it)
        args = {1: "value"}
        
        with pytest.raises(ValidationError) as exc:
            validate_tool_args("test_tool", args)
        
        assert "key must be string" in str(exc.value).lower()


class TestSanitizePath:
    """Test path sanitization."""
    
    def test_valid_relative_path(self):
        """Valid relative paths should pass."""
        result = sanitize_path("data/file.txt")
        assert result == "data/file.txt"
    
    def test_parent_directory_rejected(self):
        """Parent directory references should be rejected."""
        with pytest.raises(ValidationError) as exc:
            sanitize_path("../etc/passwd")
        
        assert "parent directory" in str(exc.value).lower()
    
    def test_null_byte_rejected(self):
        """Null bytes in paths should be rejected."""
        with pytest.raises(ValidationError):
            sanitize_path("/tmp/file\x00.txt")
    
    def test_absolute_allowed_path(self):
        """Absolute paths in allowed roots should pass."""
        result = sanitize_path("/home/noogh/data/file.txt")
        assert "/home/noogh" in result
    
    def test_absolute_disallowed_path(self):
        """Absolute paths outside allowed roots should be rejected."""
        with pytest.raises(ValidationError) as exc:
            sanitize_path("/etc/passwd")
        
        assert "not in allowed roots" in str(exc.value).lower()


class TestValidateURL:
    """Test URL validation."""
    
    def test_valid_https_url(self):
        """Valid HTTPS URLs should pass."""
        url = "https://example.com/api"
        result = validate_url(url)
        assert result == url
    
    def test_localhost_rejected(self):
        """Localhost URLs should be rejected (SSRF prevention)."""
        with pytest.raises(ValidationError) as exc:
            validate_url("http://localhost:8080/api")
        
        assert "internal network" in str(exc.value).lower()
    
    def test_private_ip_rejected(self):
        """Private IPs should be rejected."""
        private_ips = [
            "http://127.0.0.1/api",
            "http://10.0.0.1/api",
            "http://172.16.0.1/api",
            "http://192.168.1.1/api",
        ]
        
        for url in private_ips:
            with pytest.raises(ValidationError):
                validate_url(url)
    
    def test_invalid_scheme(self):
        """Non-HTTP schemes should be rejected."""
        with pytest.raises(ValidationError) as exc:
            validate_url("ftp://example.com/file")
        
        assert "scheme" in str(exc.value).lower()
    
    def test_missing_hostname(self):
        """URLs without hostname should be rejected."""
        with pytest.raises(ValidationError) as exc:
            validate_url("http:///path")
        
        assert "hostname" in str(exc.value).lower()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
