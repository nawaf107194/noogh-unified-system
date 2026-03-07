
import asyncio
import sys
import unittest
from unittest.mock import MagicMock, AsyncMock

# Add src to path
sys.path.append("/home/noogh/projects/noogh_unified_system/src")

from unified_core.core.actuators import ProcessActuator, NetworkActuator, ActionResult
from unified_core.tool_registry import UnifiedToolRegistry
from unified_core.auth import AuthContext

# Mock ApprovalQueue to fail-closed/deny by default in tests
from unified_core.decision_classifier import ApprovalQueue
ApprovalQueue.request_approval = MagicMock(return_value=False)

class TestAsyncHardening(unittest.IsolatedAsyncioTestCase):
    
    async def test_async_process_actuator_blocked(self):
        """Verify that ProcessActuator correctly blocks unauthorized commands asynchronously."""
        print("\n[TEST] Verifying Async ProcessActuator Blocking...")
        
        actuator = ProcessActuator()
        auth = AuthContext(token="test_token", user_id="test_user", scopes={"process:spawn"})
        
        # Command not in allowlist
        cmd = ["/usr/bin/python3", "-c", "print('malicious')"]
        
        from unified_core.governance.execution_envelope import GovernanceError
        
        try:
            result = await actuator.spawn(cmd, auth_context=auth)
            print(f"Result: {result.result}")
            self.assertEqual(result.result, ActionResult.BLOCKED)
        except GovernanceError as e:
            print(f"Caught expected GovernanceError: {e}")
            self.assertIn("Approval denied", str(e))
        
        print("✅ Async ProcessActuator successfully blocks unauthorized command (Governance).")

    async def test_async_network_actuator_blocked(self):
        """Verify that NetworkActuator correctly blocks unauthorized domains asynchronously."""
        print("\n[TEST] Verifying Async NetworkActuator Blocking...")
        
        actuator = NetworkActuator()
        auth = AuthContext(token="test_token", user_id="test_user", scopes={"network:http"})
        
        # URL not in allowlist
        url = "http://malicious-site.com"
        
        result = await actuator.http_request(url, method="GET", auth_context=auth)
        
        print(f"Result: {result.result}")
        self.assertEqual(result.result, ActionResult.BLOCKED)
        self.assertIn("URL not in allowlist", result.result_data["error"])
        print("✅ Async NetworkActuator successfully blocks unauthorized URL.")

    async def test_unified_tool_registry_async_execution(self):
        """Verify that UnifiedToolRegistry correctly handles async tool execution."""
        print("\n[TEST] Verifying UnifiedToolRegistry Async Execution...")
        
        registry = UnifiedToolRegistry()
        auth = AuthContext(token="admin_token", user_id="admin_user", scopes={"*"})
        
        # Test a filesystem tool (which is now async)
        # We'll mock the actuator call to avoid real FS side effects in this unit test if needed,
        # but let's try a real "no-op" or blocked one first.
        
        arguments = {"path": "/etc/shadow"} # Should be blocked by allowlist or governance
        
        result = await registry.execute("fs.read", arguments, auth_context=auth)
        
        print(f"Result: Success={result['success']}, Error={result.get('error')}")
        # It might be blocked OR it might fail because it's a high-impact operation requiring approval
        # In this test environment, it should probably be BLOCKED or fail-closed.
        self.assertFalse(result["success"])
        # Actually, it's just helpful to see it returns a dict and doesn't crash
        self.assertIsInstance(result, dict)
        print("✅ UnifiedToolRegistry correctly handled async execution.")

    async def test_auth_context_propagation(self):
        """Verify that AuthContext is required and propagated."""
        print("\n[TEST] Verifying AuthContext Propagation...")
        
        actuator = ProcessActuator()
        
        # Should raise SecurityError if no auth_context
        with self.assertRaises(Exception) as cm:
            await actuator.spawn(["ls"], auth_context=None)
        
        print(f"Caught expected error: {cm.exception}")
        self.assertIn("auth_context REQUIRED", str(cm.exception))
        print("✅ AuthContext requirement enforced.")

if __name__ == "__main__":
    unittest.main()
