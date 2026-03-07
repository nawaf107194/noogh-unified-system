import pytest
from pathlib import Path
from agents.evaluate_elite import EvaluateElite

def test_init_happy_path():
    evaluate = EvaluateElite()
    assert isinstance(evaluate.data_file, Path)
    assert str(evaluate.data_file) == '/home/noogh/projects/noogh_unified_system/src/data/backtest_setups.jsonl'
    assert isinstance(evaluate.neurons_dir, Path)
    assert str(evaluate.neurons_dir) == '/home/noogh/projects/noogh_unified_system/src/neurons'

def test_init_edge_case_none():
    with pytest.raises(TypeError):
        EvaluateElite(None)

def test_init_edge_case_empty_string():
    with pytest.raises(TypeError):
        EvaluateElite('')

def test_init_edge_case_nonexistent_path():
    nonexistent_dir = Path('/nonexistent/path')
    evaluate = EvaluateElite(neurons_dir=nonexistent_dir)
    assert isinstance(evaluate.data_file, Path)
    assert str(evaluate.data_file) == '/home/noogh/projects/noogh_unified_system/src/data/backtest_setups.jsonl'
    assert isinstance(evaluate.neurons_dir, Path)
    assert str(evaluate.neurons_dir) == '/nonexistent/path'

def test_init_edge_case_invalid_path_type():
    with pytest.raises(TypeError):
        EvaluateElite(neurons_dir=123)

# Note: There are no async behaviors in the __init__ method, so no need for separate tests for that.