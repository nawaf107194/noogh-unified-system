"""
Governed Spine - Minimal Security Architecture

DESIGN PRINCIPLES:
- Zero breaking changes
- Wrapping only, no internal modifications
- Feature flags for gradual rollout
- Fail-safe defaults

Components:
- ExecutionEnvelope: Context manager wrapper
- DecisionGovernor: Uses existing classifier
- ObservabilityBus: Event pub/sub
- FeatureFlags: Gradual rollout control
"""

from unified_core.governance.execution_envelope import (
    execution_envelope,
    async_execution_envelope,
    ExecutionEnvelope,
    AsyncExecutionEnvelope,
    GovernanceError
)
from unified_core.governance.governor import (
    get_governor,
    DecisionGovernor,
    GovernanceDecision
)
from unified_core.governance.events import (
    get_observability_bus,
    publish_event,
    GovernanceEvent,
    GovernanceEventType
)
from unified_core.governance.feature_flags import flags


__all__ = [
    "execution_envelope",
    "async_execution_envelope",
    "ExecutionEnvelope",
    "AsyncExecutionEnvelope",
    "GovernanceError",
    "get_governor",
    "DecisionGovernor",
    "GovernanceDecision",
    "get_observability_bus",
    "publish_event",
    "GovernanceEvent",
    "GovernanceEventType",
    "flags",
]
