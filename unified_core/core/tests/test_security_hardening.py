import pytest

from unified_core.core.security_hardening import FileIntegrityMonitor, ProcessMonitor, SecurityHardening

class TestSecurityHardening:

    @pytest.fixture
    def security_hardening_instance(self):
        return SecurityHardening()

    def test_happy_path(self, security_hardening_instance):
        assert isinstance(security_hardening_instance.integrity, FileIntegrityMonitor)
        assert isinstance(security_hardening_instance.ps_monitor, ProcessMonitor)

    def test_edge_case_empty_list(self):
        with pytest.raises(TypeError) as exc_info:
            SecurityHardening([])
        assert "integrity files list cannot be empty" in str(exc_info.value)

    def test_edge_case_none_value(self):
        with pytest.raises(TypeError) as exc_info:
            SecurityHardening(None)
        assert "integrity files list cannot be None" in str(exc_info.value)

    def test_error_case_invalid_input_type(self):
        with pytest.raises(TypeError) as exc_info:
            SecurityHardening([123, 456])
        assert "all items must be strings" in str(exc_info.value)