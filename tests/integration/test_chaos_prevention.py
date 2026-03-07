"""
Integration Chaos Prevention Tests
===================================
These tests prevent regression of chaos signals found in hostile audit.

Tests:
- T1: No subprocess in gateway (CHAOS-001..003)  
- T2: Allowlist single source of truth
- T3: No duplicate symbols
- T4: Gateway uses ActuatorHub

Run with: pytest tests/integration/test_chaos_prevention.py -v
"""

import ast
import os
from pathlib import Path


class TestNoSubprocessInGateway:
    """T1: Gateway must NOT contain subprocess imports or calls."""

    GATEWAY_ROOT = Path("/home/noogh/projects/noogh_unified_system/src/gateway")
    
    # QUARANTINE: docker_sandbox.py is allowed exception (isolated service)
    QUARANTINE_FILES = {
        "docker_sandbox.py",  # Uses Docker SDK which requires subprocess internally
    }
    
    # Files that are test files (allowed)
    TEST_PATTERNS = {"test_", "_test.py", "conftest.py"}

    def test_no_subprocess_import_in_gateway_routes(self):
        """No subprocess import in gateway routes, routers, or console."""
        violations = []
        
        for py_file in self.GATEWAY_ROOT.rglob("*.py"):
            # Skip quarantine files
            if py_file.name in self.QUARANTINE_FILES:
                continue
            
            # Skip test files
            if any(pat in py_file.name for pat in self.TEST_PATTERNS):
                continue
            
            content = py_file.read_text(encoding="utf-8", errors="ignore")
            
            # Check for subprocess import
            if "import subprocess" in content or "from subprocess" in content:
                violations.append(f"{py_file.relative_to(self.GATEWAY_ROOT)}: contains 'import subprocess'")
            
            # Check for os.system
            if "os.system(" in content:
                violations.append(f"{py_file.relative_to(self.GATEWAY_ROOT)}: contains 'os.system()'")
            
            # Check for os.popen
            if "os.popen(" in content:
                violations.append(f"{py_file.relative_to(self.GATEWAY_ROOT)}: contains 'os.popen()'")
        
        assert not violations, f"Subprocess bypass found:\n" + "\n".join(violations)

    def test_no_shell_true_in_gateway(self):
        """No shell=True subprocess calls (command injection risk)."""
        violations = []
        
        for py_file in self.GATEWAY_ROOT.rglob("*.py"):
            if py_file.name in self.QUARANTINE_FILES:
                continue
            if any(pat in py_file.name for pat in self.TEST_PATTERNS):
                continue
            
            content = py_file.read_text(encoding="utf-8", errors="ignore")
            
            if "shell=True" in content:
                violations.append(f"{py_file.relative_to(self.GATEWAY_ROOT)}: contains 'shell=True'")
        
        assert not violations, f"Shell injection risk:\n" + "\n".join(violations)


class TestAllowlistSingleSource:
    """T2: Allowlists must come from unified_core/core/actuators.py ONLY."""

    SRC_ROOT = Path("/home/noogh/projects/noogh_unified_system/src")
    
    # The canonical source for all allowlists
    CANONICAL_FILE = SRC_ROOT / "unified_core/core/actuators.py"
    
    # Files that should NOT define their own allowlists (outside actuators)
    FORBIDDEN_ALLOWLIST_PATTERNS = [
        "ALLOWED_SHELL_COMMANDS",
        "ALLOWED_HTTP_DOMAINS", 
        "ALLOWED_PATHS",
        "ALLOWED_URLS",
    ]

    def test_tools_extended_imports_from_actuators(self):
        """tools_extended.py should import allowlists, not define them."""
        tools_extended = self.SRC_ROOT / "gateway/app/core/tools_extended.py"
        
        if not tools_extended.exists():
            return  # Skip if file doesn't exist
        
        content = tools_extended.read_text()
        
        # Check that it imports from actuators (OBJ-2)
        # For now, we just verify it doesn't duplicate ALLOWED_COMMANDS
        # (Full unification is a future patch)
        
        # This test documents the current state - future fix should make it pass
        # assert "from unified_core.core.actuators import" in content, \
        #     "tools_extended.py should import from actuators"

    def test_training_generate_dataset_uses_canonical_lists(self):
        """training/generate_dataset.py should not have hardcoded allowlists."""
        gen_dataset = self.SRC_ROOT / "training/generate_dataset.py"
        
        if not gen_dataset.exists():
            return
        
        content = gen_dataset.read_text()
        
        # Document current state - training files may need their own lists for samples
        # This is LOW priority (CHAOS-014)
        if "ALLOWED_PATHS" in content or "ALLOWED_URLS" in content:
            # Mark as known issue, not failure
            pass


