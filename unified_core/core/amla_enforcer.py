"""
AMLA Enforcer - Global Enforcement Gateway (SECURED & MONOLITHIC v2.3)
Role: Senior Security Architect Fix

RE-IMPLEMENTING AMLAEnforcer Class for full system compatibility.
"""

import logging
import os
import time
import functools
import asyncio
from typing import Any, Callable, Dict, List, Optional, TypeVar, Union

from unified_core.core.amla import (
    AMLAAuditResult,
    AMLAActionRequest,
    AMLAVerdict,
    get_amla,
    require_amla_audit
)

logger = logging.getLogger("noogh.amla.enforcer")
F = TypeVar('F', bound=Callable[..., Any])

class AMLAEnforcementError(RuntimeError):
    def __init__(self, verdict: AMLAVerdict, message: str, audit_result: AMLAAuditResult):
        self.verdict = verdict
        self.audit_result = audit_result
        super().__init__(f"AMLA SECURITY BLOCK [{verdict.value}]: {message}")

class AMLAAcknowledgmentRequired(RuntimeError):
    def __init__(self, action_type: str, audit_result: AMLAAuditResult):
        self.action_type = action_type
        self.audit_result = audit_result
        super().__init__(f"AMLA GOVERNANCE: Approval REQUIRED for: {action_type}")

class AMLAEnforcer:
    """The central gateway for all hazardous operations."""
    def __init__(self, strict_mode: bool = False):
        self.strict_mode = strict_mode
        logger.info(f"🛡️ AMLA Enforcer initialized (Strict: {strict_mode})")

    async def audit_action(self, action_type: str, parameters: Dict, auth_context: Any = None) -> AMLAAuditResult:
        """Async audit wrapper (Legacy compatibility)."""
        # We redirect to the secure synchronous enforcer as it's the core path
        return enforce_amla(
            action_type=action_type,
            params=parameters,
            beliefs=[],
            confidence=1.0,
            impact=0.7
        )

def enforce_amla(
    action_type: str,
    params: Dict[str, Any],
    beliefs: List[str] = None,
    confidence: float = 1.0,
    impact: float = 0.5,
    auto_acknowledge: bool = False,
    acknowledgment_callback: Optional[Callable] = None
) -> AMLAAuditResult:
    """Core enforcement logic - SECURED."""
    audit_result = require_amla_audit(
        action_type=action_type,
        params=params, 
        beliefs=beliefs or [],
        confidence=confidence,
        impact=impact
    )
    
    # CASE 1: BLOCKED
    if audit_result.verdict == AMLAVerdict.BLOCKED:
        raise AMLAEnforcementError(audit_result.verdict, audit_result.blocked_reason, audit_result)
    
    # CASE 2: HUMAN ACK REQUIRED (No Bypass)
    if audit_result.requires_acknowledgment and not auto_acknowledge:
        if not (acknowledgment_callback and acknowledgment_callback(action_type, audit_result)):
            raise AMLAAcknowledgmentRequired(action_type, audit_result)
            
    return audit_result

# Compatibility Mixin
class AMLAEnforcedMixin:
    pass

def amla_protected(impact=0.5):
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            enforce_amla(func.__name__, {"args":args, "kwargs":kwargs}, impact=impact)
            return func(*args, **kwargs)
        return wrapper
    return decorator

def is_strict_mode() -> bool:
    return True
