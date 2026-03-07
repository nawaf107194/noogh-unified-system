"""
Tests for Resource Management modules
"""
import pytest
import os
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

from unified_core.resources.filesystem import (
    SecureFileSystem, FileOperation, FileAccessResult
)


class TestSecureFileSystem:
    """Test sandboxed file system access."""
    
    @pytest.fixture
    def temp_root(self):
        """Create temp directory as allowed root."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield tmpdir
    
    @pytest.fixture
    def fs(self, temp_root):
        """FileSystem with temp root."""
        return SecureFileSystem(
            allowed_roots=[temp_root],
            audit_enabled=True
        )
    
    def test_path_allowed_in_root(self, fs, temp_root):
        """Paths within allowed roots are permitted."""
        allowed_path = os.path.join(temp_root, "subdir", "file.txt")
        assert fs.is_path_allowed(allowed_path)
    
    def test_path_blocked_outside_root(self, fs):
        """Paths outside allowed roots are blocked."""
        assert not fs.is_path_allowed("/etc/passwd")
        assert not fs.is_path_allowed("/root/.bashrc")
    
    def test_blocked_paths(self, fs):
        """Explicitly blocked paths are denied."""
        blocked = ["/etc/shadow", "/etc/sudoers", "/root", "/proc/kcore"]
        for path in blocked:
            assert not fs.is_path_allowed(path)
    
    def test_write_and_read(self, fs, temp_root):
        """Write and read operations work."""
        test_path = os.path.join(temp_root, "test.txt")
        content = "Hello, Unified Core!"
        
        # Write
        result = fs.write_file(test_path, content, agent_id="test_agent")
        assert result.success
        
        # Read
        result = fs.read_file(test_path, agent_id="test_agent")
        assert result.success
        assert result.content == content
    
    def test_delete_file(self, fs, temp_root):
        """Delete operation works."""
        test_path = os.path.join(temp_root, "to_delete.txt")
        
        # Create file
        fs.write_file(test_path, "delete me")
        assert os.path.exists(test_path)
        
        # Delete
        result = fs.delete_file(test_path, agent_id="test_agent")
        assert result.success
        assert not os.path.exists(test_path)
    
    def test_read_nonexistent(self, fs, temp_root):
        """Reading nonexistent file fails gracefully."""
        result = fs.read_file(os.path.join(temp_root, "nonexistent.txt"))
        assert not result.success
        assert "not found" in result.error.lower()
    
    def test_write_creates_dirs(self, fs, temp_root):
        """Write creates parent directories."""
        test_path = os.path.join(temp_root, "deep", "nested", "dir", "file.txt")
        
        result = fs.write_file(test_path, "content", create_dirs=True)
        assert result.success
        assert os.path.exists(test_path)
    
    def test_list_directory(self, fs, temp_root):
        """Directory listing works."""
        # Create some files
        fs.write_file(os.path.join(temp_root, "file1.txt"), "a")
        fs.write_file(os.path.join(temp_root, "file2.txt"), "b")
        os.mkdir(os.path.join(temp_root, "subdir"))
        
        result = fs.list_directory(temp_root)
        assert result.success
        assert result.metadata["count"] == 3
    
    def test_write_blocked_extension(self, fs, temp_root):
        """Writing blocked extensions fails."""
        fs.block_extension(".exe")
        
        result = fs.write_file(
            os.path.join(temp_root, "malware.exe"),
            "bad content"
        )
        assert not result.success
        assert "denied" in result.error.lower()
    
    def test_audit_log(self, fs, temp_root):
        """Operations are audited."""
        test_path = os.path.join(temp_root, "audited.txt")
        
        fs.write_file(test_path, "content", agent_id="agent_x")
        fs.read_file(test_path, agent_id="agent_x")
        
        log = fs.get_audit_log(agent_id="agent_x")
        assert len(log) >= 2
        
        operations = [e.operation for e in log]
        assert FileOperation.WRITE in operations
        assert FileOperation.READ in operations
    
    def test_max_file_size(self, fs, temp_root):
        """Large files are blocked."""
        fs.max_file_size_mb = 0.001  # 1KB
        test_path = os.path.join(temp_root, "large.txt")
        
        # Create large file directly
        with open(test_path, "w") as f:
            f.write("x" * 10000)  # 10KB
        
        result = fs.read_file(test_path)
        assert not result.success
        assert "too large" in result.error.lower()
    
    def test_add_allowed_root(self, fs):
        """Dynamic root addition works."""
        new_root = "/tmp/dynamic_root"
        fs.add_allowed_root(new_root)
        
        assert any(str(r) == new_root for r in fs.allowed_roots)


class TestResourceMonitor:
    """Test system monitoring (mocked)."""
    
    @patch('unified_core.resources.monitor.psutil')
    def test_cpu_metrics(self, mock_psutil):
        """CPU metrics are collected."""
        mock_psutil.cpu_percent.return_value = 45.5
        mock_psutil.cpu_freq.return_value = MagicMock(current=2400.0, max=3600.0)
        mock_psutil.cpu_count.side_effect = [8, 16]  # cores, threads
        
        from unified_core.resources.monitor import ResourceMonitor
        
        monitor = ResourceMonitor(gpu_enabled=False)
        metrics = monitor.get_cpu_metrics()
        
        assert metrics.usage_percent == 45.5
        assert metrics.core_count == 8
    
    @patch('unified_core.resources.monitor.psutil')
    def test_memory_metrics(self, mock_psutil):
        """Memory metrics are collected."""
        mock_psutil.virtual_memory.return_value = MagicMock(
            total=32 * 1024**3,
            available=16 * 1024**3,
            used=16 * 1024**3,
            percent=50.0
        )
        mock_psutil.swap_memory.return_value = MagicMock(
            total=8 * 1024**3,
            used=1 * 1024**3,
            percent=12.5
        )
        
        from unified_core.resources.monitor import ResourceMonitor
        
        monitor = ResourceMonitor(gpu_enabled=False)
        metrics = monitor.get_memory_metrics()
        
        assert metrics.usage_percent == 50.0
        assert metrics.total_bytes == 32 * 1024**3


class TestProcessManager:
    """Test process management (mocked)."""
    
    def test_priority_enum(self):
        """Priority levels are ordered correctly."""
        from unified_core.resources.process_manager import ProcessPriority
        
        assert ProcessPriority.CRITICAL.value < ProcessPriority.HIGH.value
        assert ProcessPriority.HIGH.value < ProcessPriority.NORMAL.value
        assert ProcessPriority.NORMAL.value < ProcessPriority.LOW.value
        assert ProcessPriority.LOW.value < ProcessPriority.EXPENDABLE.value
    
    def test_protected_names(self):
        """System processes are protected."""
        from unified_core.resources.process_manager import ProcessManager
        
        pm = ProcessManager()
        
        for name in ["systemd", "init", "kernel", "sshd", "postgres"]:
            assert name in pm.PROTECTED_NAMES
    
    def test_protect_pid(self):
        """PIDs can be protected."""
        from unified_core.resources.process_manager import ProcessManager
        
        pm = ProcessManager()
        pm.protect(12345)
        
        assert 12345 in pm._protected_pids
        
        pm.unprotect(12345)
        assert 12345 not in pm._protected_pids
