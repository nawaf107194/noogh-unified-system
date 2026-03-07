
import os
import sys
from unittest.mock import MagicMock

# Add src to path
sys.path.append(os.path.join(os.getcwd(), "src"))

from noogh.app.core.agent_kernel import AgentKernel
from noogh.app.core.auth import AuthContext
from noogh.app.core.tools import ToolRegistry

def test_golden_agent_flow():
    print("=== Verifying Golden Agent Flow ===")
    
    # 1. Initialize Kernel
    mock_brain = MagicMock()
    kernel = AgentKernel(brain=mock_brain, strict_protocol=True)
    
    # 2. Mock Brain Response (Multi-turn)
    # Turn 1: Decide to Plan
    resp_1 = """THINK:
<CRITICAL: Deep cognitive step.>
I need to plan first.
ACT:
```python
create_plan(task="Refactor Database Layer")
```
REFLECT:
Executing plan creation.
"""
    # Turn 2: Completion
    resp_2 = """THINK:
<CRITICAL: Deep cognitive step.>
Plan is created. Task done.
ACT:
```python
print("Plan created")
```
REFLECT:
Task complete.
ANSWER: Plan created successfully.
"""
    # Provide enough responses for potential retries
    # Strip them to be safe
    mock_brain.generate.side_effect = [r.strip() for r in [resp_1, resp_2, resp_2, resp_2, resp_2]]
    
    # 3. Process Task
    auth = AuthContext(token="test_token", scopes={"*"}) # Full access
    task = "Refactor Database Layer"
    
    print(f"Task: {task}")
    print("Agent Thinking...")
    
    result = kernel.process(task, auth=auth)
    
    # 4. Verify Results
    print(f"\nResult Success: {result.success}")
    print(f"Result Answer: {result.answer}")
    print(f"Result Error: {result.error}")
    
    # Check if plan file was created
    plan_path = os.path.join(os.getcwd(), "CURRENT_PLAN.md")
    if os.path.exists(plan_path):
        print(f"✓ Plan file created at: {plan_path}")
        with open(plan_path, "r") as f:
            print(f"--- Plan Content ---\n{f.read(200)}...")
            
        # Cleanup
        os.remove(plan_path)
    else:
        print("❌ Plan file NOT created.")
        sys.exit(1)

    if result.success and "plan created" in result.answer.lower():
        print("\n✅ Golden Agent Verification PASSED")
    else:
        print("\n❌ Verification FAILED")
        sys.exit(1)

if __name__ == "__main__":
    test_golden_agent_flow()
