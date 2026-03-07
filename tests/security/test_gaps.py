"""
SECURITY TEST SUITE — GLOBAL COMPLIANCE GAPS
Tests for GAP-001 through GAP-006 fixes

Run: pytest tests/security/ -v
"""
import asyncio
import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))


class TestGAP001MaxActionsPerCycle:
    """GAP-001: Max actions per cycle prevents runaway execution."""
    
    def test_max_actions_attribute_exists(self):
        """Verify max actions limit is configured."""
        from unified_core.agent_daemon import AgentDaemon
        daemon = AgentDaemon()
        assert hasattr(daemon, '_max_actions_per_cycle')
        assert daemon._max_actions_per_cycle == 10


class TestGAP003FailureCooldown:
    """GAP-003: Consecutive failures trigger cooldown."""
    
    def test_cooldown_attributes_exist(self):
        """Verify cooldown mechanism is configured."""
        from unified_core.agent_daemon import AgentDaemon
        daemon = AgentDaemon()
        assert hasattr(daemon, '_consecutive_failures')
        assert hasattr(daemon, '_failure_cooldown_threshold')
        assert daemon._failure_cooldown_threshold == 3


class TestGAP004ProcessAllowlist:
    """GAP-004: Process spawning is restricted to allowlist."""
    
    def test_command_allowlist_exists(self):
        """Verify command allowlist is defined and contains safe read-only commands."""
        from unified_core.core.actuators import ProcessActuator
        assert hasattr(ProcessActuator, 'ALLOWED_COMMANDS')
        # Should contain safe read-only commands (echo, date, ls, cat, ps, etc.)
        assert len(ProcessActuator.ALLOWED_COMMANDS) >= 18
        # Verify only safe commands (no rm, chmod, wget, curl, etc.)
        for cmd in ProcessActuator.ALLOWED_COMMANDS:
            assert "rm" not in cmd, f"Dangerous command in allowlist: {cmd}"
            assert "chmod" not in cmd, f"Dangerous command in allowlist: {cmd}"
            assert "wget" not in cmd, f"Dangerous command in allowlist: {cmd}"
            assert "curl" not in cmd, f"Dangerous command in allowlist: {cmd}"
    
    def test_spawn_blocked_by_default(self):
        """Verify spawn is blocked when command not in allowlist."""
        from unified_core.core.actuators import ProcessActuator, ActionResult
        actuator = ProcessActuator()
        result = actuator.spawn(["/bin/ls"])
        assert result.result == ActionResult.BLOCKED
        assert "allowlist" in result.result_data.get("error", "").lower()


class TestGAP005NetworkAllowlist:
    """GAP-005: Network requests are restricted to allowlist."""
    
    def test_url_allowlist_exists(self):
        """Verify URL allowlist is defined."""
        from unified_core.core.actuators import NetworkActuator
        assert hasattr(NetworkActuator, 'ALLOWED_URL_PATTERNS')
        # Should only allow localhost by default
        patterns = NetworkActuator.ALLOWED_URL_PATTERNS
        assert all("localhost" in p or "127.0.0.1" in p for p in patterns)
    
    def test_external_url_blocked(self):
        """Verify external URLs are blocked."""
        from unified_core.core.actuators import NetworkActuator, ActionResult
        actuator = NetworkActuator()
        # Sync wrapper for async method
        result = asyncio.run(actuator.http_request("GET", "https://example.com"))
        assert result.result == ActionResult.BLOCKED
        assert "allowlist" in result.result_data.get("error", "").lower()


class TestGAP006CycleTimeout:
    """GAP-006: Cycles have time limits."""
    
    def test_timeout_attribute_exists(self):
        """Verify cycle timeout is configured."""
        from unified_core.agent_daemon import AgentDaemon
        daemon = AgentDaemon()
        assert hasattr(daemon, '_cycle_timeout')
        assert daemon._cycle_timeout == 30.0


class TestFilesystemAllowlist:
    """Filesystem operations are restricted to safe paths."""
    
    def test_write_paths_defined(self):
        """Verify allowed write paths are configured."""
        from unified_core.core.actuators import FilesystemActuator
        assert hasattr(FilesystemActuator, 'ALLOWED_WRITE_PATHS')
        assert len(FilesystemActuator.ALLOWED_WRITE_PATHS) > 0
    
    def test_unsafe_path_blocked(self):
        """Verify writes to unsafe paths are blocked."""
        from unified_core.core.actuators import FilesystemActuator, ActionResult
        actuator = FilesystemActuator()
        result = actuator.write_file("/etc/passwd", "malicious")
        assert result.result == ActionResult.BLOCKED


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
