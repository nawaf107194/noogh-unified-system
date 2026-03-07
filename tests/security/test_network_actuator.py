"""
Security Test: Network Actuator URL Allowlist Enforcement

MANDATORY TESTS to ensure NetworkActuator only allows requests
to whitelisted URLs.

TEST 1 - External URLs blocked
TEST 2 - Internal/Localhost URLs allowed
TEST 3 - Governance wrapping works
"""

import pytest
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))


class TestNetworkActuatorAllowlist:
    """Tests for NetworkActuator URL allowlist enforcement."""
    
    def test_external_url_blocked(self):
        """External URLs must be blocked."""
        from unified_core.core.actuators import NetworkActuator, ActionResult
        
        actuator = NetworkActuator()
        
        # Create mock auth context
        auth = MagicMock()
        auth.user_id = "test_user"
        auth.require_scope = MagicMock()
        
        # Mock integrity check
        with patch('unified_core.core.actuators.verify_integrity'):
            with patch('config.integrity.verify_integrity'):
                # Try to access external URL (should be blocked)
                result = actuator.http_request(
                    url="https://api.openai.com/v1/chat",
                    method="POST",
                    auth_context=auth
                )
        
        assert result.result == ActionResult.BLOCKED, \
            "DANGER: External URL was NOT blocked!"
        assert "not in allowlist" in result.result_data.get("error", "").lower()
    
    def test_localhost_url_allowed(self):
        """Localhost URLs should be allowed."""
        from unified_core.core.actuators import NetworkActuator
        
        actuator = NetworkActuator()
        
        # Verify localhost pattern matches
        assert actuator._is_url_allowed("http://127.0.0.1:8001/health")
        assert actuator._is_url_allowed("http://localhost:8002/api/v1/test")
        assert actuator._is_url_allowed("https://127.0.0.1/secure")
    
    def test_noogh_internal_url_allowed(self):
        """Internal NOOGH service URLs should be allowed."""
        from unified_core.core.actuators import NetworkActuator
        
        actuator = NetworkActuator()
        
        assert actuator._is_url_allowed("http://api.noogh.local/v1/inference")
        assert actuator._is_url_allowed("http://neural-engine:8000/generate")
    
    def test_arbitrary_external_blocked(self):
        """Arbitrary external URLs must be blocked."""
        from unified_core.core.actuators import NetworkActuator
        
        actuator = NetworkActuator()
        
        # These should all be blocked
        dangerous_urls = [
            "https://google.com/",
            "http://evil.com/steal-data",
            "https://api.github.com/repos",
            "http://192.168.1.1/admin",
            "https://172.16.0.1/internal",
        ]
        
        for url in dangerous_urls:
            assert not actuator._is_url_allowed(url), \
                f"DANGER: URL {url} was not blocked!"


class TestNetworkActuatorGovernance:
    """Tests for NetworkActuator governance integration."""
    
    def test_auth_required(self):
        """Auth context must be required."""
        from unified_core.core.actuators import NetworkActuator
        
        actuator = NetworkActuator()
        
        with pytest.raises(Exception):  # SecurityError or similar
            actuator.http_request(
                url="http://localhost:8001/test",
                method="GET",
                auth_context=None  # No auth!
            )
    
    def test_scope_checked(self):
        """Network scope must be verified."""
        from unified_core.core.actuators import NetworkActuator
        
        actuator = NetworkActuator()
        
        auth = MagicMock()
        auth.user_id = "test_user"
        auth.require_scope = MagicMock(side_effect=PermissionError("No scope"))
        
        with patch('config.integrity.verify_integrity'):
            with pytest.raises(PermissionError):
                actuator.http_request(
                    url="http://localhost/test",
                    method="GET",
                    auth_context=auth
                )
        
        # Verify scope was checked
        auth.require_scope.assert_called_once_with("network:http")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
