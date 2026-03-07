# NOOGH Public API v0.1

**Status:** Initial Release  
**Stability:** Experimental  
**Date:** 2026-01-20

---

## 1. Overview

This document defines the **official public API** for NOOGH Framework v0.1.

**Stability Guarantee:**
- ✅ **Core Contracts:** Stable within v0.x (MessageEnvelope, BaseAgent)
- ⚠️ **Implementation Details:** May change between minor versions
- ❌ **Internal APIs:** Not guaranteed (do not use)

---

## 2. Core Imports

### 2.1 Essential Contracts

```python
from unified_core.orchestration import (
    # Agent Contract
    BaseAgent,
    AgentResult,
    AgentRole,
    
    # Message Contract
    MessageEnvelope,
    MessageType,
    RiskLevel,
    
    # Execution Contract
    TaskGraph,
    TaskNode,
    
    # Planning
    LLMPlanner,
    PlanBuildError,
)
```

### 2.2 Agent Development

```python
from unified_core.orchestration import (
    # Base Workers
    AgentWorker,
    
    # Message Bus
    get_message_bus,
    MessageBus,
)
```

### 2.3 Tool Development

```python
from unified_core.tools import (
    # Tool Definitions
    TOOL_DEFINITIONS,
    get_tool_definition,
)

from unified_core.tool_registry import (
    # Registry
    get_unified_registry,
)
```

---

## 3. Agent Development API

### 3.1 Creating a Custom Agent

**Minimum Implementation:**

```python
from unified_core.orchestration import BaseAgent, AgentResult, AgentRole

class MyAgent(BaseAgent):
    # Required class attributes
    role = AgentRole.CODE_EXECUTOR  # Choose appropriate role
    capabilities = {
        "MY_CUSTOM_CAPABILITY",
        "ANOTHER_CAPABILITY"
    }
    
    async def handle(self, envelope: MessageEnvelope) -> AgentResult:
        """
        Handle incoming task.
        
        CONTRACT RULES:
        - Must be pure (no hidden side effects)
        - Must NOT call tools directly
        - Must NOT communicate with other agents
        - Must return AgentResult
        - Must catch all exceptions
        """
        try:
            task = envelope.payload.get("task")
            
            # Your logic here
            result = await self.process_task(task)
            
            return AgentResult(
                success=True,
                task_id=envelope.task_id,
                outputs={"result": result}
            )
            
        except Exception as e:
            return AgentResult(
                success=False,
                task_id=envelope.task_id,
                outputs={},
                error=str(e)
            )
    
    async def process_task(self, task):
        # Your implementation
        pass

# Usage
agent = MyAgent("my-agent-001")
```

### 3.2 Using AgentWorker Helper

**Simplified Development:**

```python
from unified_core.orchestration import AgentWorker, AgentRole

class MySimpleAgent(AgentWorker):
    # AgentWorker provides:
    # - Message Bus integration
    # - Capability mapping
    # - Tool execution via IsolationManager
    
    CAPABILITY_MAPPING = {
        "MY_READ_CAPABILITY": "fs.read",
        "MY_WRITE_CAPABILITY": "fs.write",
    }
    
    def __init__(self):
        super().__init__(AgentRole.FILE_MANAGER)

# Start agent
agent = MySimpleAgent()
agent.start()  # Subscribes to MessageBus
```

### 3.3 Agent Registration

```python
from unified_core.orchestration import get_orchestrator

orchestrator = get_orchestrator()
orchestrator.register_agent(agent)
```

---

## 4. Plan Building API

### 4.1 Using LLMPlanner

```python
from unified_core.orchestration import LLMPlanner, StubLLMClient

# Create planner
planner = LLMPlanner(llm_client=StubLLMClient())

# Build plan from user request
try:
    plan = await planner.build_plan(
        user_request="Analyze code for security issues"
    )
    
    print(f"Plan ID: {plan['plan_id']}")
    print(f"Tasks: {len(plan['tasks'])}")
    
except PlanBuildError as e:
    print(f"Plan rejected: {e}")
```

### 4.2 Plan Validation

```python
from unified_core.orchestration import TaskGraph

# Validate plan manually
graph = build_task_graph_from_plan(plan)

is_valid, error = graph.validate()

if not is_valid:
    print(f"Plan invalid: {error}")
else:
    execution_order = graph.topological_sort()
    print(f"Execution order: {execution_order}")
```

---

## 5. Message Bus API

### 5.1 Publishing Messages

```python
from unified_core.orchestration import get_message_bus, MessageEnvelope, MessageType

bus = get_message_bus()

# Create message
message = MessageEnvelope(
    trace_id="trace-001",
    task_id="task-001",
    sender="orchestrator",
    receiver="agent:code_executor",
    type=MessageType.REQUEST,
    payload={"task": {...}}
)

# Publish
await bus.publish(message)
```

### 5.2 Subscribing to Topics

```python
async def my_handler(envelope: MessageEnvelope):
    print(f"Received: {envelope.message_id}")

# Subscribe
bus.subscribe("agent:my_agent", my_handler)

# Unsubscribe later
bus.unsubscribe("agent:my_agent", my_handler)
```

### 5.3 Request-Reply Pattern

```python
# Send request and wait for reply
reply = await bus.request(
    message=my_message,
    timeout_ms=5000
)

if reply:
    print(f"Got reply: {reply.payload}")
else:
    print("Timeout")
```

---

## 6. Tool Registry API

### 6.1 Registering Custom Tools

```python
from unified_core.tools import TOOL_DEFINITIONS
from unified_core.orchestration import RiskLevel

TOOL_DEFINITIONS["my_custom_tool"] = {
    "name": "my_custom_tool",
    "actuator": "custom",
    "security_level": "MEDIUM",
    "risk_level": RiskLevel.RESTRICTED,
    "requires": ["input_data"],
    "description": "My custom tool"
}
```

