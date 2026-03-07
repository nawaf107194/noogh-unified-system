"""
Security Test: Network Bypass Detection

Ensures no direct network calls outside NetworkActuator.http_request().
"""

import pytest
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))


class TestNoNetworkBypass:
    """Static and runtime tests for network bypass detection."""
    
    # Directories to scan
    SCAN_DIRS = [
        Path(__file__).parent.parent.parent / "unified_core",
        Path(__file__).parent.parent.parent / "gateway",
        Path(__file__).parent.parent.parent / "neural_engine",
    ]
    
    # Allowed files (actuator implementations)
    ALLOWED_FILES = {
        "actuators.py",
        "tools_extended.py",  # Uses allowlist internally
    }
    
    # Files that are allowed to use network (internal services)
    SERVICE_FILES = {
        "neural_bridge.py",    # Talks to local neural engine
        "neural_client.py",    # Talks to local neural engine
        "sandbox.py",          # Talks to local sandbox service
        "docker_sandbox.py",   # Talks to local docker
        "lifespan.py",         # Health checks on startup
        "routes.py",           # Internal routing
        "system.py",           # System health checks
        "dashboard.py",        # Dashboard metrics
    }
    
    FORBIDDEN_PATTERNS = [
        r"import\s+requests(?:\s|$)",
        r"import\s+httpx(?:\s|$)",
        r"import\s+aiohttp(?:\s|$)",
        r"from\s+urllib\s+import",
        r"import\s+socket(?:\s|$)",
        r"requests\.\w+\(",
        r"httpx\.\w+\(",
        r"aiohttp\.\w+\(",
    ]
    
    def test_no_network_bypass_in_core_logic(self):
        """Core logic files should not make direct network calls."""
        # Files that should NEVER have network calls
        forbidden_core_files = [
            "gravity.py",
            "scar.py", 
            "consequence.py",
            "world_model.py",
            "tool_policy.py",
            "benchmark_runner.py",
        ]
        
        violations = []
        for scan_dir in self.SCAN_DIRS:
            if not scan_dir.exists():
                continue
            for py_file in scan_dir.rglob("*.py"):
                if ".archive" in str(py_file):
                    continue
                if py_file.name not in forbidden_core_files:
                    continue
                    
                content = py_file.read_text(errors="ignore")
                for pattern in self.FORBIDDEN_PATTERNS:
                    if re.search(pattern, content):
                        violations.append(f"{py_file.name}: {pattern}")
        
        assert not violations, f"NETWORK BYPASS IN CORE:\n" + "\n".join(violations)
    
    def test_network_calls_use_allowlist(self):
        """Verify tools_extended.py uses domain allowlist."""
        tools_ext = Path(__file__).parent.parent.parent / "gateway" / "app" / "core" / "tools_extended.py"
        if tools_ext.exists():
            content = tools_ext.read_text()
            assert "ALLOWED_HTTP_DOMAINS" in content, "tools_extended.py must have domain allowlist"
            assert "hostname not in ALLOWED_HTTP_DOMAINS" in content, "Must check domain against allowlist"


class TestNetworkActuatorEnforcement:
    """Verify NetworkActuator enforces allowlist."""
    
    def test_network_actuator_has_allowlist(self):
        """NetworkActuator must have URL allowlist."""
        from unified_core.core.actuators import NetworkActuator
        assert hasattr(NetworkActuator, 'ALLOWED_URL_PATTERNS')
        assert len(NetworkActuator.ALLOWED_URL_PATTERNS) > 0
    
    def test_external_url_blocked(self):
        """External URLs must be blocked."""
        import asyncio
        from unified_core.core.actuators import NetworkActuator, ActionResult
        
        actuator = NetworkActuator()
        result = asyncio.run(actuator.http_request("GET", "https://evil.com/steal-data"))
        assert result.result == ActionResult.BLOCKED


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
