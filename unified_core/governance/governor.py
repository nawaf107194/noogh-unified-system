"""
Decision Governor

Uses existing decision_classifier functions to determine:
- Allow
- Require approval
- Block

ZERO coupling to subsystems.
"""

import logging
import time
from typing import Optional
from enum import Enum
from unified_core.neural_bridge import get_neural_bridge, NeuralRequest

from unified_core.decision_classifier import (
    classify_decision,
    requires_approval,
    DecisionImpact,
    ApprovalQueue,
    ApprovalRequest,
    generate_decision_id
)
from unified_core.governance.feature_flags import flags
from unified_core.governance.events import (
    publish_event,
    GovernanceEventType
)


logger = logging.getLogger("unified_core.governance.governor")


class GovernanceDecision(Enum):
    """Governance decision outcomes."""
    ALLOW = "allow"
    REQUIRE_APPROVAL = "require_approval"
    BLOCK = "block"


class DecisionGovernor:
    """
    Decision governor using existing classifier.
    
    DESIGN:
    - Uses classify_decision (already exists)
    - Uses ApprovalQueue (already exists)
    - No new logic, just orchestrates existing components
    """
    
    def classify(self, component: str) -> DecisionImpact:
            """
            Classify operation impact.
        
            Args:
                component: Component identifier (e.g., "process.spawn")
        
            Returns:
                DecisionImpact level
            """
            if not isinstance(component, str):
                raise TypeError("The 'component' argument must be a string.")
            if not component:
                raise ValueError("The 'component' argument cannot be an empty string.")
        
            try:
                return classify_decision(component)
            except Exception as e:
                self.logger.error(f"Failed to classify decision for component '{component}': {str(e)}")
                raise
    
    def decide(
        self,
        component: str,
        user_id: str,
        params: Optional[dict] = None
    ) -> GovernanceDecision:
        """
        Make governance decision.
        
        Returns:
            ALLOW, REQUIRE_APPROVAL, or BLOCK
        """
        # Feature flag check
        if not flags.APPROVAL_GATE_ENABLED:
            # Approval gate disabled → always allow
            return GovernanceDecision.ALLOW
        
        # Classify impact
        impact = self.classify(component)
        
        # Decision logic
        if impact in [DecisionImpact.LOW, DecisionImpact.MEDIUM]:
            return GovernanceDecision.ALLOW
        
        elif impact in [DecisionImpact.HIGH, DecisionImpact.CRITICAL]:
            # High/Critical: require approval
            publish_event(
                GovernanceEventType.APPROVAL_REQUESTED,
                component=component,
                user_id=user_id,
                impact=impact.value,
                params=params
            )
            return GovernanceDecision.REQUIRE_APPROVAL
        
        else:
            # Unknown impact → fail-closed
            logger.warning(f"Unknown impact level: {impact}")
            return GovernanceDecision.BLOCK
    
    async def request_approval(
        self,
        component: str,
        user_id: str,
        params: Optional[dict] = None,
        timeout: float = 300.0
    ) -> bool:
        """
        Request human approval (ASYNC).
        
        Args:
            component: Component identifier
            user_id: User requesting operation
            params: Operation parameters
            timeout: Approval timeout (seconds)
        
        Returns:
            True if approved, False if denied/timeout
        """
        decision_id = generate_decision_id(component, params or {}, user_id)
        
        request = ApprovalRequest(
            decision_id=decision_id,
            action_type=component,
            impact=self.classify(component),
            params=params or {},
            justification=f"User {user_id} requesting {component}",
            user_id=user_id,
            timestamp=time.time()
        )
        
        # In a real async system, we would publish to a queue and wait for a response
        # Here we bridge to the existing ApprovalQueue blocking call via run_in_executor
        # to avoid blocking the main event loop while waiting for human.
        import asyncio
        loop = asyncio.get_running_loop()
        
        approved = await loop.run_in_executor(
            None,
            ApprovalQueue.request_approval,
            request,
            timeout
        )
        
        # Publish result
        if approved:
            publish_event(
                GovernanceEventType.APPROVAL_GRANTED,
                component=component,
                user_id=user_id
            )
        else:
            publish_event(
                GovernanceEventType.APPROVAL_DENIED,
                component=component,
                user_id=user_id
            )
        
        return approved

    def request_approval_sync(
            self,
            component: str,
            user_id: str,
            params: Optional[dict] = None,
            timeout: float = 300.0
        ) -> bool:
            """
            Request human approval (BLOCKING).
        
            Args:
                component: Component identifier
                user_id: User requesting operation
                params: Operation parameters
                timeout: Approval timeout (seconds)
        
            Returns:
                True if approved, False if denied/timeout
            """
            if not isinstance(component, str):
                raise ValueError("Component must be a string.")
            if not isinstance(user_id, str):
                raise ValueError("User ID must be a string.")
            if params is not None and not isinstance(params, dict):
                raise ValueError("Params must be a dictionary or None.")
            if not isinstance(timeout, (int, float)) or timeout <= 0:
                raise ValueError("Timeout must be a positive number.")

            try:
                decision_id = generate_decision_id(component, params or {}, user_id)
            except Exception as e:
                logging.error(f"Failed to generate decision ID: {e}")
                return False

            try:
                request = ApprovalRequest(
                    decision_id=decision_id,
                    action_type=component,
                    impact=self.classify(component),
                    params=params or {},
                    justification=f"User {user_id} requesting {component}",
                    user_id=user_id,
                    timestamp=time.time()
                )
            except Exception as e:
                logging.error(f"Failed to create approval request: {e}")
                return False

            try:
                # Request approval (BLOCKING)
                approved = ApprovalQueue.request_approval(request, timeout=timeout)
            except Exception as e:
                logging.error(f"Approval request failed: {e}")
                return False

            try:
                # Publish result
                if approved:
                    publish_event(
                        GovernanceEventType.APPROVAL_GRANTED,
                        component= component,
                        user_id= user_id
                    )
                else:
                    publish_event(
                        GovernanceEventType.APPROVAL_DENIED,
                        component= component,
                        user_id= user_id
                    )
            except Exception as e:
                logging.error(f"Failed to publish event: {e}")

            return approved

    async def consult_brain(
        self,
        component: str,
        brief: str,
        urgency: float = 0.5
    ) -> str:
        """
        Request strategic advice from the Brain (LLM).
        """
        publish_event(
            GovernanceEventType.STRATEGIC_CONSULTATION_REQUESTED,
            component=component,
            brief=brief,
            urgency=urgency
        )
        
        bridge = get_neural_bridge()
        request = NeuralRequest(
            query=f"STRATEGIC CONSULTATION: {brief}",
            urgency=urgency,
            context={"source": component, "mode": "strategy"}
        )
        
        response = await bridge.think_with_authority(request)
        return response.content if response.success else "Consultation failed: Brain offline."


# Global singleton
_governor = DecisionGovernor()


def get_governor() -> DecisionGovernor:
    """Get global decision governor."""
    return _governor
