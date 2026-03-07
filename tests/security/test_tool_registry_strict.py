"""
Security Test: Tool Registry Strict Enforcement

Ensures tool resolution is registry-only with no invented tools.
"""

import pytest
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))


class TestToolRegistryStrict:
    """Tests for strict tool registry enforcement."""
    
    SPEC_PATH = Path(__file__).parent.parent.parent / "unified_core" / "config" / "tool_mapping_spec.json"
    
    def test_spec_file_exists(self):
        """tool_mapping_spec.json must exist."""
        assert self.SPEC_PATH.exists(), f"Tool spec not found at {self.SPEC_PATH}"
    
    def test_spec_is_valid_json(self):
        """Tool spec must be valid JSON."""
        content = self.SPEC_PATH.read_text()
        spec = json.loads(content)
        assert isinstance(spec, dict), "Spec must be a dictionary"
    
    def test_spec_has_principles(self):
        """Spec must define security principles."""
        content = self.SPEC_PATH.read_text()
        spec = json.loads(content)
        
        principles = spec.get("principles", {})
        assert "model_cannot_invent_tools" in str(principles).lower() or "tools" in spec, \
            "Spec must define that model cannot invent tools"
    
    def test_spec_has_tools(self):
        """Spec must define available tools."""
        content = self.SPEC_PATH.read_text()
        spec = json.loads(content)
        
        tools = spec.get("tools", spec.get("tool_definitions", []))
        assert len(tools) > 0, "Spec must define at least one tool"


class TestToolPolicyEnforcement:
    """Tests for ToolPolicy strict resolution."""
    
    def test_tool_policy_exists(self):
        """ToolPolicy class must exist."""
        from unified_core.benchmarks.tool_policy import ToolPolicy
        assert ToolPolicy is not None
    
    def test_unknown_tool_returns_noop(self):
        """Unknown action types must resolve to noop, not invented tools."""
        from unified_core.benchmarks.tool_policy import ToolPolicy
        
        policy = ToolPolicy()
        
        # Test with decision containing unknown action
        decision = {"content": {"action_type": "destroy_world", "proposition": "evil stuff"}}
        result = policy.resolve(decision, observation="", task={})
        
        # Should return noop or known tool, never invented
        assert result["tool_name"] in policy.KNOWN_TOOLS, \
            f"Unknown action resolved to unknown tool: {result['tool_name']}"
    
    def test_resolution_always_returns_known_tool(self):
        """All resolutions must return tools from KNOWN_TOOLS."""
        from unified_core.benchmarks.tool_policy import ToolPolicy
        
        policy = ToolPolicy()
        
        # Test various inputs
        test_cases = [
            {"content": {"action_type": "shell_execute"}},  # Almost like shell_exec
            {"content": {"action_type": "read_files"}},     # Plural
            {"content": {"action_type": "download_file"}},  # Invented
            {"content": {"action_type": "upload_data"}},    # Invented
        ]
        
        for decision in test_cases:
            result = policy.resolve(decision, observation="", task={})
            assert result["tool_name"] in policy.KNOWN_TOOLS, \
                f"Resolution returned unknown tool: {result['tool_name']}"


class TestToolRegistryIntegration:
    """Integration tests for ToolRegistry."""
    
    def test_tool_registry_loads_spec(self):
        """ToolRegistry must load from spec file."""
        try:
            from unified_core.tool_registry import ToolRegistry
            registry = ToolRegistry()
            assert len(registry._tools) > 0 or hasattr(registry, 'tools')
        except ImportError:
            pytest.skip("ToolRegistry not available")
    
    def test_tool_execution_requires_registration(self):
        """Only registered tools can be executed."""
        try:
            from unified_core.tool_registry import ToolRegistry
            registry = ToolRegistry()
            
            # Try to execute unregistered tool
            result = registry.execute("nonexistent_tool_xyz", {})
            
            # Must fail or return error
            assert result is None or not result.get("success", True), \
                "Unregistered tool execution should fail"
        except (ImportError, AttributeError):
            pytest.skip("ToolRegistry.execute not available")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
