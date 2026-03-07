"""
Decision Impact Classification

ALL actuator operations MUST be classified by impact level.
HIGH/CRITICAL operations require human approval before execution.

IMPACT LEVELS:
- LOW: Read operations, status checks (auto-approved)
- MEDIUM: Write operations with reversibility (auto-approved with logging)
- HIGH: Delete operations, network requests (REQUIRES APPROVAL)
- CRITICAL: Process spawn/kill, model loading (REQUIRES APPROVAL + AUDIT)
"""

import asyncio
import hashlib
import logging
import threading
import time
from dataclasses import dataclass
from enum import Enum
from typing import Dict, Optional

logger = logging.getLogger("unified_core.decision_classifier")


class DecisionImpact(Enum):
    """Impact levels for actuator operations."""
    LOW = 1       # read_file, list_dir, status checks
    MEDIUM = 2    # write_file (can be reverted from backup)
    HIGH = 3      # delete_file, http_request (irreversible)
    CRITICAL = 4  # process spawn/kill, training (system-level)


# Mapping of actuator operations to impact levels
IMPACT_MAP: Dict[str, DecisionImpact] = {
    # Filesystem operations
    "filesystem.read": DecisionImpact.LOW,
    "filesystem.write": DecisionImpact.MEDIUM,
    "filesystem.delete": DecisionImpact.HIGH,
    "filesystem.mkdir": DecisionImpact.LOW,
    
    # Network operations
    "network.http_request": DecisionImpact.HIGH,
    
    # Process operations
    "process.spawn": DecisionImpact.CRITICAL,
    "process.kill": DecisionImpact.CRITICAL,
}


@dataclass
class ApprovalRequest:
    """Request for human approval of a decision."""
    decision_id: str
    action_type: str
    impact: DecisionImpact
    params: dict
    justification: str
    user_id: str
    timestamp: float
    
    def to_dict(self) -> dict:
        return {
            "decision_id": self.decision_id,
            "action_type": self.action_type,
            "impact": self.impact.name,
            "params": self.params,
            "justification": self.justification,
            "user_id": self.user_id,
            "timestamp": self.timestamp,
        }


class ApprovalQueue:
    """
    Global approval queue for HIGH/CRITICAL decisions.
    
    SECURITY: All HIGH/CRITICAL operations MUST be approved by humans.
    Requests timeout after 5 minutes and are automatically rejected.
    """
    
    _pending: Dict[str, ApprovalRequest] = {}
    _approvals: Dict[str, bool] = {}  # decision_id → approved/rejected
    _lock = threading.Lock()
    
    APPROVAL_TIMEOUT = 300  # 5 minutes
    
    @classmethod
    def request_approval(cls, request: ApprovalRequest, timeout: float = None) -> bool:
        """
        Request human approval. BLOCKS until approved/rejected or timeout.
        
        Args:
            request: The approval request
            timeout: Custom timeout in seconds (default: 300)
            
        Returns:
            True if approved, False if rejected or timeout
        """
        timeout = timeout or cls.APPROVAL_TIMEOUT
        
        with cls._lock:
            cls._pending[request.decision_id] = request
            logger.critical(
                f"🚨 APPROVAL REQUIRED [{request.impact.name}]: "
                f"{request.action_type} - {request.justification}"
            )
            logger.info(f"Decision ID: {request.decision_id}")
            logger.info(f"Parameters: {request.params}")
        
        # Wait for approval (blocking)
        start = time.time()
        while True:
            with cls._lock:
                # Check if decision was processed
                if request.decision_id in cls._approvals:
                    result = cls._approvals[request.decision_id]
                    # Cleanup
                    del cls._approvals[request.decision_id]
                    if request.decision_id in cls._pending:
                        del cls._pending[request.decision_id]
                    
                    status = "APPROVED" if result else "REJECTED"
                    logger.info(f"Decision {request.decision_id} {status}")
                    return result
            
            # Check timeout
            if time.time() - start > timeout:
                with cls._lock:
                    if request.decision_id in cls._pending:
                        del cls._pending[request.decision_id]
                logger.error(
                    f"Approval timeout for {request.decision_id} "
                    f"after {timeout}s - AUTO-REJECTED"
                )
                return False
            
            # Sleep briefly before checking again
            time.sleep(0.5)
    
    @classmethod
    def approve(cls, decision_id: str) -> bool:
        """
        Approve a pending decision (called by human via API).
        
        Returns:
            True if decision was pending, False if not found
        """
        with cls._lock:
            if decision_id in cls._pending:
                cls._approvals[decision_id] = True
                logger.info(f"Decision {decision_id} approved by human")
                return True
            logger.warning(f"Cannot approve {decision_id} - not found in pending")
            return False
    
    @classmethod
    def reject(cls, decision_id: str, reason: str = "") -> bool:
        """
        Reject a pending decision.
        
        Returns:
            True if decision was pending, False if not found
        """
        with cls._lock:
            if decision_id in cls._pending:
                cls._approvals[decision_id] = False
                logger.warning(f"Decision {decision_id} rejected by human: {reason}")
                return True
            logger.warning(f"Cannot reject {decision_id} - not found in pending")
            return False
    
    @classmethod
    def list_pending(cls) -> list:
        """Get list of all pending approval requests."""
        with cls._lock:
            return [req.to_dict() for req in cls._pending.values()]
    
    @classmethod
    def clear_all(cls):
        """Clear all pending requests (for testing/emergency)."""
        with cls._lock:
            cls._pending.clear()
            cls._approvals.clear()
            logger.warning("All pending approvals cleared")


def classify_decision(action_type: str) -> DecisionImpact:
    """
    Classify a decision by its impact level.
    
    Args:
        action_type: Action type in format "actuator.operation"
        
    Returns:
        Impact level for this action type
    """
    return IMPACT_MAP.get(action_type, DecisionImpact.CRITICAL)


def generate_decision_id(action_type: str, params: dict, user_id: str) -> str:
    """Generate unique decision ID from action parameters."""
    content = f"{action_type}:{params}:{user_id}:{time.time()}"
    return hashlib.sha256(content.encode()).hexdigest()[:16]


def requires_approval(impact: DecisionImpact) -> bool:
    """Check if an impact level requires human approval."""
    return impact.value >= DecisionImpact.HIGH.value