### 6.2 Executing Tools (Through Isolation)

```python
from unified_core.orchestration import get_isolation_manager

isolation = get_isolation_manager()

result = await isolation.execute_in_isolation(
    tool_name="fs.read",
    arguments={"path": "/tmp/file.txt"},
    isolation="none",  # or "sandbox" or "lab_container"
    timeout_ms=10000
)

if result["success"]:
    print(result["output"])
```

---

## 7. Orchestration API

### 7.1 Full Request Processing

```python
from unified_core.orchestration import get_orchestrator

orchestrator = get_orchestrator()

# Process user request end-to-end
result = await orchestrator.process_request(
    user_request="Read file and analyze it",
    user_id="user-001"
)

print(f"Success: {result['success']}")
print(f"Results: {result['results']}")
```

### 7.2 Manual Plan Execution

```python
# Execute a pre-built plan
execution_result = await orchestrator.execute_plan(
    plan=my_plan,
    trace_id="trace-002"
)
```

---

## 8. Configuration API

### 8.1 Resource Limits

```python
from unified_core.orchestration import get_resource_manager

resources = get_resource_manager()

# Configure GPU limits
resources.GPU_LIMITS["high"] = 2  # Max 2 concurrent high-GPU tasks

# Configure rate limiting
resources.min_tool_interval_ms = 2000  # 2s between tool calls
```

### 8.2 Security Policy

```python
from unified_core.orchestration import RISK_POLICY

# Add tool to safe list
RISK_POLICY.SAFE_TOOLS.add("my_safe_tool")

# Add dangerous chain pattern
RISK_POLICY.DANGEROUS_CHAINS.append(
    ("my_write_tool", "my_exec_tool", "custom_chain")
)
```

---

## 9. Error Handling

### 9.1 Exception Types

```python
from unified_core.orchestration import (
    PlanBuildError,       # Plan validation failed
    GraphValidationError, # DAG validation failed
    ResourceError,        # Resource exhaustion
    IsolationError,       # Isolation failure
)

try:
    plan = await planner.build_plan(request)
except PlanBuildError as e:
    # Handle plan errors
    print(f"Plan invalid: {e}")
except ResourceError as e:
    # Handle resource errors
    print(f"Resources unavailable: {e}")
```

### 9.2 AgentResult Error Handling

```python
result = await agent.handle(envelope)

if not result.success:
    if result.blocked:
        print("Operation blocked by security policy")
    else:
        print(f"Error: {result.error}")
```

---

## 10. Testing Utilities

### 10.1 Stub LLM Client

```python
from unified_core.orchestration import StubLLMClient

# For testing without real LLM
stub_llm = StubLLMClient()

# Returns predefined safe plan
plan = await stub_llm.generate("test request")
```

### 10.2 Mock Message Bus

```python
from unified_core.orchestration import MessageBus

# Create isolated bus for testing
test_bus = MessageBus()

# Your tests...
```

---

## 11. Best Practices

### 11.1 Agent Development

✅ **DO:**
- Inherit from `BaseAgent` or `AgentWorker`
- Catch all exceptions in `handle()`
- Return structured `AgentResult`
- Log significant actions
- Validate inputs

❌ **DON'T:**
- Call tools directly (use `IsolationManager`)
- Communicate with agents directly (use `MessageBus`)
- Raise unhandled exceptions
- Modify global state
- Skip contract validation

### 11.2 Plan Building

✅ **DO:**
- Use abstract capabilities (not tool names)
- Validate plans before execution
- Set appropriate risk levels
- Respect max 10 tasks limit
- Check for dangerous chains

❌ **DON'T:**
- Include tool names in plans
- Skip DAG validation
- Exceed task limits
- Create write→exec chains
- Use fail-open logic

### 11.3 Security

✅ **DO:**
- Canonicalize all file paths
- Use allowlists (not denylists)
- Fail-closed on unknown inputs
- Log security events
- Respect isolation boundaries

❌ **DON'T:**
- Trust user input
- Skip path validation
- Bypass isolation
- Ignore security warnings
- Use eval() or exec()

---

## 12. Migration Guide

### From v0.0 → v0.1

**Breaking Changes:**
- `AgentWorker` now requires explicit role
- `MessageEnvelope` requires all fields
- `TaskGraph.validate()` is mandatory

**Migration Steps:**

1. Update agent initialization:
```python
# Old
agent = MyAgent()

# New
agent = MyAgent("agent-id-001")
```

2. Add role to agents:
```python
class MyAgent(BaseAgent):
    role = AgentRole.CODE_EXECUTOR  # Add this
    capabilities = {...}
```

3. Validate plans:
```python
# Add before execution
is_valid, error = graph.validate()
if not is_valid:
    raise PlanBuildError(error)
```

---

## 13. Versioning

**Current Version:** `0.1.0`

**Stability:**
- v0.x: Experimental (may have breaking changes in minor versions)
- v1.x: Stable (breaking changes only in major versions)

**Deprecation Policy:**
- Deprecated features: 2 minor versions notice
- Removed in: Next major version

---

## 14. Support

**Documentation:**
- `docs/framework_philosophy.md` - Core principles
- `docs/architecture.md` - System design
- `docs/api.md` - This document

**Examples:**
- `demo/e2e_multi_agent_demo.py` - Complete workflow
- `agents/code_executor_agent.py` - Agent example
- `agents/file_manager_agent.py` - Agent example

---

**API Status:** INITIAL RELEASE  
**Review Date:** 2026-02-20  
**Feedback:** Report issues to framework maintainers
