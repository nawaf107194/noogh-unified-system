# NOOGH Framework Philosophy

## 1. What Is NOOGH?

NOOGH is not an agent.  
NOOGH is not a chatbot.  
NOOGH is not a workflow engine.

NOOGH is:

> A Secure Multi-Agent Operating Framework  
> for building, orchestrating, and governing intelligent agents  
> under strict security, isolation, and coordination guarantees.

NOOGH provides:

- Multi-agent orchestration
- DAG-based execution planning
- Chain attack prevention
- Unified tool governance
- Progressive isolation (none / sandbox / lab)
- Fail-closed security by default

NOOGH is designed for **systems**, not demos.

---

## 2. Core Design Principles (Non-Negotiable)

These principles are **not configurable**.

### 2.1 Fail-Closed By Default

Any ambiguity, unknown tool, unknown agent, or invalid plan:

> MUST be BLOCKED.

There is no fail-open path in the framework.

---

### 2.2 No Direct Tool Execution

No component is allowed to execute tools directly.

All tool execution MUST go through:

- RiskPolicy
- IsolationManager
- ResourceManager
- UnifiedToolRegistry

Any bypass is a security violation.

---

### 2.3 No Direct Agent-to-Agent Communication

Agents MUST NOT communicate directly.

All inter-agent communication MUST go through:

- MessageBus
- MessageEnvelope
- Orchestrator routing

This guarantees:

- Auditing
- Tracing
- Mediation
- Isolation

---

### 2.4 Orchestrator Is the Only Authority

Only the Orchestrator may:

- Build execution plans
- Validate DAGs
- Assign tasks to agents
- Allocate resources
- Decide execution order

Agents are **workers**, not decision makers.

---

### 2.5 Explicit Risk Classification

Every tool and every task MUST have:

- RiskLevel: SAFE / RESTRICTED / DANGEROUS
- IsolationLevel: NONE / SANDBOX / LAB_CONTAINER

Unknown tools are always:

> RiskLevel = DANGEROUS  
> Isolation = LAB_CONTAINER  

Fail-closed.

---

### 2.6 Security Over Performance

If there is a conflict between:

- Security
- Performance
- Convenience

Security ALWAYS wins.

---

## 3. What NOOGH Is NOT

NOOGH is NOT:

- A prompt engineering library
- A chat framework
- A tool-calling wrapper
- A scripting engine
- A workflow DSL

NOOGH does NOT:

- Allow free tool usage
- Allow ungoverned execution
- Allow implicit permissions
- Allow hidden chains
- Allow unsafe defaults

---

## 4. Architectural Boundaries

The framework is strictly layered:

1. **Gateway Layer**  
   - Accepts user requests  
   - No execution  

2. **Orchestrator Layer**  
   - Planning  
   - DAG validation  
   - Risk assessment  
   - Resource arbitration  

3. **Message Bus Layer**  
   - All inter-agent communication  
   - Tracing and audit  

4. **Agent Layer**  
   - Pure workers  
   - No orchestration  
   - No direct tools  

5. **Tool Layer**  
   - UnifiedToolRegistry only  
   - Isolation enforced  

6. **Actuator Layer**  
   - Real-world effects  
   - Allowlist + canonicalization  

No layer may skip another.

---

## 5. Contract-Based Framework

NOOGH is a contract-driven framework.

Every component must obey:

- Message contract (MessageEnvelope)
- Agent contract (BaseAgent)
- Tool contract (ToolDefinition)
- Execution contract (TaskGraph)
- Security contract (RiskPolicy + Isolation)

Breaking a contract is a framework-level error.

---

## 6. Target Use Cases

NOOGH is designed for:

- Secure multi-agent systems
- Autonomous code execution systems
- AI-assisted DevOps
- Security automation
- Research on agent governance
- High-risk automation environments

NOOGH is NOT designed for:

- Casual chatbots
- Toy agents
- Low-trust environments
- Prompt-only systems

---

## 7. Long-Term Vision

NOOGH aims to become:

> The reference operating framework  
> for secure, orchestrated, multi-agent AI systems.

With:

- Formal security model
- Auditable execution
- Provable chain prevention
- Deterministic orchestration
- Research-grade architecture

---

## 8. Final Rule

If a feature violates:

- Security
- Determinism
- Auditability
- Isolation
- Governance

Then:

> The feature MUST NOT be implemented.

This rule overrides all others.
