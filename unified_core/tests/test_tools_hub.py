import pytest
from unittest.mock import patch, MagicMock
from pathlib import Path
from typing import Dict

# Assuming the class is named `ToolsHub` and `TOOLS_DIR` is defined somewhere in the module.
# Adjust these imports according to your actual module structure.
from unified_core.tools_hub import ToolsHub, TOOLS_DIR

@pytest.fixture
def mock_toolshub():
    toolshub = ToolsHub()
    toolshub.tool_dir = "test_tool_dir"
    return toolshub

@pytest.mark.parametrize("exists, files", [(True, ["file1.txt", "file2.txt"]), (False, [])])
def test_get_prompts_happy_path(mock_toolshub, exists, files):
    with patch.object(Path, 'exists', return_value=exists), \
         patch.object(Path, 'rglob', return_value=[MagicMock(name=f) for f in files]):
        result = mock_toolshub.get_prompts()
        if exists:
            assert result == {"prompt_files": files, "dir": str(TOOLS_DIR / mock_toolshub.tool_dir / "conf")}
        else:
            assert result == {"error": "Prompts directory not found"}

def test_get_prompts_edge_case_empty_directory(mock_toolshub):
    with patch.object(Path, 'exists', return_value=True), \
         patch.object(Path, 'rglob', return_value=[]):
        result = mock_toolshub.get_prompts()
        assert result == {"prompt_files": [], "dir": str(TOOLS_DIR / mock_toolshub.tool_dir / "conf")}

def test_get_prompts_error_case_invalid_directory(mock_toolshub):
    mock_toolshub.tool_dir = None
    with patch.object(Path, 'exists', return_value=False):
        result = mock_toolshub.get_prompts()
        assert result == {"error": "Prompts directory not found"}

# Assuming there's no asynchronous behavior in the provided function.
# If there were, you would need to use async/await and pytest-asyncio or similar.