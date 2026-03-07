# NOOGH Framework

**A Secure Multi-Agent Operating Framework**

[![Version](https://img.shields.io/badge/version-0.1.0-blue.svg)](https://github.com/noogh/framework)
[![Status](https://img.shields.io/badge/status-experimental-orange.svg)](https://github.com/noogh/framework)
[![License](https://img.shields.io/badge/license-Apache%202.0-green.svg)](LICENSE)

---

## What is NOOGH?

NOOGH is a **contract-based framework** for building secure, orchestrated multi-agent AI systems with:

- ✅ **DAG-based execution** (cycle detection + chain prevention)
- ✅ **Progressive isolation** (none → sandbox → lab container)
- ✅ **Fail-closed security** (unknown = blocked)
- ✅ **Message Bus architecture** (complete auditability)
- ✅ **Formal contracts** (BaseAgent, MessageEnvelope, TaskGraph)

NOOGH is designed for **high-security, production-grade** multi-agent systems—not casual chatbots.

---

## Quick Start

### Installation

```bash
# Clone repository
git clone https://github.com/noogh/framework.git
cd framework/src

# Install dependencies
pip install -r requirements.txt
```

### Your First Agent

```python
from unified_core.orchestration import BaseAgent, AgentResult, AgentRole

class MyAgent(BaseAgent):
    role = AgentRole.CODE_EXECUTOR
    capabilities = {"ANALYZE_CODE"}
    
    async def handle(self, envelope):
        # Your logic here
        return AgentResult(
            success=True,
            task_id=envelope.task_id,
            outputs={"result": "analysis complete"}
        )

# Usage
agent = MyAgent("my-agent-001")
```

### Run E2E Demo

```bash
python3 demo/e2e_multi_agent_demo.py
```

**Output:**
```
✅ Tasks executed: 4
✅ Vulnerabilities found: 2
✅ Patches generated: 2
✅ Multi-agent collaboration: SUCCESSFUL
```

---

## Core Features

### 1. DAG-Based Execution

Plans are validated as Directed Acyclic Graphs:

```python
from unified_core.orchestration import TaskGraph

graph = TaskGraph()
# Add tasks...

is_valid, error = graph.validate()
# ✅ Detects cycles
# ✅ Detects dangerous chains (write→exec)
# ✅ Enforces max 10 tasks
```

### 2. Progressive Isolation

| Risk Level | Isolation | Environment |
|-----------|-----------|-------------|
| SAFE | none | Same process |
| RESTRICTED | sandbox | Isolated process |
| DANGEROUS | lab_container | Docker |

### 3. Fail-Closed Security

```python
# Unknown tool?
→ RiskLevel = DANGEROUS
→ Isolation = LAB_CONTAINER
→ Blocked by default
```

### 4. Message Bus Architecture

All agent communication goes through MessageBus:

```python
bus = get_message_bus()

# Publish
await bus.publish(message)

# Subscribe
bus.subscribe("agent:my_agent", handler)
```

**Result:** Complete audit trail, zero direct coupling.

### 5. Chain Attack Prevention

Automatically blocks dangerous sequences:

- ❌ write → exec
- ❌ read_secrets → network
- ❌ download → exec

---

## Architecture

```
┌─────────────────────────────────────┐
│ Gateway (User requests)             │
└────────────┬────────────────────────┘
             ↓
┌─────────────────────────────────────┐
│ Orchestrator (Planning + Validation)│
└────────────┬────────────────────────┘
             ↓
┌─────────────────────────────────────┐
│ Message Bus (Pub/Sub + Audit)       │
└────────────┬────────────────────────┘
             ↓
┌─────────────────────────────────────┐
│ Agents (Workers)                    │
└────────────┬────────────────────────┘
             ↓
┌─────────────────────────────────────┐
│ Tool Execution (Isolation enforced) │
└────────────┬────────────────────────┘
             ↓
┌─────────────────────────────────────┐
│ Actuators (Real-world effects)      │
└─────────────────────────────────────┘
```

**Key Principle:** No layer may be skipped.

---

## Documentation

- [Framework Philosophy](docs/framework_philosophy.md) - Core principles
- [Architecture](docs/architecture.md) - System design
- [Public API](docs/api.md) - Developer guide
- [E2E Demo](demo/e2e_multi_agent_demo.py) - Working example

---

## Examples

### Creating an Agent

```python
from unified_core.orchestration import BaseAgent, AgentResult, AgentRole

class SecurityAuditor(BaseAgent):
    role = AgentRole.SECURITY_AUDITOR
    capabilities = {
        "SCAN_CODE_FOR_VULNERABILITIES",
        "DETECT_MALICIOUS_CODE"
    }
    
    async def handle(self, envelope):
        task = envelope.payload["task"]
        
        # Analyze code
        issues = await self.scan_code(task)
        
        return AgentResult(
            success=True,
            task_id=envelope.task_id,
            outputs={"issues": issues}
        )
```

### Building a Plan

```python
from unified_core.orchestration import LLMPlanner

planner = LLMPlanner(llm_client=my_llm)

plan = await planner.build_plan(
    "Analyze code and generate patches"
)

# Plan validated automatically:
# ✅ JSON schema
# ✅ DAG structure
# ✅ Chain detection
# ✅ Capability validation
```

### Executing a Plan

```python
from unified_core.orchestration import get_orchestrator

orchestrator = get_orchestrator()

result = await orchestrator.execute_plan(plan)

if result["success"]:
    print(f"Executed {len(result['tasks'])} tasks")
```

---

## Security Model

### Core Principles

1. **Fail-Closed:** Unknown = Blocked
2. **No Direct Tools:** All execution via IsolationManager
3. **No Direct Agent Communication:** All via MessageBus
4. **Explicit Risk:** Everything classified
5. **Security > Performance:** Always

### Enforced Contracts

**BaseAgent:**
```python
# Required attributes
role: AgentRole
capabilities: Set[str]

# Required method
async def handle(envelope) -> AgentResult
```

**MessageEnvelope:**
```python
# All fields required
message_id, trace_id, task_id
sender, receiver, type
risk_level, scopes, payload
```

**TaskGraph:**
```python
# Must pass validation
validate() → (is_valid, error)

# Checks:
- No cycles
- No dangerous chains
- Max 10 tasks
- Valid dependencies
```

---

## Comparison

| Feature | NOOGH | LangGraph | AutoGPT | Swarm |
|---------|-------|-----------|---------|-------|
| DAG Validation | ✅ | ✅ | ❌ | ❌ |
| Chain Prevention | ✅ | ❌ | ❌ | ❌ |
| Progressive Isolation | ✅ | ❌ | ❌ | ❌ |
| Fail-Closed | ✅ | ❌ | ❌ | ❌ |
| Message Bus | ✅ | Partial | ❌ | ❌ |
| Formal Contracts | ✅ | Partial | ❌ | ❌ |
| Audit Trail | ✅ | Partial | Partial | ❌ |

**NOOGH Focus:** Security-first, production-grade, formally structured.

---

## Use Cases

✅ **Ideal For:**
- Secure multi-agent systems
- Autonomous code execution
- AI-assisted DevOps
- Security automation
- Research on agent governance
- High-risk environments

❌ **Not For:**
- Casual chatbots
- Toy demos
- Prompt-only systems
- Low-trust prototypes

---

## Roadmap

### v0.1 (Current) ✅
- [x] Core orchestration
- [x] DAG validation
- [x] Chain prevention
- [x] Message Bus
- [x] BaseAgent contract
- [x] Documentation

### v0.2 (Next)
- [ ] Sandbox service
- [ ] Lab container
- [ ] Performance optimization
- [ ] Comprehensive tests
- [ ] More agent examples

### v1.0 (Future)
- [ ] Distributed orchestration
- [ ] Multi-tenant support
- [ ] Formal security proof
- [ ] Research publication

---

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

**Key Points:**
- Follow BaseAgent contract
- Write tests
- Document changes
- Respect security principles

---

## License

Apache License 2.0 - See [LICENSE](LICENSE)

---

## Citation

If you use NOOGH in research:

```bibtex
@software{noogh2026,
  title={NOOGH: A Secure Multi-Agent Operating Framework},
  author={NOOGH Team},
  year={2026},
  version={0.1.0},
  url={https://github.com/noogh/framework}
}
```

---

## Support

- **Documentation:** [docs/](docs/)
- **Examples:** [demo/](demo/)
- **Issues:** [GitHub Issues](https://github.com/noogh/framework/issues)

---

## Acknowledgments

Built with security-first principles inspired by:
- OWASP Security Standards
- NIST AI Risk Framework
- EU AI Act Requirements
- Zero Trust Architecture

---

**NOOGH Framework** - Secure Multi-Agent Systems, Done Right.

**Version:** 0.1.0 | **Status:** Experimental | **License:** Apache 2.0
