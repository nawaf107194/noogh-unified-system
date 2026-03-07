# NOOGH Framework Architecture

**Version:** 0.1  
**Status:** Foundation Established  
**Date:** 2026-01-20

---

## 1. System Overview

NOOGH is a **layered, contract-based framework** for building secure multi-agent systems.

### Core Characteristics:
- **Deterministic execution** via DAG
- **Fail-closed security** at every boundary
- **Complete auditability** through message tracing
- **Progressive isolation** (none → sandbox → lab)
- **Zero direct coupling** between components

---

## 2. Architectural Layers

The framework is strictly layered with **no layer skipping allowed**.

```
┌─────────────────────────────────────────────────┐
│ Layer 1: GATEWAY                                │
│ - User request intake                           │
│ - Authentication/authorization                  │
│ - NO execution logic                            │
└────────────────┬────────────────────────────────┘
                 ↓
┌─────────────────────────────────────────────────┐
│ Layer 2: ORCHESTRATOR                           │
│ - LLMPlanner: Request → Plan (JSON)             │
│ - DAG validation (cycles, chains)               │
│ - Risk assessment                               │
│ - Resource allocation                           │
│ - Execution coordination                        │
└────────────────┬────────────────────────────────┘
                 ↓
┌─────────────────────────────────────────────────┐
│ Layer 3: MESSAGE BUS                            │
│ - Pub/Sub routing                               │
│ - Message envelope enforcement                  │
│ - Dead Letter Queue (DLQ)                       │
│ - Complete message history                      │
│ - Trace ID propagation                          │
└────────────────┬────────────────────────────────┘
                 ↓
┌─────────────────────────────────────────────────┐
│ Layer 4: AGENTS                                 │
│ - Inherit from BaseAgent                        │
│ - Listen on MessageBus                          │
│ - Map capabilities → tools                      │
│ - Return AgentResult                            │
│ - NO decision making                            │
└────────────────┬────────────────────────────────┘
                 ↓
┌─────────────────────────────────────────────────┐
│ Layer 5: TOOL EXECUTION                         │
│ - IsolationManager: Route to none/sandbox/lab   │
│ - ResourceManager: Acquire locks/GPU            │
│ - UnifiedToolRegistry: Tool lookup              │
└────────────────┬────────────────────────────────┘
                 ↓
┌─────────────────────────────────────────────────┐
│ Layer 6: ACTUATORS                              │
│ - FilesystemActuator: Path canonicalization     │
│ - NetworkActuator: URL allowlist                │
│ - ProcessActuator: Command validation           │
│ - Real-world effects (writes, exec, network)    │
└─────────────────────────────────────────────────┘
```

---

## 3. Component Contracts

### 3.1 MessageEnvelope (Required Fields)

Every message MUST contain:

```python
{
    "message_id": str,      # Auto-generated UUID
    "trace_id": str,        # Request tracking
    "task_id": str,         # Task identifier
    "sender": str,          # Source component
    "receiver": str,        # Target component
    "type": MessageType,    # REQUEST/RESULT/ERROR/EVENT
    "risk_level": RiskLevel,
    "scopes": List[str],
    "payload": Dict,
    "timestamp": str
}
```

**Enforcement:** MessageBus rejects incomplete envelopes.

### 3.2 BaseAgent (Required Methods)

Every agent MUST:

```python
class MyAgent(BaseAgent):
    role = AgentRole.XXX         # Required
    capabilities = {"CAP1", ...} # Required
    
    async def handle(self, envelope: MessageEnvelope) -> AgentResult:
        # Contract rules:
        # 1. Pure execution (no hidden side effects)
        # 2. No direct tool calls
        # 3. No direct agent communication
        # 4. Always return AgentResult
        # 5. Never raise unhandled exceptions
        pass
```

**Enforcement:** Framework validates at initialization.

### 3.3 TaskGraph (Validation Rules)

Every plan MUST pass:

1. **Structural validation:**
   - All dependencies exist
   - No cycles (DAG property)
   - Max 10 tasks
   - Valid task IDs

2. **Security validation:**
   - No dangerous chains (write→exec, read→network)
   - Risk/isolation consistency
   - Resource constraints

**Enforcement:** `TaskGraph.validate()` MUST return `(True, None)`.

### 3.4 ToolDefinition (Required Metadata)

Every tool MUST specify:

```python
{
    "name": str,                # Unique identifier
    "actuator": ActuatorType,   # Which actuator executes it
    "security_level": str,      # SAFE/LOW/MEDIUM/HIGH/CRITICAL
    "risk_level": RiskLevel,    # SAFE/RESTRICTED/DANGEROUS
    "requires": List[str],      # Required parameters
    "description": str
}
```

**Enforcement:** UnifiedToolRegistry rejects incomplete tools.

---

## 4. Execution Flow (Standard Path)

### 4.1 Request Processing

```
User Request
    ↓
Gateway validates authentication
    ↓
Gateway → Orchestrator.process_request()
    ↓
LLMPlanner builds JSON plan
    ↓
Plan schema validation
    ↓
TaskGraph.validate() (cycles + chains)
    ↓
If invalid → REJECT (fail-closed)
    ↓
If valid → Execute
```

### 4.2 Task Execution

