import pytest

from unified_core.resources.process_manager import ProcessManager

class TestProtect:

    def setup_method(self):
        self.manager = ProcessManager()

    def test_happy_path(self):
        """Test adding a valid PID to the protected list."""
        pid = 1234
        initial_count = len(self.manager._protected_pids)
        self.manager.protect(pid)
        assert len(self.manager._protected_pids) == initial_count + 1
        assert pid in self.manager._protected_pids

    def test_empty_input(self):
        """Test adding an empty input to the protected list."""
        with pytest.raises(TypeError):
            self.manager.protect(None)

    def test_negative_boundary(self):
        """Test adding a negative boundary value to the protected list."""
        with pytest.raises(ValueError):
            self.manager.protect(-1)

    def test_large_boundary(self):
        """Test adding a large boundary value to the protected list."""
        import sys
        max_int = sys.maxsize
        initial_count = len(self.manager._protected_pids)
        self.manager.protect(max_int + 1)
        assert len(self.manager._protected_pids) == initial_count + 1
        assert max_int + 1 in self.manager._protected_pids

    def test_non_integer_input(self):
        """Test adding a non-integer input to the protected list."""
        with pytest.raises(TypeError):
            self.manager.protect("1234")