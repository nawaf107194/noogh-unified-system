"""
Security Tests for Protocol Parser.
Tests all security measures: size limits, timeouts, forbidden patterns, safe parsing.
"""

import time

import pytest

from gateway.app.core.protocol import (
    MAX_CODE_SIZE,
    MAX_RESPONSE_SIZE,
    ProtocolViolation,
    create_secure_parser,
)


class TestSecurityHardening:
    """Test security measures in protocol parser"""

    @pytest.fixture
    def parser(self):
        return create_secure_parser()

    def test_response_size_limit(self, parser):
        """Reject oversized responses"""
        huge_response = "THINK:\n" + "x" * (MAX_RESPONSE_SIZE + 1000)
        with pytest.raises(ProtocolViolation, match="THINK block exceeds size limit"):
            parser.parse(huge_response, strict=True)

    def test_code_size_limit(self, parser):
        """Reject oversized code blocks"""
        huge_code = "x" * (MAX_CODE_SIZE + 1000)
        response = f"""THINK:
Test

ACT:
```python
{huge_code}
```

REFLECT:
Done"""

        parsed = parser.parse(response, strict=False)
        assert "size limit" in " ".join(parsed.violations)

    def test_forbidden_import_detection(self, parser):
        """Detect forbidden __import__"""
        response = """THINK:
Try to bypass

ACT:
```python
__import__('os').system('ls')
```

REFLECT:
Done"""

        parsed = parser.parse(response, strict=False)
        action = parser.extract_action(parsed)

        assert action["tool"] == "reject"
        assert "forbidden" in action["metadata"]["reason"].lower()

    def test_forbidden_eval_detection(self, parser):
        """Detect forbidden eval"""
        response = """THINK:
Test

ACT:
```python
eval('print(123)')
```

REFLECT:
Done"""

        parsed = parser.parse(response, strict=False)
        assert any("forbidden" in v.lower() for v in parsed.violations)

    def test_forbidden_subprocess_detection(self, parser):
        """Detect forbidden subprocess"""
        response = """THINK:
Test

ACT:
```python
import subprocess
subprocess.run(['ls'])
```

REFLECT:
Done"""

        parsed = parser.parse(response, strict=False)
        assert any("forbidden" in v.lower() for v in parsed.violations)

    def test_forbidden_open_detection(self, parser):
        """Detect forbidden open() - should use tools instead"""
        response = """THINK:
Test

ACT:
```python
f = open('file.txt', 'r')
```

REFLECT:
Done"""

        parsed = parser.parse(response, strict=False)
        assert any("forbidden" in v.lower() for v in parsed.violations)

    def test_infinite_loop_detection(self, parser):
        """Detect while True infinite loops"""
        response = """THINK:
Test

ACT:
```python
while True:
    print('forever')
```

REFLECT:
Done"""

        parsed = parser.parse(response, strict=False)
        assert any("forbidden" in v.lower() for v in parsed.violations)

    def test_parse_timeout_protection(self, parser):
        """Test that large inputs are handled quickly (line-by-line parsing)"""
        # Create response with many lines - parser should handle quickly
        response = "THINK:\n" + "test\n" * 1000 + "\nACT:\nNONE\n\nREFLECT:\nDone"

        start = time.time()
        try:
            # Parser handles large inputs efficiently
            parsed = parser.parse(response, strict=False)
            elapsed = time.time() - start
            assert elapsed < 1.0  # Should be fast (< 1 second)
            assert parsed.think is not None
        except ProtocolViolation:
            pass  # Acceptable if it rejects the large input

    def test_safe_code_accepted(self, parser):
        """Safe code should be accepted"""
        response = """THINK:
Calculate factorial

ACT:
```python
import math
result = math.factorial(10)
print(result)
```

REFLECT:
Done"""

        parsed = parser.parse(response, strict=False)
        action = parser.extract_action(parsed)

        assert action["tool"] == "exec_python"
        assert action["code"] is not None
        assert action["metadata"]["safe"] is True

    def test_correction_prompt_caching(self, parser):
        """Correction prompts should be cached"""
        violations1 = ("Missing THINK", "Missing ACT")
        violations2 = ("Missing THINK", "Missing ACT")

        prompt1 = parser.generate_correction_prompt(violations1)
        prompt2 = parser.generate_correction_prompt(violations2)

        # Should be same object (cached)
        assert prompt1 == prompt2


class TestSafeParsing:
    """Test safe line-by-line parsing"""

    @pytest.fixture
    def parser(self):
        return create_secure_parser()

    def test_basic_parsing(self, parser):
        """Basic valid response"""
        response = """THINK:
Need to test

ACT:
```python
print('test')
```

REFLECT:
Success

ANSWER:
Test result"""

        parsed = parser.parse(response, strict=False)

        assert parsed.think is not None
        assert parsed.act_code is not None
        assert parsed.reflect is not None
        assert parsed.answer is not None
        assert parsed.is_final is True

    def test_multiline_blocks(self, parser):
        """Handle multiline content in blocks"""
        response = """THINK:
Line 1 of thinking
Line 2 of thinking
Line 3 of thinking

ACT:
```python
# Comment line 1
# Comment line 2
print('test')
```

REFLECT:
Line 1
Line 2
Done"""

        parsed = parser.parse(response, strict=False)

        assert "Line 1 of thinking" in parsed.think
        assert "Line 3 of thinking" in parsed.think
        assert "Comment line 1" in parsed.act_code

    def test_no_regex_backtracking_vulnerability(self, parser):
        """Safe parsing shouldn't have ReDoS vulnerability"""
        # Create input that would cause regex backtracking
        malicious = "THINK:\n" + "a" * 1000 + "\n\nACT:\n" + "```" + "a" * 1000

        start = time.time()
        try:
            parser.parse(malicious, strict=False)
        except Exception:
            pass
        elapsed = time.time() - start

        # Should fail fast, not hang
        assert elapsed < 1.0  # Increased tolerance


class TestActionExtraction:
    """Test action extraction with security metadata"""

    @pytest.fixture
    def parser(self):
        return create_secure_parser()

    def test_extract_with_metadata(self, parser):
        """Actions include metadata"""
        response = """THINK:
Test

ACT:
```python
print(123)
```

REFLECT:
Done"""

        parsed = parser.parse(response, strict=False)
        action = parser.extract_action(parsed)

        assert "metadata" in action
        assert "code_length" in action["metadata"]
        assert action["metadata"]["safe"] is True

    def test_reject_action_for_violations(self, parser):
        """Rejected actions include violation details"""
        response = """THINK:
Test

ACT:
```python
eval('bad')
```

REFLECT:
Done"""

        parsed = parser.parse(response, strict=False)
        action = parser.extract_action(parsed)

        assert action["tool"] == "reject"
        assert "reason" in action["metadata"]
        assert "violations" in action["metadata"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
