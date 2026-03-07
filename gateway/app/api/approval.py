"""
Human Approval API

FastAPI endpoints for reviewing and approving/rejecting pending decisions.

SECURITY: Only accessible by admin-level users.
"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import List

from unified_core.auth import AuthContext, require_bearer
from unified_core.decision_classifier import ApprovalQueue

router = APIRouter(prefix="/approval", tags=["approval"])


class ApprovalDecision(BaseModel):
    """Request body for approval/rejection."""
    decision_id: str
    reason: str = ""


@router.get("/pending")
async def list_pending_approvals(auth: AuthContext = Depends(require_bearer)) -> List[dict]:
    """
    List all pending approval requests.
    
    SECURITY: Requires admin scope.
    """
    auth.require_scope("admin")
    
    pending = ApprovalQueue.list_pending()
    return pending


@router.post("/approve")
async def approve_decision(
    decision: ApprovalDecision,
    auth: AuthContext = Depends(require_bearer)
) -> dict:
    """
    Approve a pending decision.
    
    SECURITY: Requires admin scope.
    """
    auth.require_scope("admin")
    
    success = ApprovalQueue.approve(decision.decision_id)
    if not success:
        raise HTTPException(status_code=404, detail="Decision not found or already processed")
    
    return {
        "success": True,
        "decision_id": decision.decision_id,
        "approved_by": auth.user_id
    }


@router.post("/reject")
async def reject_decision(
    decision: ApprovalDecision,
    auth: AuthContext = Depends(require_bearer)
) -> dict:
    """
    Reject a pending decision.
    
    SECURITY: Requires admin scope.
    """
    auth.require_scope("admin")
    
    success = ApprovalQueue.reject(decision.decision_id, decision.reason)
    if not success:
        raise HTTPException(status_code=404, detail="Decision not found or already processed")
    
    return {
        "success": True,
        "decision_id": decision.decision_id,
        "rejected_by": auth.user_id,
        "reason": decision.reason
    }


@router.delete("/clear")
async def clear_pending_approvals(auth: AuthContext = Depends(require_bearer)) -> dict:
    """
    Clear all pending approvals (EMERGENCY USE ONLY).
    
    SECURITY: Requires admin scope.
    """
    auth.require_scope("admin")
    
    ApprovalQueue.clear_all()
    
    return {
        "success": True,
        "cleared_by": auth.user_id
    }
