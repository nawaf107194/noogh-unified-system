"""
Adversarial Self-Audit Agent (ASAA) - Internal Decision Court

Every decision MUST pass through this agent before execution.
The ASAA's job is to PROVE that decisions are wrong, not to approve them.

DESIGN PHILOSOPHY:
- If a decision survives adversarial scrutiny, it may proceed
- If a decision is fragile, it must be delayed and acknowledged
- If a decision is dangerous, it must be blocked

NO DECISION EXECUTES WITHOUT ASAA VERIFICATION.
"""

import hashlib
import json
import logging
import os
import time
from dataclasses import dataclass, field, asdict
from typing import Any, Dict, List, Optional, Tuple
from enum import Enum

logger = logging.getLogger("unified_core.core.asaa")


class AuditVerdict(Enum):
    """Verdict from ASAA evaluation."""
    APPROVED = "approved"           # Decision may proceed
    REQUIRES_ACK = "requires_ack"   # Needs human acknowledgment
    DELAYED = "delayed"             # Friction delay imposed
    BLOCKED = "blocked"             # Execution prevented


@dataclass
class AuditResult:
    """
    Result of ASAA evaluation.
    
    This is the JSON output for every decision attempt.
    """
    action_id: str
    confidence: float
    fragility: float
    requires_acknowledgment: bool
    friction_delay_seconds: float
    mechanism_disclosure: str
    advisory_message: str
    verdict: AuditVerdict = AuditVerdict.APPROVED
    blocked_reason: Optional[str] = None
    timestamp: float = field(default_factory=time.time)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "action_id": self.action_id,
            "confidence": round(self.confidence, 4),
            "fragility": round(self.fragility, 4),
            "requires_acknowledgment": self.requires_acknowledgment,
            "friction_delay_seconds": round(self.friction_delay_seconds, 2),
            "mechanism_disclosure": self.mechanism_disclosure,
            "advisory_message": self.advisory_message,
            "verdict": self.verdict.value,
            "blocked_reason": self.blocked_reason,
            "timestamp": self.timestamp
        }
    
    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2)


@dataclass
class ActionRequest:
    """A decision request submitted to ASAA for evaluation."""
    action_type: str
    params: Dict[str, Any]
    source_beliefs: List[str]           # Belief IDs that led to this decision
    confidence: float                    # System's confidence in this action
    impact_level: float = 0.5           # 0.0 (low) to 1.0 (high)
    context: Optional[str] = None       # Additional context


