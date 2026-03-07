"""
NOOGH Autonomy Module
======================
Self-governing AI agent capabilities.

Components:
- AgentConstitution: Identity, mission, values, and red lines (FIRST layer)
- DecisionEngine: IF condition THEN action rules
- AutonomousMonitor: Self-triggered background monitoring
- IntentRegistry: Structured understanding of user intents
- SafetyPolicy: Security and permission enforcement

Usage:
    from neural_engine.autonomy import (
        get_constitution,
        get_decision_engine,
        get_monitor,
        get_intent_registry,
        get_safety_policy,
        start_autonomous_monitoring,
    )
"""

from neural_engine.autonomy.constitution import (
    AgentConstitution,
    Identity,
    Mission,
    RedLines,
    OperationalLimits,
    CoreValues,
    get_constitution,
    check_constitution,
    is_constitutional,
    ConstitutionViolation,
)

from neural_engine.autonomy.decision_engine import (
    DecisionEngine,
    get_decision_engine,
    Rule,
    Decision,
    Observation,
    ActionType,
    ActionSeverity,
)

from neural_engine.autonomy.monitor import (
    AutonomousMonitor,
    MonitorConfig,
    get_monitor,
    start_autonomous_monitoring,
    stop_autonomous_monitoring,
)

from neural_engine.autonomy.intent_registry import (
    IntentRegistry,
    Intent,
    IntentMatch,
    IntentCategory,
    get_intent_registry,
)

from neural_engine.autonomy.safety_policy import (
    SafetyPolicy,
    SafetyRule,
    PermissionLevel,
    ActionScope,
    get_safety_policy,
    is_command_safe,
)

from neural_engine.autonomy.file_awareness import (
    FileAwareness,
    FileCategory,
    FilePolicy,
    AllowedUse,
    get_file_awareness,
    check_file_use,
    get_file_category,
)

from neural_engine.autonomy.file_classifier import (
    FileAutoClassifier,
    ClassificationProposal,
    get_auto_classifier,
)

from neural_engine.autonomy.code_doctor import (
    CodeDoctor,
    CodeDiagnosis,
    get_code_doctor,
)

from neural_engine.autonomy.change_guard import (
    ChangeGuard,
    ChangeRequest,
    ChangeVerdict,
    get_change_guard,
)

from neural_engine.autonomy.self_improver import (
    SelfImprover,
    ImprovementProposal,
    ImprovementPlan,
    get_self_improver,
)

from neural_engine.autonomy.proposal_memory import (
    ProposalMemory,
    RejectionLearner,
    EnhancedSelfImprover,
    get_enhanced_improver,
)

__all__ = [
    # Constitution (FIRST layer)
    "AgentConstitution",
    "Identity",
    "Mission",
    "RedLines",
    "OperationalLimits",
    "CoreValues",
    "get_constitution",
    "check_constitution",
    "is_constitutional",
    "ConstitutionViolation",
    
    # Decision Engine
    "DecisionEngine",
    "get_decision_engine",
    "Rule",
    "Decision",
    "Observation",
    "ActionType",
    "ActionSeverity",
    
    # Monitor
    "AutonomousMonitor",
    "MonitorConfig",
    "get_monitor",
    "start_autonomous_monitoring",
    "stop_autonomous_monitoring",
    
    # Intent Registry
    "IntentRegistry",
    "Intent",
    "IntentMatch",
    "IntentCategory",
    "get_intent_registry",
    
    # Safety Policy
    "SafetyPolicy",
    "SafetyRule",
    "PermissionLevel",
    "ActionScope",
    "get_safety_policy",
    "is_command_safe",
    
    # File Awareness
    "FileAwareness",
    "FileCategory",
    "FilePolicy",
    "AllowedUse",
    "get_file_awareness",
    "check_file_use",
    "get_file_category",
    
    # File Auto-Classifier
    "FileAutoClassifier",
    "ClassificationProposal",
    "get_auto_classifier",
    
    # Code Doctor
    "CodeDoctor",
    "CodeDiagnosis",
    "get_code_doctor",
    
    # Change Guard
    "ChangeGuard",
    "ChangeRequest",
    "ChangeVerdict",
    "get_change_guard",
    
    # Self-Improver
    "SelfImprover",
    "ImprovementProposal",
    "ImprovementPlan",
    "get_self_improver",
    
    # Tier-9: Proposal Memory & Learning
    "ProposalMemory",
    "RejectionLearner",
    "EnhancedSelfImprover",
    "get_enhanced_improver",
]
