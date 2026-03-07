import pytest
from typing import Dict, Any, Optional

def extract_metadata_from_diff(diff: str) -> Optional[Dict[str, Any]]:
    """Extract original_code and refactored_code from a proposal diff.

    Supports two formats:

    1. NOOGH format:
        # Refactoring: <function_name>
        # Confidence: <N>%
        --- ORIGINAL ---
        <original code>
        +++ REFACTORED +++
        <refactored code>

    2. Unified diff format:
        --- a/path/to/file
        +++ b/path/to/file
        @@ -N,M +N,M @@
        <context and changes>
    """
    if not diff:
        return None

    # Try NOOGH format first
    result = _parse_noogh_format(diff)
    if result:
        return result

    # Try unified diff format
    result = _parse_unified_diff(diff)
    if result:
        return result

    return None

def _parse_noogh_format(diff: str) -> Optional[Dict[str, Any]]:
    lines = diff.split('\n')
    for line in lines:
        if 'Refactoring:' in line:
            function_name = line.split('Refactoring:')[1].strip()
        elif 'Confidence:' in line:
            confidence = int(line.split('Confidence:')[1].strip('%'))
        elif '--- ORIGINAL ---' in line:
            original_code = '\n'.join(lines[lines.index(line) + 1:])
            break
    else:
        return None

    for line in reversed(lines):
        if '+++ REFACTORED +++' in line:
            refactored_code = '\n'.join(lines[:lines.index(line)])
            break
    else:
        return None

    return {
        'function_name': function_name,
        'confidence': confidence,
        'original_code': original_code.strip(),
        'refactored_code': refactored_code.strip()
    }

def _parse_unified_diff(diff: str) -> Optional[Dict[str, Any]]:
    lines = diff.split('\n')
    for line in lines:
        if '---' in line and '+++' in line:
            file_paths = line.split(' ')[1].split('/')
            function_name = '/'.join(file_paths[:-1])
            break
    else:
        return None

    original_code = []
    refactored_code = []
    for line in lines:
        if '@@' in line:
            continue
        elif line.startswith('-'):
            original_code.append(line[2:])
        elif line.startswith('+'):
            refactored_code.append(line[2:])

    return {
        'function_name': function_name,
        'confidence': None,
        'original_code': '\n'.join(original_code),
        'refactored_code': '\n'.join(refactored_code)
    }

def test_extract_metadata_from_diff():
    # Happy path
    noogh_diff = """# Refactoring: my_function
# Confidence: 90%
--- ORIGINAL ---
def old_function(x):
    return x + 1

+++ REFACTORED +++
def my_function(x):
    return x + 2"""
    assert extract_metadata_from_diff(noogh_diff) == {
        'function_name': 'my_function',
        'confidence': 90,
        'original_code': 'def old_function(x):\n    return x + 1',
        'refactored_code': 'def my_function(x):\n    return x + 2'
    }

    unified_diff = """--- a/path/to/file.py
+++ b/path/to/file.py
@@ -1,4 +1,5 @@
 def old_function(x):
     return x + 1

+def new_function():
+    return 0"""
    assert extract_metadata_from_diff(unified_diff) == {
        'function_name': '/path/to/file',
        'confidence': None,
        'original_code': 'def old_function(x):\n    return x + 1',
        'refactored_code': 'def new_function():\n    return 0'
    }

    # Edge cases
    assert extract_metadata_from_diff("") is None
    assert extract_metadata_from_diff(None) is None

    # Error cases
    invalid_noogh_diff = """# Refactoring: my_function
--- ORIGINAL ---
def old_function(x):
    return x + 1"""
    assert extract_metadata_from_diff(invalid_noogh_diff) is None

    invalid_unified_diff = """--- a/path/to/file.py
+++ b/path/to/file.py
@@ -1,4 +1,5 @@
 def old_function(x):
     return x + 1"""
    assert extract_metadata_from_diff(invalid_unified_diff) is None

test_extract_metadata_from_diff()