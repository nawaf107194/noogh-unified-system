
import sys
import os
import unittest
from unittest.mock import MagicMock

# Add src to path
sys.path.append("/home/noogh/projects/noogh_unified_system/src")

from gateway.app.core.tools import ToolRegistry
from unified_core.core.actuators import ProcessActuator, ActionResult

class TestSecurityFixes(unittest.TestCase):
    
    def test_gateway_rce_fallback_removed(self):
        print("\n[TEST] Verifying Gateway RCE Fallback Removal...")
        
        # Setup Mock Kernel with Broken Sandbox
        mock_kernel = MagicMock()
        mock_kernel.sandbox_service.execute_code.side_effect = Exception("Sandbox Connection Refused")
        
        # Initialize Tool Registry
        registry = ToolRegistry(kernel=mock_kernel, data_dir="/tmp")
        
        # Attempt RCE (Use safe code to bypass AST check, we want to hit the connection error)
        code = "print('Safe Code')"
        result = registry.get("exec_python")(code)
        
        # Verification
        print(f"Result: {result}")
        self.assertFalse(result["success"])
        self.assertIn("Sandbox Unavailable", result["error"])
        self.assertNotIn("RCE_SUCCESS", result.get("output", ""))
        print("✅ Gateway RCE Fallback successfully removed.")

    def test_unified_core_acl_enforcement(self):
        print("\n[TEST] Verifying Unified Core ACL Enforcement...")
        
        actuator = ProcessActuator(enable_amla=False) # Disable AMLA for pure ACL test
        
        # payload
        cmd = ["/usr/bin/python3", "-c", "print('owned')"]
        
        # Attempt Execution
        result = actuator.spawn(cmd)
        
        # Verification
        print(f"Result: {result.result} - {result.result_data}")
        self.assertEqual(result.result, ActionResult.BLOCKED)
        self.assertIn("Command not in allowlist", result.result_data["error"])
        print("✅ Unified Core ACL successfully blocks python3.")

if __name__ == "__main__":
    unittest.main()