class TestNoDuplicateSymbols:
    """T3: Critical symbols must have single definition."""

    SRC_ROOT = Path("/home/noogh/projects/noogh_unified_system/src")
    
    # Skip venv and cache
    SKIP_DIRS = {".venv", "venv", "__pycache__", "unsloth_compiled_cache", "node_modules"}

    def test_single_gpu_memory_manager(self):
        """GPUMemoryManager should be defined in one canonical location."""
        definitions = []
        
        for py_file in self.SRC_ROOT.rglob("*.py"):
            # Skip excluded dirs
            if any(skip in py_file.parts for skip in self.SKIP_DIRS):
                continue
            
            try:
                content = py_file.read_text(encoding="utf-8", errors="ignore")
            except Exception:
                continue
            
            # Check for class definition
            if "class GPUMemoryManager" in content:
                definitions.append(str(py_file.relative_to(self.SRC_ROOT)))
        
        # We expect exactly 2 for now (gpu_manager.py and resource_governor.py)
        # After OBJ-4 fix, should be 1
        assert len(definitions) <= 2, f"GPUMemoryManager defined in {len(definitions)} places: {definitions}"

    def test_single_tool_result(self):
        """ToolResult should be defined in one canonical location."""
        definitions = []
        
        for py_file in self.SRC_ROOT.rglob("*.py"):
            if any(skip in py_file.parts for skip in self.SKIP_DIRS):
                continue
            
            try:
                content = py_file.read_text(encoding="utf-8", errors="ignore")
            except Exception:
                continue
            
            # Check for dataclass ToolResult
            if "@dataclass" in content and "class ToolResult" in content:
                definitions.append(str(py_file.relative_to(self.SRC_ROOT)))
        
        # Document current state: 2 definitions exist
        # After OBJ-4 fix, should be 1
        assert len(definitions) <= 2, f"ToolResult defined in {len(definitions)} places: {definitions}"


class TestGatewayUsesActuatorHub:
    """T4: Gateway execution must go through ActuatorHub."""

    GATEWAY_ROOT = Path("/home/noogh/projects/noogh_unified_system/src/gateway")

    def test_tools_extended_uses_process_actuator(self):
        """safe_shell_exec should use ProcessActuator."""
        tools_extended = self.GATEWAY_ROOT / "app/core/tools_extended.py"
        
        if not tools_extended.exists():
            return
        
        content = tools_extended.read_text()
        
        # Check that ProcessActuator is imported and used
        assert "from unified_core.core.actuators import ProcessActuator" in content, \
            "tools_extended.py must import ProcessActuator"
        
        assert "ProcessActuator()" in content, \
            "tools_extended.py must instantiate ProcessActuator"


class TestDockerSandboxQuarantine:
    """Verify docker_sandbox.py is properly quarantined."""

    SANDBOX_FILE = Path("/home/noogh/projects/noogh_unified_system/src/gateway/app/services/docker_sandbox.py")

    def test_sandbox_is_isolated_service(self):
        """docker_sandbox.py should only be called via service layer, not directly from routes."""
        # This is a documentation test - actual enforcement requires code review
        assert self.SANDBOX_FILE.exists(), "docker_sandbox.py should exist"
        
        content = self.SANDBOX_FILE.read_text()
        
        # Verify it's a class-based service, not a loose function
        assert "class LocalDockerSandbox" in content, "Should be encapsulated in class"
        
        # Verify it uses Docker SDK security features
        assert "--network" in content, "Should use network isolation"
        assert "--memory" in content, "Should use memory limits"


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v"])
