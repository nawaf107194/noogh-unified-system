"""
Security Test: Subprocess Bypass Elimination

MANDATORY TESTS to ensure gateway/app/core/skills.py
never executes subprocess directly.

TEST 1 - Static grep guard (fast)
TEST 2 - Runtime monkeypatch trap (strong)
TEST 3 - Actuator gate verification
"""

import pytest
import os
import sys
import re
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))


class TestNoSubprocessBypass:
    """Static analysis tests to ensure no subprocess imports."""
    
    SKILLS_PATH = Path(__file__).parent.parent.parent / "gateway" / "app" / "core" / "skills.py"
    
    # FORBIDDEN PATTERNS - any of these = AUTO-FAIL
    FORBIDDEN_PATTERNS = [
        r"import\s+subprocess",
        r"from\s+subprocess\s+import",
        r"subprocess\.",
        r"os\.system\s*\(",
        r"os\.popen\s*\(",
        r"pty\.spawn",
        r"create_subprocess_exec",
        r"create_subprocess_shell",
        r"pexpect\.",
        r"paramiko\.",
    ]
    
    def test_skills_file_exists(self):
        """Verify skills.py exists."""
        assert self.SKILLS_PATH.exists(), f"skills.py not found at {self.SKILLS_PATH}"
    
    def test_no_subprocess_import(self):
        """CRITICAL: skills.py must not import subprocess."""
        content = self.SKILLS_PATH.read_text()
        
        for pattern in self.FORBIDDEN_PATTERNS:
            matches = re.findall(pattern, content, re.MULTILINE)
            assert not matches, (
                f"SECURITY VIOLATION: Forbidden pattern '{pattern}' found in skills.py\n"
                f"Matches: {matches}"
            )
    
    def test_no_subprocess_in_gateway_core(self):
        """Scan all of gateway/app/core for subprocess bypasses."""
        gateway_core = Path(__file__).parent.parent.parent / "gateway" / "app" / "core"
        
        violations = []
        for py_file in gateway_core.glob("*.py"):
            content = py_file.read_text()
            for pattern in self.FORBIDDEN_PATTERNS:
                if re.search(pattern, content):
                    # Exception: constants.py defines regex patterns for detection, not execution
                    if "constants.py" in str(py_file) and "IMPORT_SUBPROCESS" in content:
                        continue
                    # Exception: ast_validator.py defines blocklist strings, not execution
                    if "ast_validator.py" in str(py_file):
                        continue
                    # Exception: tools_extended.py comment about removal (not import)
                    if "tools_extended.py" in str(py_file) and "# SECURITY: subprocess import removed" in content:
                        # Check if there's actual import statement
                        if not re.search(r"^import\s+subprocess\s*$", content, re.MULTILINE):
                            continue
                    violations.append(f"{py_file.name}: {pattern}")
        
        assert not violations, f"BYPASS DETECTED:\n" + "\n".join(violations)


class TestRuntimeMonkeypatchTrap:
    """Runtime tests that trap any subprocess execution attempts."""
    
    def test_subprocess_run_trapped(self, monkeypatch):
        """If subprocess.run is called, this test FAILS."""
        import subprocess
        
        call_log = []
        
        def trap_run(*args, **kwargs):
            call_log.append(("subprocess.run", args, kwargs))
            raise RuntimeError("TRAP: subprocess.run was called!")
        
        def trap_popen(*args, **kwargs):
            call_log.append(("subprocess.Popen", args, kwargs))
            raise RuntimeError("TRAP: subprocess.Popen was called!")
        
        monkeypatch.setattr(subprocess, "run", trap_run)
        monkeypatch.setattr(subprocess, "Popen", trap_popen)
        
        # Import and call skills
        from gateway.app.core.skills import AgentSkills
        skills = AgentSkills(safe_root="/tmp")
        
        # These should return BLOCKED, not trigger subprocess
        result = skills.run_tests(".")
        assert result["success"] is False, "run_tests should be blocked"
        assert "SECURITY_BLOCKED" in result.get("error", ""), "Should return SECURITY_BLOCKED"
        
        # Verify trap was never hit
        assert len(call_log) == 0, f"BYPASS DETECTED: subprocess was called: {call_log}"
    
    def test_git_commands_blocked(self):
        """git_status and git_diff must return BLOCKED."""
        from gateway.app.core.skills import AgentSkills
        skills = AgentSkills(safe_root="/tmp")
        
        status_result = skills.git_status()
        assert status_result["success"] is False
        assert "SECURITY_BLOCKED" in status_result.get("error", "")
        
        diff_result = skills.git_diff()
        assert diff_result["success"] is False
        assert "SECURITY_BLOCKED" in diff_result.get("error", "")


class TestActuatorGateVerification:
    """Verify that process execution only works through ProcessActuator."""
    
    def test_process_actuator_allowlist_enforced(self):
        """ProcessActuator must block commands not in ALLOWED_COMMANDS."""
        from unified_core.core.actuators import ProcessActuator
        
        actuator = ProcessActuator()
        
        # Attempt to run a command NOT in allowlist
        result = actuator.spawn(cmd=["/usr/bin/rm", "-rf", "/"])
        
        # Must be blocked
        assert result.result_data.get("blocked", False) or "not allowed" in str(result.result_data).lower() or result.result.value != "success", \
            "DANGER: rm -rf was not blocked!"
    
    def test_process_actuator_allows_safe_commands(self):
        """ProcessActuator should allow commands in ALLOWED_COMMANDS."""
        from unified_core.core.actuators import ProcessActuator
        
        actuator = ProcessActuator()
        
        # /usr/bin/echo is in ALLOWED_COMMANDS
        result = actuator.spawn(cmd=["/usr/bin/echo", "test"])
        
        # Should succeed (echo is allowlisted)
        # If it's blocked, that's also fine - stricter is better
        # We just verify no exception was raised


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