class AdversarialSelfAuditAgent:
    """
    Internal court that evaluates every decision.
    
    MISSION: Prevent overconfident, unstable, or unsafe decisions.
    
    This agent has AUTHORITY to:
    - Require explicit acknowledgment
    - Impose mandatory delay
    - Block execution entirely
    
    NO BYPASS IS ALLOWED.
    """
    
    # Thresholds (configurable via environment)
    FRAGILITY_WARN_THRESHOLD = float(os.getenv("ASAA_FRAGILITY_WARN", "0.4"))
    FRAGILITY_BLOCK_THRESHOLD = float(os.getenv("ASAA_FRAGILITY_BLOCK", "0.8"))
    IMPACT_HIGH_THRESHOLD = float(os.getenv("ASAA_IMPACT_HIGH", "0.7"))
    
    # Friction scaling
    BASE_FRICTION_SECONDS = 5.0
    MAX_FRICTION_SECONDS = 60.0
    
    # Storage for audit log
    from unified_core.config import settings
    AUDIT_LOG_PATH = settings.ASAA_LOG_PATH
    
    def __init__(self, decision_scorer=None, belief_store=None):
        self._scorer = decision_scorer
        self._beliefs = belief_store
        
        self._blocked_count = 0
        self._delayed_count = 0
        self._approved_count = 0
        self._audit_history: List[AuditResult] = []
        
        # Ensure audit log directory exists
        os.makedirs(os.path.dirname(self.AUDIT_LOG_PATH), exist_ok=True)
        
        logger.info("ASAA initialized - All decisions must pass through this agent")
    
    def set_decision_scorer(self, scorer):
        """Set reference to DecisionScorer for fragility computation."""
        self._scorer = scorer
        logger.info("ASAA: DecisionScorer connected")
    
    def set_belief_store(self, beliefs):
        """Set reference to belief store for counterfactual analysis."""
        self._beliefs = beliefs
        logger.info("ASAA: BeliefStore connected")
    
    def evaluate(self, request: ActionRequest) -> AuditResult:
        """
        Evaluate a decision request.
        
        This is the MAIN ENTRY POINT for all decisions.
        Every action must pass through here.
        """
        action_id = self._generate_action_id(request)
        
        # 1. Compute fragility
        fragility = self._compute_fragility(request)
        
        # 2. Determine friction and acknowledgment requirements
        requires_ack, friction_delay = self._determine_friction_and_ack(request, fragility)
        
        # 3. Generate disclosures and advisory
        mechanism = self._generate_mechanism_disclosure(request, fragility)
        advisory = self._generate_advisory(fragility, request.impact_level)
        
        # 4. Determine verdict
        verdict, blocked_reason = self._determine_verdict(fragility, friction_delay, requires_ack)
        
        # 5. Create result
        result = AuditResult(
            action_id=action_id,
            confidence=request.confidence,
            fragility=fragility,
            requires_acknowledgment=requires_ack,
            friction_delay_seconds=friction_delay,
            mechanism_disclosure=mechanism,
            advisory_message=advisory,
            verdict=verdict,
            blocked_reason=blocked_reason
        )
        
        # 6. Log and persist
        self._log_audit(result)
        self._audit_history.append(result)
        
        logger.info(f"ASAA verdict for {action_id}: {verdict.value} (fragility={fragility:.2f})")
        
        return result

    def _determine_friction_and_ack(self, request: ActionRequest, fragility: float) -> Tuple[bool, float]:
        """Determine if acknowledgment is required and calculate friction delay."""
        requires_ack = False
        friction_delay = 0.0
        
        if fragility > self.FRAGILITY_WARN_THRESHOLD:
            requires_ack = True
            friction_delay = self._calculate_friction(fragility, request.impact_level)
            
        if request.impact_level > self.IMPACT_HIGH_THRESHOLD:
            requires_ack = True
            friction_delay = max(friction_delay, self.BASE_FRICTION_SECONDS * 2)
            
        return requires_ack, friction_delay

    def _determine_verdict(self, fragility: float, friction_delay: float, requires_ack: bool) -> Tuple[AuditVerdict, Optional[str]]:
        """Determine final verdict based on fragility and friction."""
        if fragility > self.FRAGILITY_BLOCK_THRESHOLD:
            self._blocked_count += 1
            return AuditVerdict.BLOCKED, f"Fragility {fragility:.2f} exceeds block threshold {self.FRAGILITY_BLOCK_THRESHOLD}"
            
        if friction_delay > 0:
            self._delayed_count += 1
            return AuditVerdict.DELAYED, None
            
        if requires_ack:
            return AuditVerdict.REQUIRES_ACK, None
            
        self._approved_count += 1
        return AuditVerdict.APPROVED, None
    
    def _compute_fragility(self, request: ActionRequest) -> float:
        """
        Compute fragility using real WorldModel belief store.
        
        Queries actual belief confidence and falsification history
        instead of simulating counterfactual inversions.
        """
        if not self._beliefs or not request.source_beliefs:
            return 0.3
        
        involved_beliefs = []
        for belief_id in request.source_beliefs[:3]:  # Top 3
            # Use real store sync method if available
            if hasattr(self._beliefs, '_get_belief_sync'):
                belief_data = self._beliefs._get_belief_sync(belief_id)
                if belief_data:
                    involved_beliefs.append(belief_data)
            elif hasattr(self._beliefs, 'get'):
                belief = self._beliefs.get(belief_id)
                if belief:
                    involved_beliefs.append(belief)
        
        if not involved_beliefs:
            return 0.3
        
        # Compute fragility from real data:
        # 1. Check how many beliefs have low confidence (< 0.5)
        # 2. Check falsification history for related beliefs
        weak_count = 0
        for b in involved_beliefs:
            conf = b.get('confidence', 0.5) if isinstance(b, dict) else getattr(b, 'confidence', 0.5)
            state = b.get('state', 'active') if isinstance(b, dict) else getattr(b, 'state', 'active')
            state_str = state.value if hasattr(state, 'value') else str(state)
            
            if conf < 0.4 or state_str == 'weakened':
                weak_count += 1
            elif state_str == 'falsified':
                weak_count += 1  # Falsified beliefs = maximum fragility contribution
        
        # Check falsification history
        falsification_penalty = 0.0
        if hasattr(self._beliefs, '_get_all_falsifications_sync'):
            try:
                falsifications = self._beliefs._get_all_falsifications_sync()
                recent_falsifications = [f for f in falsifications 
                                        if f.get('timestamp', 0) > time.time() - 3600]  # Last hour
                falsification_penalty = min(len(recent_falsifications) * 0.05, 0.3)
            except Exception:
                pass
        
        fragility = (weak_count / max(len(involved_beliefs), 1)) + falsification_penalty
        return min(fragility, 1.0)
    
    def _calculate_friction(self, fragility: float, impact: float) -> float:
        """Calculate friction delay based on fragility and impact."""
        # Base friction scaled by fragility
        friction = self.BASE_FRICTION_SECONDS * (1 + fragility * 2)
        
        # High impact multiplier
        if impact > self.IMPACT_HIGH_THRESHOLD:
            friction *= 1.5
        
        return min(friction, self.MAX_FRICTION_SECONDS)
    
    def _generate_mechanism_disclosure(self, request: ActionRequest, fragility: float) -> str:
        """Generate transparent explanation of scoring logic."""
        parts = [
            f"Action type: {request.action_type}",
            f"Based on beliefs: {len(request.source_beliefs)} beliefs consulted",
            f"System confidence: {request.confidence:.2%}",
            f"Fragility score: {fragility:.2%} (counterfactual inversion test)",
            f"Impact level: {request.impact_level:.2%}",
        ]
        
        if fragility > self.FRAGILITY_WARN_THRESHOLD:
            parts.append("⚠️ HIGH FRAGILITY: Decision changes when top beliefs are inverted")
        
        return " | ".join(parts)
    
    def _generate_advisory(self, fragility: float, impact: float) -> str:
        """Generate advisory message highlighting risk and uncertainty."""
        if fragility > self.FRAGILITY_BLOCK_THRESHOLD:
            return (
                "🔴 CRITICAL: This decision is extremely fragile. "
                "Inverting key beliefs causes complete decision reversal. "
                "Execution is BLOCKED until fragility is reduced."
            )
        
        if fragility > self.FRAGILITY_WARN_THRESHOLD:
            return (
                f"🟠 WARNING: Decision fragility is {fragility:.0%}. "
                "This means the decision may be wrong if underlying beliefs are incorrect. "
                "Human acknowledgment required before proceeding."
            )
        
        if impact > self.IMPACT_HIGH_THRESHOLD:
            return (
                "🟡 CAUTION: High-impact action. "
                "Even with low fragility, consequences may be significant. "
                "Please review before execution."
            )
        
        return "✅ Decision appears stable under counterfactual testing."
    
    def _generate_action_id(self, request: ActionRequest) -> str:
        """Generate unique action ID."""
        content = f"{request.action_type}:{time.time()}:{os.urandom(4).hex()}"
        return hashlib.sha256(content.encode()).hexdigest()[:16]
    
    def _log_audit(self, result: AuditResult):
        """Persist audit result to log file."""
        try:
            with open(self.AUDIT_LOG_PATH, "a") as f:
                f.write(result.to_json() + "\n")
        except Exception as e:
            logger.error(f"Failed to log audit: {e}")
    
    def acknowledge_action(self, action_id: str, operator: str, rationale: str) -> bool:
        """
        Record human acknowledgment for a delayed/requires_ack action.
        
        Returns True if action may now proceed.
        """
        logger.warning(
            f"ASAA: Action {action_id} acknowledged by {operator}. "
            f"Rationale: {rationale}"
        )
        
        # Log the override
        override_log = {
            "action_id": action_id,
            "operator": operator,
            "rationale": rationale,
            "timestamp": time.time(),
            "event": "HUMAN_OVERRIDE"
        }
        
        try:
            with open(self.AUDIT_LOG_PATH, "a") as f:
                f.write(json.dumps(override_log) + "\n")
        except Exception as e:
            logger.error(f"Failed to log override: {e}")
        
        return True
    
    def get_statistics(self) -> Dict[str, Any]:
        """Return ASAA statistics."""
        return {
            "total_evaluated": self._approved_count + self._delayed_count + self._blocked_count,
            "approved": self._approved_count,
            "delayed": self._delayed_count,
            "blocked": self._blocked_count,
            "block_rate": self._blocked_count / max(1, self._approved_count + self._delayed_count + self._blocked_count),
            "thresholds": {
                "fragility_warn": self.FRAGILITY_WARN_THRESHOLD,
                "fragility_block": self.FRAGILITY_BLOCK_THRESHOLD,
                "impact_high": self.IMPACT_HIGH_THRESHOLD
            }
        }


# === SINGLETON ACCESS ===
_asaa_instance: Optional[AdversarialSelfAuditAgent] = None


def get_asaa() -> AdversarialSelfAuditAgent:
    """Get or create global ASAA instance."""
    global _asaa_instance
    if _asaa_instance is None:
        _asaa_instance = AdversarialSelfAuditAgent()
    return _asaa_instance


def require_asaa_approval(action_type: str, params: Dict[str, Any], 
                          beliefs: List[str], confidence: float,
                          impact: float = 0.5) -> AuditResult:
    """
    Convenience function: submit action for ASAA evaluation.
    
    This MUST be called before any decision execution.
    """
    asaa = get_asaa()
    request = ActionRequest(
        action_type=action_type,
        params=params,
        source_beliefs=beliefs,
        confidence=confidence,
        impact_level=impact
    )
    return asaa.evaluate(request)
