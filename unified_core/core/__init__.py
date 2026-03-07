"""
Core AI Components - Hardened v2.3
"""

from .world_model import WorldModel, Belief, Prediction, Observation, Falsification
from .consequence import ConsequenceEngine, Action, Outcome, Constraint
from .coercive_memory import AdvisoryMemory, CoerciveMemory, MemoryVerdict, Blocker, Penalty
from .scar import FailureRecord, ScarTissue, Scar, Failure
from .gravity import DecisionScorer, GravityWell, Decision, DecisionContext, Goal, ActionProposal
from .world_init import seed_world_model, initialize_ai_core_knowledge, FOUNDATIONAL_BELIEFS

from .asaa import (
    AdversarialSelfAuditAgent, 
    ActionRequest, 
    AuditResult, 
    AuditVerdict,
    get_asaa,
    require_asaa_approval
)
from .amla import (
    AdversarialMilitaryAuditAgent,
    AMLAActionRequest,
    AMLAAuditResult,
    AMLAVerdict,
    get_amla,
    require_amla_audit
)
from .amla_enforcer import (
    AMLAEnforcer,
    enforce_amla,
    amla_protected,
    AMLAEnforcementError,
    AMLAAcknowledgmentRequired,
    AMLAEnforcedMixin,
    is_strict_mode
)

__all__ = [
    "WorldModel", "Belief", "Prediction", "Observation", "Falsification",
    "ConsequenceEngine", "Action", "Outcome", "Constraint",
    "AdvisoryMemory", "CoerciveMemory", "MemoryVerdict", "Blocker", "Penalty",
    "FailureRecord", "ScarTissue", "Scar", "Failure",
    "DecisionScorer", "GravityWell", "Decision", "DecisionContext", "Goal", "ActionProposal",
    "seed_world_model", "initialize_ai_core_knowledge", "FOUNDATIONAL_BELIEFS",

    "AdversarialSelfAuditAgent", "ActionRequest", "AuditResult", "AuditVerdict",
    "get_asaa", "require_asaa_approval",
    "AdversarialMilitaryAuditAgent", "AMLAActionRequest", "AMLAAuditResult", "AMLAVerdict",
    "get_amla", "require_amla_audit",
    "AMLAEnforcer", "enforce_amla", "amla_protected", "AMLAEnforcementError", "AMLAAcknowledgmentRequired",
    "AMLAEnforcedMixin", "is_strict_mode"
]