```
For each task in topological order:
    ↓
1. ResourceManager.acquire_resources()
    - GPU tokens
    - File locks
    - Rate limit check
    ↓
2. MessageBus.publish(task_message)
    - Routes to agent:role topic
    ↓
3. Agent.handle(envelope)
    - Maps capability → tool
    - Calls IsolationManager.execute_in_isolation()
    ↓
4. IsolationManager routes to:
    - none: Direct execution (SAFE only)
    - sandbox: Isolated process
    - lab_container: Docker (not yet implemented)
    ↓
5. UnifiedToolRegistry.execute(tool_name)
    - Actuator validation
    - AMLA checks
    - Execute
    ↓
6. Agent returns AgentResult
    ↓
7. ResourceManager.release_resources()
    ↓
8. Orchestrator aggregates results
```

---

## 5. Security Boundaries

### 5.1 Isolation Tiers

| Tier | Environment | Allowed | Forbidden |
|------|-------------|---------|-----------|
| **none** | Same process | Read-only operations | Write, exec, network |
| **sandbox** | Isolated process | Temp writes, safe exec | Network, system files |
| **lab_container** | Docker | Everything | Host access |

**Rule:** Risk level determines minimum isolation tier.

### 5.2 Path Security

**Canonicalization:** All paths MUST be resolved via `Path.resolve()`.

**Allowlist:** All paths MUST pass:
```python
canonical_path.relative_to(allowed_canonical)
```

**TOCTOU Prevention:** Use `O_NOFOLLOW` for sensitive operations.

### 5.3 Chain Prevention

**Blocked Patterns:**
- `fs.write` → `code.exec_python`
- `fs.write` → `proc.run`
- `mem.search` → `net.http_post`
- `net.http_get` → `code.exec_python`

**Detection:** TaskGraph scans execution order for sequential patterns.

---

## 6. Extension Points

### 6.1 Where Extension IS Allowed

✅ **New Agents:**
```python
class MyCustomAgent(BaseAgent):
    role = AgentRole.CUSTOM
    capabilities = {...}
    
    async def handle(self, envelope):
        # Your logic
        return AgentResult(...)
```

✅ **New Tools:**
```python
TOOL_DEFINITIONS["my_tool"] = {
    "actuator": "custom",
    "risk_level": RiskLevel.RESTRICTED,
    ...
}
```

✅ **Custom Capabilities:**
```python
agent.CAPABILITY_MAPPING["MY_CUSTOM_CAP"] = "my_tool"
```

✅ **Custom Actuators:**
```python
class MyActuator(BaseActuator):
    def execute(self, tool_name, arguments):
        # Your implementation
        pass
```

### 6.2 Where Extension IS FORBIDDEN

❌ **Cannot Change:**
- MessageEnvelope structure
- BaseAgent contract
- TaskGraph validation logic
- Fail-closed default behavior
- Security layer hierarchy

❌ **Cannot Bypass:**
- MessageBus (no direct agent communication)
- UnifiedToolRegistry (no direct tool calls)
- IsolationManager (no direct execution)
- ResourceManager (no ungoverned resource use)

---

## 7. Versioning Strategy

### 7.1 Semantic Versioning

**Format:** `MAJOR.MINOR.PATCH`

- **MAJOR:** Breaking contract changes
- **MINOR:** New features (backward compatible)
- **PATCH:** Bug fixes only

**Current:** `0.1.0` (Foundation)

### 7.2 Contract Stability

**Stable (v1.0+):**
- MessageEnvelope
- BaseAgent
- TaskGraph validation
- Security rules

**Experimental (v0.x):**
- LLM integration details
- Sandbox implementation
- Lab container specifics

---

## 8. Performance Characteristics

### 8.1 Design Trade-offs

| Aspect | Priority | Impact |
|--------|----------|--------|
| Security | 1st | +Latency, -Throughput |
| Auditability | 2nd | +Storage, +Overhead |
| Determinism | 3rd | -Flexibility |
| Performance | 4th | Acceptable for security |

**Philosophy:** Security > Performance, always.

### 8.2 Expected Overhead

- **Message routing:** ~1-5ms per message
- **DAG validation:** ~10-50ms per plan
- **Path canonicalization:** ~0.1-1ms per file
- **Isolation (sandbox):** ~100-500ms per task
- **Isolation (container):** ~1-5s per task

**Acceptable** for high-security applications.

---

## 9. Future Architecture Evolution

### Phase 1: Foundation (Complete ✅)
- Message Bus
- DAG validation
- Agent contracts
- Basic isolation

### Phase 2: Production Hardening (In Progress)
- Sandbox service
- Lab container orchestrator
- Resource scaling
- Performance optimization

### Phase 3: Advanced Features
- Distributed orchestration
- Multi-tenant support
- Advanced threat detection
- Formal verification

---

## 10. Decision Log

### Why DAG Instead of Free-form Workflows?
**Reason:** Enables cycle detection and chain validation at plan time.

### Why Message Bus Instead of Direct Calls?
**Reason:** Complete auditability and inter-agent isolation.

### Why Fail-Closed Default?
**Reason:** Security-critical systems cannot assume safety.

### Why No Agent-to-Agent Communication?
**Reason:** Prevents unmediated coordination and hidden channels.

### Why Progressive Isolation?
**Reason:** Balance between security and performance for different risk levels.

---

**Document Status:** AUTHORITATIVE  
**Maintained By:** Framework Core Team  
**Review Cycle:** Every major version
