import pytest
from unified_core.evolution.innovation_engine import InnovationEngine

# Create an instance of InnovationEngine for testing purposes
engine = InnovationEngine()

def test_extract_function_by_ast_happy_path():
    # Arrange
    file_path = "test_file.py"
    function_name = "happy_function"

    with open(file_path, 'w', encoding='utf-8') as f:
        f.write("""
def happy_function():
    return "Hello, World!"
""")

    # Act
    result = engine._extract_function_by_ast(file_path, function_name)

    # Assert
    assert result == "    return \"Hello, World!\"\n"

def test_extract_function_by_ast_edge_case_empty_file():
    # Arrange
    file_path = "empty_file.py"
    
    with open(file_path, 'w', encoding='utf-8') as f:
        pass

    function_name = "non_existent_function"

    # Act
    result = engine._extract_function_by_ast(file_path, function_name)

    # Assert
    assert result is None

def test_extract_function_by_ast_edge_case_none_file():
    # Arrange
    file_path = None
    function_name = "non_existent_function"

    # Act
    result = engine._extract_function_by_ast(file_path, function_name)

    # Assert
    assert result is None

def test_extract_function_by_ast_error_case_invalid_file_path():
    # Arrange
    file_path = "nonexistent_file.py"
    function_name = "non_existent_function"

    # Act
    result = engine._extract_function_by_ast(file_path, function_name)

    # Assert
    assert result is None

def test_extract_function_by_ast_async_function():
    # Arrange
    file_path = "test_async_file.py"
    function_name = "async_function"

    with open(file_path, 'w', encoding='utf-8') as f:
        f.write("""
import asyncio

async def async_function():
    await asyncio.sleep(1)
    return "Hello, World!"
""")

    # Act
    result = engine._extract_function_by_ast(file_path, function_name)

    # Assert
    assert result == """    await asyncio.sleep(1)\n    return \"Hello, World!\"\n"""

def test_extract_function_by_ast_missing_end_lineno():
    # Arrange
    file_path = "test_missing_end lineno.py"
    function_name = "missing_end_lineno"

    with open(file_path, 'w', encoding='utf-8') as f:
        f.write("""
def missing_end_lineno():
    return "Hello, World!"
""")

    # Act
    result = engine._extract_function_by_ast(file_path, function_name)

    # Assert
    assert result == "    return \"Hello, World!\"\n"