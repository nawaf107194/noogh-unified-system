import pytest
import os

from gateway.app.core.skills import search_code

class TestSearchCode:

    @pytest.fixture
    def sample_workspace_dir(self, tmp_path):
        # Create a temporary workspace directory with some files
        root = tmp_path / "workspace"
        root.mkdir()

        (root / "file1.py").write_text("import os")
        (root / "file2.js").write_text("console.log('hello')")
        (root / "file3.ts").write_text("let x = 5")

        # Create a nested directory
        (root / "nested" / "file4.py").write_text("def test(): pass")

        return str(root)

    def test_happy_path(self, sample_workspace_dir):
        result = search_code(sample_workspace_dir, "import")
        assert result["success"] is True
        assert len(result["output"].splitlines()) == 1

    def test_edge_case_empty_pattern(self, sample_workspace_dir):
        result = search_code(sample_workspace_dir, "")
        assert result["success"] is False
        assert "error" in result

    def test_edge_case_no_files(self, tmp_path):
        workspace_dir = str(tmp_path)
        result = search_code(workspace_dir, "import")
        assert result["success"] is True
        assert len(result["output"].splitlines()) == 0

    def test_edge_case_none_pattern(self):
        with pytest.raises(TypeError) as e:
            search_code("workspace", None)
        assert str(e.value) == "'NoneType' object cannot be interpreted as an integer"

    def test_edge_case_invalid_workspace_dir(self, tmp_path):
        with pytest.raises(FileNotFoundError):
            search_code(str(tmp_path / "nonexistent"), "import")

    def test_limit_matches(self, sample_workspace_dir):
        result = search_code(sample_workspace_dir, "import")
        assert len(result["output"].splitlines()) == 1

        # Add more matches to exceed the limit
        (sample_workspace_dir + "/file5.py").write_text("import sys")
        result = search_code(sample_workspace_dir, "import")
        assert len(result["output"].splitlines()) == 20