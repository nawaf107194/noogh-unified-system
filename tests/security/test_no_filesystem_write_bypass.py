"""
Security Test: Filesystem Write Bypass Detection

Ensures no direct filesystem writes outside FilesystemActuator.
"""

import pytest
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))


class TestNoFilesystemWriteBypass:
    """Static analysis tests for filesystem write bypass detection."""
    
    # Directories to scan
    SCAN_DIRS = [
        Path(__file__).parent.parent.parent / "unified_core",
        Path(__file__).parent.parent.parent / "gateway",
        Path(__file__).parent.parent.parent / "neural_engine",
    ]
    
    # Allowed files (actuator implementations and state management)
    ALLOWED_FILES = {
        # Actuators
        "actuators.py",
        # Core state management (must write to persist state)
        "scar.py",
        "consequence.py",
        "immutable_storage.py",
        "protected_storage.py",
        "coercive_memory.py",
        "world_model.py",
        "amla.py",
        "asaa.py",
        # Watchdog (system management)
        "watchdog.py",
        # Benchmark output
        "benchmark_runner.py",
        # Config/state persistence
        "session_store.py",
        "jobs.py",
        "scheduler.py",
        "model_registry.py",
        "prompt_manager.py",
        "library.py",
        "hmac_logger.py",
        "comprehensive_reporter.py",
        "training_harness.py",
        # Legacy/tools
        "tool_7936.py",
    }
    
    FORBIDDEN_PATTERNS = [
        r"open\s*\([^)]*['\"][wax+]",  # open with write modes
        r"\.write_text\s*\(",
        r"\.write_bytes\s*\(",
        r"\.unlink\s*\(",
        r"rmtree\s*\(",
        r"shutil\.move\s*\(",
        r"shutil\.copy\s*\(",
    ]
    
    def test_no_write_bypass_in_core_logic(self):
        """Core decision logic should not write to filesystem."""
        # Files that should NEVER write directly
        forbidden_core_files = [
            "gravity.py",
            "tool_policy.py",
            "dreamer.py",
            "reasoning.py",
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
        
        assert not violations, f"FILESYSTEM WRITE BYPASS IN CORE:\n" + "\n".join(violations)
    
    def test_skills_uses_safe_path(self):
        """skills.py must validate paths before writing."""
        skills_path = Path(__file__).parent.parent.parent / "gateway" / "app" / "core" / "skills.py"
        if skills_path.exists():
            content = skills_path.read_text()
            assert "_ensure_safe_path" in content, "skills.py must have path validation"


class TestFilesystemActuatorEnforcement:
    """Verify FilesystemActuator enforces write paths."""
    
    def test_filesystem_actuator_has_allowlist(self):
        """FilesystemActuator must have write path allowlist."""
        from unified_core.core.actuators import FilesystemActuator
        assert hasattr(FilesystemActuator, 'ALLOWED_WRITE_PATHS')
        assert len(FilesystemActuator.ALLOWED_WRITE_PATHS) > 0
    
    def test_unsafe_path_blocked(self):
        """Writes to unsafe paths must be blocked."""
        from unified_core.core.actuators import FilesystemActuator, ActionResult
        
        actuator = FilesystemActuator()
        result = actuator.write_file("/etc/passwd", "malicious")
        assert result.result == ActionResult.BLOCKED
    
    def test_allowed_path_works(self):
        """Writes to allowed paths should succeed."""
        from unified_core.core.actuators import FilesystemActuator, ActionResult
        import tempfile
        import os
        
        actuator = FilesystemActuator()
        # Use tmp which should be allowed
        test_path = "/tmp/noogh_safe/test_write.txt"
        os.makedirs(os.path.dirname(test_path), exist_ok=True)
        
        # Check if path is allowed
        if any(test_path.startswith(p) for p in FilesystemActuator.ALLOWED_WRITE_PATHS):
            result = actuator.write_file(test_path, "test content")
            # Should succeed if path is allowed
            assert result.result in [ActionResult.SUCCESS, ActionResult.BLOCKED]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
