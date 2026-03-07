
import sys
import os

# Ensure we can import from src
sys.path.append(os.getcwd())

from noogh.app.core.tools import ToolRegistry, Tool

def verify_constraints():
    print("[INFO] Initializing ToolRegistry...")
    registry = ToolRegistry()
    
    tools = registry.list_tools()
    print(f"[INFO] Loaded tools: {list(tools.keys())}")
    
    forbidden = ["shell_exec", "http_request", "http_get", "http_post", "sqlite_query", "safe_shell_exec"]
    violations = []
    
    for tool in tools:
        if tool in forbidden:
            violations.append(tool)
            
    if violations:
        print(f"[FAIL] CRITICAL SECURITY VIOLATION: Forbidden tools found in registry: {violations}")
        return False
        
    print("[PASS] No forbidden tools detected.")
    
    # Verify sandbox is active in registry
    if not registry.sandbox:
        print("[FAIL] Sandbox not initialized in registry.")
        return False
        
    print("[PASS] Sandbox initialized.")
    return True

if __name__ == "__main__":
    if verify_constraints():
        print("✅ CONSTRAINT VERIFICATION PASSED")
        sys.exit(0)
    else:
        print("❌ CONSTRAINT VERIFICATION FAILED")
        sys.exit(1)
