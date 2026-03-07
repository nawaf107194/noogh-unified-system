import pytest
from unified_core.core.security_hardening import FileIntegrityMonitor, ProcessMonitor, SecurityHardening

class TestSecurityHardening:

    def test_happy_path(self):
        security = SecurityHardening()
        assert isinstance(security.integrity, FileIntegrityMonitor)
        assert isinstance(security.ps_monitor, ProcessMonitor)

    @pytest.mark.parametrize("invalid_input", [None, [], {}, ""])
    def test_edge_cases_invalid_inputs(self, invalid_input):
        with pytest.raises(TypeError):
            security = SecurityHardening(invalid_input)

# Note: The __init__ method does not have an explicit raise statement for invalid inputs,
# so we do not include an error case in this test suite.