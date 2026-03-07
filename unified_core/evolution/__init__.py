"""
NOOGH Evolution Module - Self-Directed Layer
Version: 1.1.0

Components:
- EvolutionLedger: Tamper-evident audit trail with hash chain
- PolicyGate: Safety validation for proposals
- SandboxExecutor: Isolated execution environment
- PatchProposer: Structured proposal generation
"""

from .ledger import (
    EvolutionLedger,
    EvolutionProposal,
    ProposalType,
    ProposalStatus,
    get_evolution_ledger,
)

from .policy_gate import (
    PolicyGate,
    PolicyRule,
    RiskLevel,
    get_policy_gate,
)

from .sandbox import (
    SandboxExecutor,
    SandboxConfig,
    ExecutionResult,
    get_sandbox_executor,
)

from .proposer import (
    PatchProposer,
    get_patch_proposer,
)

from .goal_audit import (
    GoalAuditEngine,
    GoalMetrics,
    get_goal_audit_engine,
)

from .controller import (
    EvolutionController,
    get_evolution_controller,
)



__all__ = [
    # Ledger
    "EvolutionLedger",
    "EvolutionProposal",
    "ProposalType",
    "ProposalStatus",
    "get_evolution_ledger",
    
    # Policy Gate
    "PolicyGate",
    "PolicyRule",
    "RiskLevel",
    "get_policy_gate",
    
    # Sandbox
    "SandboxExecutor",
    "SandboxConfig",
    "ExecutionResult",
    "get_sandbox_executor",
    
    # Proposer
    "PatchProposer",
    "get_patch_proposer",
]

__version__ = "1.1.0"
