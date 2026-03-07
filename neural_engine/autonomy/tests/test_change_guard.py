import pytest

def test_count_affected_functions_happy_path():
    original = """
def func1():
    pass

def func2():
    pass
"""
    proposed = """
def func1():
    pass

def func3():
    pass
"""
    assert _count_affected_functions(original, proposed) == 1

def test_count_affected_functions_no_changes():
    code = """
def func1():
    pass

def func2():
    pass
"""
    assert _count_affected_functions(code, code) == 0

def test_count_affected_functions_empty_strings():
    assert _count_affected_functions("", "") == 0

def test_count_affected_functions_one_empty_string():
    original = """
def func1():
    pass
"""
    proposed = ""
    assert _count_affected_functions(original, proposed) == 1

def test_count_affected_functions_none_values():
    assert _count_affected_functions(None, None) == 0

def test_count_affected_functions_invalid_original_code():
    original = "This is not valid Python code"
    proposed = """
def func1():
    pass
"""
    assert _count_affected_functions(original, proposed) == -1

def test_count_affected_functions_invalid_proposed_code():
    original = """
def func1():
    pass
"""
    proposed = "This is not valid Python code"
    assert _count_affected_functions(original, proposed) == -1

def test_count_affected_functions_mixed_valid_and_invalid_code():
    original = """
def func1():
    pass
"""
    proposed = "This is not valid Python code\n\ndef func2():\n    pass"
    assert _count_affected_functions(original, proposed) == -1

def test_count_affected_functions_large_number_of_changes():
    original = "\n".join(f"def func{i}():\n    pass" for i in range(100))
    proposed = "\n".join(f"def func{i}():\n    pass" if i % 2 == 0 else f"def new_func{i}():\n    pass" for i in range(100))
    assert _count_affected_functions(original, proposed) == 50