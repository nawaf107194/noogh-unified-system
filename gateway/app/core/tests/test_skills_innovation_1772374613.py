import pytest
from gateway.app.core.skills import search_code

def test_search_code_happy_path(tmpdir):
    # Create a sample file with expected pattern
    (tmpdir / "main.py").write_text("def test_function():\n    print('Hello, World!')")
    
    result = search_code(str(tmpdir), "test")
    assert result["success"] is True
    assert "main.py" in result["output"]

def test_search_code_multiple_matches(tmpdir):
    # Create multiple files with expected pattern
    (tmpdir / "file1.py").write_text("print('Function 1')")
    (tmpdir / "file2.py").write_text("print('Function 2')")
    
    result = search_code(str(tmpdir), "Function")
    assert result["success"] is True
    assert len(result["output"].splitlines()) == 2

def test_search_code_no_matches(tmpdir):
    # Create a file without expected pattern
    (tmpdir / "main.py").write_text("print('Hello, World!')")
    
    result = search_code(str(tmpdir), "not_found")
    assert result["success"] is True
    assert not result["output"]

def test_search_code_empty_workspace():
    empty_dir = pytest.tmpdir_factory.mktemp("empty_dir")
    
    result = search_code(str(empty_dir), "test")
    assert result["success"] is True
    assert not result["output"]

def test_search_code_invalid_pattern(tmpdir):
    (tmpdir / "main.py").write_text("print('Hello, World!')")
    
    result = search_code(str(tmpdir), "")
    assert result["success"] is False
    assert "error" in result

def test_search_code_filetypes(tmpdir):
    # Create files with different extensions
    (tmpdir / "script.js").write_text("console.log('Hello, World!')")
    (tmpdir / "code.ts").write_text("console.error('Error')")
    
    result = search_code(str(tmpdir), "log")
    assert result["success"] is True
    assert "script.js" in result["output"]

def test_search_code_limit_matches(tmpdir):
    # Create more than 20 files with expected pattern
    for i in range(30):
        (tmpdir / f"file{i}.py").write_text(f"print('Function {i}')")
    
    result = search_code(str(tmpdir), "Function")
    assert result["success"] is True
    assert len(result["output"].splitlines()) == 20