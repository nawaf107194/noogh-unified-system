import pytest
from pathlib import Path
from noogh_system_diagnostic import check_syntax, DiagResult

@pytest.fixture
def sample_py_files(tmp_path):
    py_file1 = tmp_path / "test1.py"
    py_file2 = tmp_path / "test2.py"
    py_file3 = tmp_path / "subdir/test3.py"

    with open(py_file1, 'w') as f:
        f.write("print('Hello, World!')")
    
    with open(py_file2, 'w') as f:
        f.write("a = 1 +")
    
    with open(py_file3, 'w') as f:
        f.write("def foo(): pass")

    return tmp_path

@pytest.fixture
def engine_root(tmp_path):
    sub_dir = tmp_path / "subdir"
    sub_dir.mkdir()
    (tmp_path / "test.py").touch()
    (sub_dir / "test_sub.py").touch()
    return tmp_path

@pytest.fixture
def src_root(tmp_path):
    (tmp_path / "src").mkdir()
    with open(tmp_path / "src" / "main.py", 'w') as f:
        f.write("print('Hello, World!')")
    return tmp_path

def test_check_syntax_normal(sample_py_files, engine_root, src_root):
    original_engine_root = DiagResult.engine_root
    DiagResult.engine_root = engine_root
    original_src_root = DiagResult.src_root
    DiagResult.src_root = src_root
    
    result = check_syntax()
    
    assert isinstance(result, DiagResult)
    assert not result.is_error, "Should not have any errors"
    assert result.message == f"All {len(list(sample_py_files.rglob('*.py')))} Python files parse cleanly"
    
    DiagResult.engine_root = original_engine_root
    DiagResult.src_root = original_src_root

def test_check_syntax_empty(engine_root, src_root):
    with pytest.raises(ValueError) as exc_info:
        check_syntax()
    
    assert str(exc_info.value) == "No .py files found in the directory"

def test_check_syntax_none(sample_py_files, engine_root, src_root):
    original_engine_root = DiagResult.engine_root
    DiagResult.engine_root = None
    original_src_root = DiagResult.src_root
    DiagResult.src_root = src_root
    
    with pytest.raises(ValueError) as exc_info:
        check_syntax()
    
    assert str(exc_info.value) == "No .py files found in the directory"
    
    DiagResult.engine_root = original_engine_root
    DiagResult.src_root = original_src_root

def test_check_syntax_async(engine_root, src_root):
    with pytest.raises(NotImplementedError) as exc_info:
        check_syntax(async_mode=True)
    
    assert str(exc_info.value) == "Async mode is not supported for this function"