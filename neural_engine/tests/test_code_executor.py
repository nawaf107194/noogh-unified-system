import pytest

from neural_engine.code_executor import CodeExecutor

def test_init_happy_path():
    executor = CodeExecutor(timeout=5)
    assert executor.timeout == 5
    assert isinstance(executor, CodeExecutor)

def test_init_edge_case_zero_timeout():
    executor = CodeExecutor(timeout=0)
    assert executor.timeout == 0
    assert isinstance(executor, CodeExecutor)

def test_init_edge_case_negative_timeout():
    executor = CodeExecutor(timeout=-1)
    assert executor.timeout == -1
    assert isinstance(executor, CodeExecutor)

def test_init_edge_case_none_timeout():
    executor = CodeExecutor(timeout=None)
    assert executor.timeout is None
    assert isinstance(executor, CodeExecutor)

def test_init_error_case_invalid_type():
    with pytest.raises(TypeError):
        CodeExecutor(timeout="invalid")