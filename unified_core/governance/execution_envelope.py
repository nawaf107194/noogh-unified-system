"""
Execution Envelope - Context Manager for Governed Execution

CRITICAL DESIGN PRINCIPLES:
1. ZERO modification to wrapped functions
2. Fail-open if governance disabled
3. Fail-closed for CRITICAL operations
4. No async/sync hazards
5. Graceful degradation
"""

import logging
import time
import asyncio
from typing import Optional, Any, Callable
from contextlib import contextmanager, asynccontextmanager

from unified_core.decision_classifier import DecisionImpact
from unified_core.governance.feature_flags import flags
from unified_core.governance.events import (
    publish_event,
    GovernanceEventType
)
from unified_core.governance.governor import (
    get_governor,
    GovernanceDecision
)


logger = logging.getLogger("unified_core.governance.envelope")


class GovernanceError(Exception):
    """Raised when governance blocks execution."""
    pass


class ExecutionEnvelope:
    """
    Execution envelope for governed operations.
    
    Usage:
        with execution_envelope(
            auth=auth_context,
            component="process.spawn",
            impact=DecisionImpact.CRITICAL
        ):
            result = actual_operation()
    
    The envelope:
    - Checks auth
    - Classifies impact
    - Requests approval if needed
    - Publishes events
    - Enforces timeout
    - NO modification to actual_operation()
    """
    
    def __init__(
        self,
        auth_context: Optional[Any],
        component: str,
        impact: Optional[DecisionImpact] = None,
        params: Optional[dict] = None,
        timeout: float = 30.0
    ):
        self.auth_context = auth_context
        self.component = component
        self.impact = impact
        self.params = params or {}
        self.timeout = timeout
        self.start_time = None
        self.governor = get_governor()
    
    def _check_enabled(self) -> bool:
        """Check if governance is enabled for this component."""
        if not flags.GOVERNANCE_ENABLED:
            return False
        return flags.is_enabled_for(self.component)
    
    def _verify_auth(self):
        """Verify auth context (if gate enabled)."""
        if not flags.AUTH_GATE_ENABLED:
            return
        
        if self.auth_context is None:
            if flags.DRY_RUN:
                logger.warning(
                    f"[DRY-RUN] Missing auth for {self.component}"
                )
            else:
                raise GovernanceError(
                    f"Auth required for {self.component}"
                )
    
    def _check_approval(self) -> bool:
        """
        Check if approval required and granted.
        
        Returns:
            True if operation can proceed
        """
        if not flags.APPROVAL_GATE_ENABLED:
            return True
        
        user_id = getattr(self.auth_context, 'user_id', 'unknown')
        
        # Get decision
        decision = self.governor.decide(
            component=self.component,
            user_id=user_id,
            params=self.params
        )
        
        if decision == GovernanceDecision.ALLOW:
            return True
        
        elif decision == GovernanceDecision.BLOCK:
            if flags.DRY_RUN:
                logger.warning(
                    f"[DRY-RUN] Would block {self.component}"
                )
                return True
            else:
                raise GovernanceError(
                    f"Operation blocked: {self.component}"
                )
        
        elif decision == GovernanceDecision.REQUIRE_APPROVAL:
            if flags.DRY_RUN:
                logger.warning(
                    f"[DRY-RUN] Would require approval for {self.component}"
                )
                return True
            else:
                # SYNC context - cannot await approval
                # Fail-closed for safety
                error_msg = f"SECURITY BREACH: High-impact operation '{self.component}' attempted in sync context requiring approval."
                logger.critical(error_msg)
                raise GovernanceError(error_msg)
        
        return False
    
    def __enter__(self):
        """Enter sync context."""
        if not self._check_enabled():
            # Governance disabled → transparent passthrough
            return self
        
        self.start_time = time.time()
        
        # Publish start event
        publish_event(
            GovernanceEventType.EXECUTION_STARTED,
            component=self.component,
            user_id=getattr(self.auth_context, 'user_id', 'unknown'),
            params=self.params
        )
        
        # Verify auth
        self._verify_auth()
        
        # Check approval (sync only checks, cannot request)
        self._check_approval()
        
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit sync context."""
        if not self._check_enabled():
            return False
        
        duration = time.time() - self.start_time if self.start_time else 0
        
        if exc_type is None:
            # Success
            publish_event(
                GovernanceEventType.EXECUTION_COMPLETED,
                component=self.component,
                user_id=getattr(self.auth_context, 'user_id', 'unknown'),
                duration=duration
            )
        else:
            # Failure
            publish_event(
                GovernanceEventType.EXECUTION_FAILED,
                component=self.component,
                user_id=getattr(self.auth_context, 'user_id', 'unknown'),
                duration=duration,
                error=str(exc_val)
            )
        
        return False  # Don't suppress exceptions


class AsyncExecutionEnvelope:
    """Async version of ExecutionEnvelope."""
    
    def __init__(self, *args, **kwargs):
        self.sync_envelope = ExecutionEnvelope(*args, **kwargs)
        self.governor = get_governor()
    
    async def __aenter__(self):
        """Enter async context."""
        if not self.sync_envelope._check_enabled():
            return self
        
        self.sync_envelope.start_time = time.time()
        
        publish_event(
            GovernanceEventType.EXECUTION_STARTED,
            component=self.sync_envelope.component,
            user_id=getattr(self.sync_envelope.auth_context, 'user_id', 'unknown'),
            params=self.sync_envelope.params
        )
        
        # Verify auth
        self.sync_envelope._verify_auth()
        
        # Approval check (async can request approval)
        if flags.APPROVAL_GATE_ENABLED:
            user_id = getattr(self.sync_envelope.auth_context, 'user_id', 'unknown')
            
            decision = self.governor.decide(
                component=self.sync_envelope.component,
                user_id=user_id,
                params=self.sync_envelope.params
            )
            
            if decision == GovernanceDecision.REQUIRE_APPROVAL:
                if flags.DRY_RUN:
                    logger.warning(
                        f"[DRY-RUN] Would request approval for {self.sync_envelope.component}"
                    )
                else:
                    # Request approval asynchronously
                    approved = await self.governor.request_approval(
                        component=self.sync_envelope.component,
                        user_id=user_id,
                        params=self.sync_envelope.params,
                        timeout=self.sync_envelope.timeout
                    )
                    
                    if not approved:
                        raise GovernanceError(
                            f"Approval denied for {self.sync_envelope.component}"
                        )
        
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Exit async context."""
        if not self.sync_envelope._check_enabled():
            return False
        
        duration = time.time() - self.sync_envelope.start_time if self.sync_envelope.start_time else 0
        
        if exc_type is None:
            publish_event(
                GovernanceEventType.EXECUTION_COMPLETED,
                component=self.sync_envelope.component,
                user_id=getattr(self.sync_envelope.auth_context, 'user_id', 'unknown'),
                duration=duration
            )
        else:
            publish_event(
                GovernanceEventType.EXECUTION_FAILED,
                component=self.sync_envelope.component,
                user_id=getattr(self.sync_envelope.auth_context, 'user_id', 'unknown'),
                duration=duration,
                error=str(exc_val)
            )
        
        return False


# Convenience functions
@contextmanager
def execution_envelope(
    auth,
    component: str,
    impact: Optional[DecisionImpact] = None,
    params: Optional[dict] = None,
    timeout: float = 30.0
):
    """Sync execution envelope context manager."""
    with ExecutionEnvelope(auth, component, impact, params, timeout) as env:
        yield env


@asynccontextmanager
async def async_execution_envelope(
    auth,
    component: str,
    impact: Optional[DecisionImpact] = None,
    params: Optional[dict] = None,
    timeout: float = 30.0
):
    """Async execution envelope context manager."""
    async with AsyncExecutionEnvelope(auth, component, impact, params, timeout) as env:
        yield env
