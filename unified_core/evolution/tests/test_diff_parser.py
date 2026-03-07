import pytest
from unittest.mock import patch
from your_module.diff_parser import _parse_unified_diff  # Adjust the import according to your project structure

@pytest.fixture
def valid_diff():
    return """--- a/file.py
+++ b/file.py
@@ -1,5 +1,5 @@
-def old_function():
+async def new_function():
     print("Hello, world!")
-    return 42
+    await asyncio.sleep(1)
     print("Goodbye, world!")"""

@pytest.fixture
def invalid_diff():
    return """--- a/file.py
+++ b/file.py
@@ -1,5 +1,5 @@
-def old_function():
+new_function():
     print("Hello, world!")
-    return 42
+    await asyncio.sleep(1)
     print("Goodbye, world!")"""

@pytest.fixture
def empty_diff():
    return ""

@pytest.fixture
def no_headers_diff():
    return """@@ -1,5 +1,5 @@
-def old_function():
+async def new_function():
     print("Hello, world!")
-    return 42
+    await asyncio.sleep(1)
     print("Goodbye, world!")"""

def test_parse_unified_diff_valid(valid_diff):
    result = _parse_unified_diff(valid_diff)
    assert result is not None
    assert result["original_code"] == "def old_function():\n    print(\"Hello, world!\")\n    return 42\n    print(\"Goodbye, world!\")"
    assert result["refactored_code"] == "async def new_function():\n    print(\"Hello, world!\")\n    await asyncio.sleep(1)\n    print(\"Goodbye, world!\")"
    assert result["function"] == "new_function"
    assert result["confidence"] == 0.7

def test_parse_unified_diff_invalid(invalid_diff):
    result = _parse_unified_diff(invalid_diff)
    assert result is None

def test_parse_unified_diff_empty(empty_diff):
    result = _parse_unified_diff(empty_diff)
    assert result is None

def test_parse_unified_diff_no_headers(no_headers_diff):
    result = _parse_unified_diff(no_headers_diff)
    assert result is None

@patch('your_module.diff_parser.logger')
def test_parse_unified_diff_exception(mock_logger, valid_diff):
    # Modify valid_diff to cause an exception, e.g., by removing necessary parts
    modified_diff = valid_diff.replace('@@', '')
    result = _parse_unified_diff(modified_diff)
    assert result is None
    mock_logger.debug.assert_called_once()