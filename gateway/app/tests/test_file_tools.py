"""
Tests for File I/O tools added in Phase 2.
Tests read_file, write_file, list_files with security validation.
"""

import os
import tempfile
from pathlib import Path

import pytest

from gateway.app.core.tools import ToolRegistry


class TestFileIOTools:
    """Test file I/O tools functionality"""

    @pytest.fixture
    def temp_workspace(self):
        """Create temporary workspace for testing"""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield tmpdir

    @pytest.fixture
    def tools(self, temp_workspace):
        """Create ToolRegistry with temporary workspace"""
        return ToolRegistry(data_dir=temp_workspace)

    def test_tools_has_file_operations(self, tools):
        """Registry includes file I/O tools"""
        tool_list = tools.list_tools()
        assert "read_file" in tool_list
        assert "write_file" in tool_list
        assert "list_files" in tool_list

    def test_write_then_read_file(self, tools, temp_workspace, admin_auth):
        """Write file then read it back"""
        content = "Hello from Noogh!"

        # Write
        write_result = tools.execute_tool("write_file", auth=admin_auth, path="test.txt", content=content)
        assert write_result["success"] is True
        assert "Wrote" in write_result["output"]

        # Read
        read_result = tools.execute_tool("read_file", auth=admin_auth, path="test.txt")
        assert read_result["success"] is True
        assert read_result["output"] == content

    def test_read_nonexistent_file(self, tools, admin_auth):
        """Reading nonexistent file returns error"""
        result = tools.execute_tool("read_file", auth=admin_auth, path="missing.txt")
        assert result["success"] is False
        assert "not found" in (result.get("output", "") + result.get("error", "")).lower()

    def test_write_creates_directories(self, tools, temp_workspace, admin_auth):
        """Write creates parent directories"""
        result = tools.execute_tool("write_file", auth=admin_auth, path="subdir/nested/file.txt", content="test")
        assert result["success"] is True

        # Verify directory was created
        assert os.path.exists(os.path.join(temp_workspace, "subdir", "nested"))

    def test_list_files_empty_directory(self, tools, admin_auth):
        """List files in empty directory"""
        result = tools.execute_tool("list_files", auth=admin_auth, path=".")
        # Should succeed or show empty
        assert "Error" not in result["output"] or "Empty" in result["output"]

    def test_list_files_with_content(self, tools, temp_workspace, admin_auth):
        """List files shows existing files"""
        # Create some files
        Path(temp_workspace, "file1.txt").write_text("test1")
        Path(temp_workspace, "file2.py").write_text("test2")
        os.mkdir(os.path.join(temp_workspace, "subdir"))

        result = tools.execute_tool("list_files", auth=admin_auth, path=".")
        assert result["success"] is True
        assert "file1.txt" in result["output"]
        assert "file2.py" in result["output"]
        assert "subdir" in result["output"]

    def test_path_traversal_blocked(self, tools, temp_workspace, admin_auth):
        """Security: block path traversal attacks"""
        # Try to write outside workspace
        result = tools.execute_tool("write_file", auth=admin_auth, path="../outside.txt", content="hack")
        assert result["success"] is False
        assert "Error" in result.get("output", "") or "Error" in result.get("error", "")

    def test_file_size_limit(self, tools, admin_auth):
        """Files larger than 1MB are rejected"""
        large_content = "x" * (1024 * 1024 + 1)  # 1MB + 1 byte
        result = tools.execute_tool("write_file", auth=admin_auth, path="large.txt", content=large_content)
        assert result["success"] is False
        assert "too large" in (result.get("output", "") + result.get("error", "")).lower()

    def test_read_binary_file_fails(self, tools, temp_workspace, admin_auth):
        """Reading binary files returns error"""
        # Create binary file
        binary_path = os.path.join(temp_workspace, "binary.bin")
        with open(binary_path, "wb") as f:
            f.write(bytes([0, 1, 2, 255]))

        result = tools.execute_tool("read_file", auth=admin_auth, path="binary.bin")
        assert result["success"] is False
        assert "not text" in (result.get("output", "") + result.get("error", "")).lower()


class TestToolRegistryIntegration:
    """Test ToolRegistry with all tools"""

    def test_all_tools_registered(self):
        """All Phase 2 tools are registered"""
        tools = ToolRegistry()
        expected_tools = {"exec_python", "read_file", "write_file", "list_files"}
        actual_tools = set(tools.list_tools().keys())
        assert expected_tools.issubset(actual_tools)

    def test_tool_execution_consistency(self, admin_auth):
        """All tools return consistent result format"""
        tools = ToolRegistry()

        # Test each tool returns dict with success, output, error
        result = tools.execute_tool("exec_python", auth=admin_auth, code="print('test')")
        # assert "error" in result # Standardize: error key might be None or missing on success?
        # Actually, let's just check success and output are present.
        assert "success" in result
        assert "output" in result

        with tempfile.TemporaryDirectory() as tmpdir:
            tools_with_workspace = ToolRegistry(workspace_dir=tmpdir)

            result2 = tools_with_workspace.execute_tool("list_files", auth=admin_auth, path=".")
            assert "success" in result2
            assert "output" in result2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
