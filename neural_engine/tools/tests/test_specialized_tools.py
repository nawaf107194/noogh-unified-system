import pytest
from neural_engine.tools.specialized_tools import list_project_files, _is_path_safe

def test_list_project_files_happy_path():
    result = list_project_files(directory="./tests", pattern="*.py")
    assert result["success"] is True
    assert result["directory"] == "./tests"
    assert result["pattern"] == "*.py"
    assert len(result["files"]) > 0  # Assuming there are some .py files in the test directory
    assert result["count"] == len(result["files"])
    assert "summary_ar" in result

def test_list_project_files_empty_directory():
    with pytest.raises(ValueError) as exc_info:
        list_project_files(directory="./empty_dir", pattern="*.txt")
    assert str(exc_info.value) == "SECURITY_BLOCKED: Directory not allowed"

def test_list_project_files_none_directory():
    result = list_project_files(directory=None, pattern="*.py")
    assert result["success"] is False
    assert result["error"] == "SECURITY_BLOCKED: Directory not allowed"
    assert result["summary_ar"] == "تم حظر الوصول: المجلد غير مسموح به"

def test_list_project_files_boundary_pattern():
    result = list_project_files(directory="./tests", pattern="*.py.*")
    assert result["success"] is False
    assert result["error"] is None  # No specific error message expected for invalid patterns in this function
    assert result["summary_ar"] == "فشل استعراض الملفات: "

def test_list_project_files_security_block():
    with pytest.raises(ValueError) as exc_info:
        list_project_files(directory="/etc", pattern="*.txt")
    assert str(exc_info.value) == "SECURITY_BLOCKED: Directory not allowed"

def test_list_project_files_limit_files():
    result = list_project_files(directory="./tests", pattern="*.py")
    assert len(result["files"]) <= 50