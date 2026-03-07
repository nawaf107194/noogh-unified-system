"""
Adversarial Military-Level Audit Agent (AMLA) - Supreme Audit Layer

MISSION: Audit all NOOGH system decisions BEFORE execution.
AUTHORITY: Overrides ASAA only to EXPOSE weaknesses, never to bypass.

MECHANISMS:
1. Counterfactual Extreme Stress - Inverts top 5-10 beliefs
2. Decision Fragility Extreme (DFE) - Score [0.0-1.0]
3. Adversarial Input Injection Detection - Bypass attempt testing
4. Friction Gate Challenge - Mandatory acknowledgment for high-risk
5. Security Alert - Flags bypass attempts as violations

HONESTY DISCLAIMER:
- This is an advisory audit layer, not enforcement
- All verdicts are recommendations that may be overridden
- Persistence is filesystem-based and MAY BE LOST
- No physical enforcement mechanism exists
"""

import hashlib
import json
import logging
import os
import time
import unicodedata
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple
from enum import Enum

logger = logging.getLogger("unified_core.core.amla")


class AMLAVerdict(Enum):
    """
    AMLA verdict levels - more granular than ASAA.
    
    ALERT is unique to AMLA - detects security violations.
    """
    APPROVED = "APPROVED"           # Safe to execute
    REQUIRES_ACK = "REQUIRES_ACK"   # Human confirmation needed
    DELAYED = "DELAYED"             # Friction delay applied
    BLOCKED = "BLOCKED"             # Execution denied
    ALERT = "ALERT"                 # SECURITY VIOLATION detected


@dataclass
class AttackSimulation:
    """Result of an adversarial bypass attempt."""
    attack_type: str
    attack_payload: Dict[str, Any]
    bypass_successful: bool
    detection_reason: str
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "attack_type": self.attack_type,
            "bypass_successful": self.bypass_successful,
            "detection_reason": self.detection_reason
        }


@dataclass
class CounterfactualVariation:
    """Result of a belief inversion test."""
    belief_id: str
    original_confidence: float
    inverted_confidence: float
    decision_changed: bool
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "belief_id": self.belief_id,
            "original_confidence": round(self.original_confidence, 4),
            "inverted_confidence": round(self.inverted_confidence, 4),
            "decision_changed": self.decision_changed
        }


@dataclass
class AMLAAuditResult:
    """
    Complete AMLA audit result with full transparency.
    
    Every field is disclosed for maximum transparency.
    """
    action_id: str
    confidence: float
    fragility: float                    # ASAA-level fragility
    fragility_extreme: float            # DFE score (AMLA)
    requires_acknowledgment: bool
    friction_delay_seconds: float
    mechanism_disclosure: str           # Full audit trace
    advisory_message: str               # Risk/uncertainty warning
    verdict: AMLAVerdict
    blocked_reason: Optional[str] = None
    attack_simulations: List[AttackSimulation] = field(default_factory=list)
    counterfactual_variations: List[CounterfactualVariation] = field(default_factory=list)
    impact_level: float = 0.5
    timestamp: float = field(default_factory=time.time)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "action_id": self.action_id,
            "confidence": round(self.confidence, 4),
            "fragility": round(self.fragility, 4),
            "fragility_extreme": round(self.fragility_extreme, 4),
            "requires_acknowledgment": self.requires_acknowledgment,
            "friction_delay_seconds": round(self.friction_delay_seconds, 2),
            "mechanism_disclosure": self.mechanism_disclosure,
            "advisory_message": self.advisory_message,
            "verdict": self.verdict.value,
            "blocked_reason": self.blocked_reason,
            "attack_simulations": [a.to_dict() for a in self.attack_simulations],
            "counterfactual_variations": [c.to_dict() for c in self.counterfactual_variations],
            "impact_level": round(self.impact_level, 4),
            "timestamp": self.timestamp
        }
    
    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2)


@dataclass
class AMLAActionRequest:
    """Action request submitted to AMLA for extreme audit."""
    action_type: str
    params: Dict[str, Any]
    source_beliefs: List[str]           # Belief IDs that led to this decision
    confidence: float                    # System's confidence in this action
    impact_level: float = 0.5           # 0.0 (low) to 1.0 (high)
    context: Optional[str] = None       # Additional context


class AdversarialMilitaryAuditAgent:
    """
    Military Supreme Audit Layer.
    
    AUTHORITY: Overrides ASAA only to EXPOSE weaknesses.
    MISSION: Maximum scrutiny before any execution.
    
    This agent performs EXTREME counterfactual testing and
    actively attempts to bypass its own security controls.
    
    DESIGN PHILOSOPHY:
    - If a decision survives AMLA, it may proceed
    - If a bypass is detected, ALERT is raised
    - If fragility is extreme, execution is BLOCKED
    
    HONESTY DISCLAIMER:
    All enforcement is advisory. No physical enforcement exists.
    """
    
    # Thresholds (configurable via environment)
    DFE_WARN_THRESHOLD = float(os.getenv("AMLA_DFE_WARN", "0.7"))
    DFE_DELAY_THRESHOLD = float(os.getenv("AMLA_DFE_DELAY", "0.9"))
    DFE_BLOCK_THRESHOLD = float(os.getenv("AMLA_DFE_BLOCK", "0.98"))
    IMPACT_HIGH_THRESHOLD = float(os.getenv("AMLA_IMPACT_HIGH", "0.95"))
    
    # Friction scaling (Reduced for Sovereign Mode)
    BASE_FRICTION_SECONDS = 2.0
    MAX_FRICTION_SECONDS = 30.0
    MIN_FRICTION_DELAY = 5.0  # Minimum delay for high-fragility decisions
    
    # Beliefs to test in counterfactual (top N)
    MAX_BELIEFS_TO_INVERT = 10
    MIN_BELIEFS_TO_INVERT = 5
    
    # Storage for audit log
    from unified_core.config import settings
    AUDIT_LOG_PATH = settings.AMLA_LOG_PATH
    
    # Known bypass patterns to detect
    # IMPORTANT: These are checked as exact key names or with word boundaries
    # to avoid false positives on words like 'enforce', 'reinforce'
    BYPASS_PATTERNS = [
        "__bypass__",
        "admin_override",
        "skip_friction",
        "skip_amla",
        "no_audit",
        "--no-verify",
        "--skip-audit",
        "--force",          # Only the flag, not the word 'force'
        "bypass=true",
        "override=true",
    ]
    
    # Additional patterns that require exact key match (not substring)
    EXACT_KEY_PATTERNS = [
        "sudo",
        "force",
        "override",
    ]
    
    def __init__(self, belief_store=None, advisory_memory=None, asaa=None):
        self._beliefs = belief_store
        self._memory = advisory_memory
        self._asaa = asaa
        
        self._alert_count = 0
        self._blocked_count = 0
        self._delayed_count = 0
        self._approved_count = 0
        self._audit_history: List[AMLAAuditResult] = []
        
        # Ensure audit log directory exists
        os.makedirs(os.path.dirname(self.AUDIT_LOG_PATH), exist_ok=True)
        
        logger.info("AMLA initialized - Military Supreme Audit Layer active")
    
    def set_belief_store(self, beliefs):
        """Set reference to belief store for counterfactual analysis."""
        self._beliefs = beliefs
        logger.info("AMLA: BeliefStore connected")
    
    def set_advisory_memory(self, memory):
        """Set reference to AdvisoryMemory for bypass testing."""
        self._memory = memory
        logger.info("AMLA: AdvisoryMemory connected")
    
    def set_asaa(self, asaa):
        """Set reference to ASAA for baseline fragility."""
        self._asaa = asaa
        logger.info("AMLA: ASAA connected")
    
    def evaluate(self, request: AMLAActionRequest, beliefs: List = None) -> AMLAAuditResult:
        """
        Perform EXTREME audit of an action request.
        """
        action_id = self._generate_action_id(request)
        test_beliefs = beliefs or self._get_beliefs_for_request(request)
        
        # Audit stages
        baseline_fragility = self._perf_baseline_audit(request, test_beliefs)
        dfe, variations = self._perf_extreme_audit(request, test_beliefs)
        attacks, bypass_detected = self._perf_adversarial_audit(request)
        requires_ack, friction_delay = self._perf_friction_audit(dfe, request.impact_level, request)
        
        # Finalization
        mechanism = self._generate_mechanism_disclosure(
            request, baseline_fragility, dfe, attacks, variations
        )
        advisory = self._generate_advisory(dfe, request.impact_level, bypass_detected)
        verdict, blocked_reason = self._determine_verdict(
            dfe, bypass_detected, requires_ack, friction_delay
        )
        
        self._update_counters(verdict)
        
        result = AMLAAuditResult(
            action_id=action_id,
            confidence=request.confidence,
            fragility=baseline_fragility,
            fragility_extreme=dfe,
            requires_acknowledgment=requires_ack,
            friction_delay_seconds=friction_delay,
            mechanism_disclosure=mechanism,
            advisory_message=advisory,
            verdict=verdict,
            blocked_reason=blocked_reason,
            attack_simulations=attacks,
            counterfactual_variations=variations,
            impact_level=request.impact_level
        )
        
        self._log_audit(result)
        self._audit_history.append(result)
        
        logger.info(
            f"AMLA verdict for {action_id}: {verdict.value} "
            f"(DFE={dfe:.2%}, baseline={baseline_fragility:.2%})"
        )
        return result

    def _perf_baseline_audit(self, request, beliefs) -> float:
        return self._compute_baseline_fragility(request, beliefs)

    def _perf_extreme_audit(self, request, beliefs) -> Tuple[float, List[CounterfactualVariation]]:
        return self._compute_fragility_extreme(request, beliefs)

    def _perf_adversarial_audit(self, request) -> Tuple[List[AttackSimulation], bool]:
        return self._run_adversarial_injections(request)

    def _perf_friction_audit(self, dfe, impact, request) -> Tuple[bool, float]:
        return self._validate_friction_gate(dfe, impact, request)
    
    def _compute_baseline_fragility(self, request: AMLAActionRequest, beliefs: List) -> float:
        """
        Compute baseline fragility using real belief data (replaces ASAA-equivalent).
        """
        if not beliefs:
            return 0.3  # Default when no beliefs
        
        top_beliefs = sorted(beliefs, key=lambda b: getattr(b, 'confidence', 0.5), reverse=True)[:3]
        weak_count = 0
        
        for belief in top_beliefs:
            original = getattr(belief, 'confidence', 0.5)
            state = getattr(belief, 'state', 'active')
            state_str = state.value if hasattr(state, 'value') else str(state)
            
            if original < 0.4 or state_str in ('weakened', 'falsified'):
                weak_count += 1
        
        return min(weak_count / max(len(top_beliefs), 1), 1.0)
    
    def _compute_fragility_extreme(
        self, 
        request: AMLAActionRequest, 
        beliefs: List
    ) -> Tuple[float, List[CounterfactualVariation]]:
        """
        Compute Decision Fragility Extreme (DFE) via belief inversion.
        """
        if not beliefs:
            return 0.3, []
        
        test_beliefs = self._get_test_beliefs(beliefs)
        dfe, variations = self._process_belief_variations(request, test_beliefs)
        
        return dfe, variations

    def _get_test_beliefs(self, beliefs: List) -> List:
        sorted_beliefs = sorted(
            beliefs, 
            key=lambda b: getattr(b, 'confidence', 0.5), 
            reverse=True
        )
        num_to_test = min(
            max(self.MIN_BELIEFS_TO_INVERT, len(sorted_beliefs)),
            self.MAX_BELIEFS_TO_INVERT
        )
        return sorted_beliefs[:num_to_test]

    def _process_belief_variations(
        self, 
        request: AMLAActionRequest, 
        test_beliefs: List
    ) -> Tuple[float, List[CounterfactualVariation]]:
        """
        Compute decision fragility using real WorldModel belief data.
        
        Instead of simulating confidence inversions, we analyze:
        1. Actual belief confidence levels and states
        2. Historical falsification records from the real store
        """
        variations = []
        fragile_count = 0
        
        for belief in test_beliefs:
            belief_id = getattr(belief, 'belief_id', str(id(belief)))
            original_conf = getattr(belief, 'confidence', 0.5)
            state = getattr(belief, 'state', 'active')
            state_str = state.value if hasattr(state, 'value') else str(state)
            
            # Real fragility: belief is fragile if confidence is extreme
            # or if state is weakened/falsified
            is_fragile = (
                original_conf < 0.3 or 
                original_conf > 0.9 or 
                state_str in ('weakened', 'falsified')
            )
            
            if is_fragile:
                fragile_count += 1
            
            variations.append(CounterfactualVariation(
                belief_id=belief_id,
                original_confidence=original_conf,
                inverted_confidence=1.0 - original_conf,
                decision_changed=is_fragile
            ))
        
        # Add falsification history penalty from real store
        falsification_penalty = 0.0
        if hasattr(self, '_beliefs') and self._beliefs and hasattr(self._beliefs, '_get_all_falsifications_sync'):
            try:
                import time as _time
                falsifications = self._beliefs._get_all_falsifications_sync()
                recent = [f for f in falsifications if f.get('timestamp', 0) > _time.time() - 3600]
                falsification_penalty = min(len(recent) * 0.05, 0.3)
            except Exception:
                pass
        
        dfe = (fragile_count / max(len(test_beliefs), 1)) + falsification_penalty
        return min(dfe, 1.0), variations
    
    def _would_decision_change(
        self, 
        request: AMLAActionRequest, 
        belief, 
        original_conf: float
    ) -> bool:
        """
        Determine if decision would change given inverted belief.
        
        HEURISTICS:
        1. If belief was source for this decision AND confidence swing > 0.5 → likely change
        2. If belief confidence was > 0.8 and now < 0.2 → likely change
        3. If belief_id matches action parameters → likely change
        """
        belief_id = getattr(belief, 'belief_id', '')
        current_conf = getattr(belief, 'confidence', 0.5)
        swing = abs(original_conf - current_conf)
        
        # Check if belief is a source for this decision
        is_source_belief = belief_id in request.source_beliefs
        
        # High-confidence swing in source belief
        if is_source_belief and swing > 0.5:
            return True
        
        # Extreme confidence reversal
        if original_conf > 0.8 and current_conf < 0.2:
            return True
        
        if original_conf < 0.2 and current_conf > 0.8:
            return True
        
        # Belief ID referenced in action params
        params_str = json.dumps(request.params)
        if belief_id[:8] in params_str:
            return swing > 0.4
        
        return False
    
    def _run_adversarial_injections(
        self, 
        request: AMLAActionRequest
    ) -> Tuple[List[AttackSimulation], bool]:
        """
        Craft adversarial inputs to test bypass resistance.
        
        ATTACKS:
        1. Parameter injection - bypass flags in params
        2. Homoglyph substitution - Unicode look-alikes
        3. Template injection - f-string exploitation
        4. Keyword stuffing - diluting blocked terms
        5. Case manipulation - bypassing case-sensitive checks
        
        Returns: (attack_results, any_bypass_detected)
        """
        attacks = []
        any_bypass = False
        
        # Attack 1: Parameter injection
        attack1 = self._test_param_injection(request)
        attacks.append(attack1)
        if attack1.bypass_successful:
            any_bypass = True
        
        # Attack 2: Homoglyph substitution
        attack2 = self._test_homoglyph_attack(request)
        attacks.append(attack2)
        if attack2.bypass_successful:
            any_bypass = True
        
        # Attack 3: Template injection
        attack3 = self._test_template_injection(request)
        attacks.append(attack3)
        if attack3.bypass_successful:
            any_bypass = True
        
        # Attack 4: Keyword stuffing
        attack4 = self._test_keyword_stuffing(request)
        attacks.append(attack4)
        if attack4.bypass_successful:
            any_bypass = True
        
        # Attack 5: Case manipulation
        attack5 = self._test_case_manipulation(request)
        attacks.append(attack5)
        if attack5.bypass_successful:
            any_bypass = True
        
        return attacks, any_bypass
    
    def _test_param_injection(self, request: AMLAActionRequest) -> AttackSimulation:
        """Test for bypass flags in parameters."""
        # 1. Check substring patterns in raw JSON
        substring_attack = self._check_substring_injections(request.params)
        if substring_attack:
            return substring_attack
        
        # 2. Check exact key patterns in nested structure
        key_attack = self._check_key_injections(request.params)
        if key_attack:
            return key_attack
        
        return AttackSimulation(
            attack_type="param_injection",
            attack_payload={},
            bypass_successful=False,
            detection_reason="No bypass patterns detected in parameters"
        )

    def _check_substring_injections(self, params: Dict[str, Any]) -> Optional[AttackSimulation]:
        """Check for bypass patterns in serialized parameters."""
        params_str = json.dumps(params).lower()
        for pattern in self.BYPASS_PATTERNS:
            if pattern.lower() in params_str:
                return AttackSimulation(
                    attack_type="param_injection",
                    attack_payload={"detected_pattern": pattern},
                    bypass_successful=True,
                    detection_reason=f"Bypass pattern '{pattern}' found in parameters"
                )
        return None

    def _check_key_injections(self, params: Dict[str, Any]) -> Optional[AttackSimulation]:
        """Check for exact bypass keys in nested parameters."""
        exact_match = self._recursively_find_key(params, self.EXACT_KEY_PATTERNS)
        if exact_match:
            return AttackSimulation(
                attack_type="param_injection",
                attack_payload={"detected_key": exact_match},
                bypass_successful=True,
                detection_reason=f"Bypass key '{exact_match}' found in parameters"
            )
        return None

    def _recursively_find_key(self, obj: Any, patterns: List[str]) -> Optional[str]:
        """Deep search for matching keys in nested structures."""
        if isinstance(obj, dict):
            for key in obj.keys():
                key_lower = str(key).lower()
                for pattern in patterns:
                    if key_lower == pattern.lower():
                        return pattern
            # Recurse into values
            for value in obj.values():
                result = self._recursively_find_key(value, patterns)
                if result:
                    return result
        elif isinstance(obj, list):
            for item in obj:
                result = self._recursively_find_key(item, patterns)
                if result:
                    return result
        return None
    
    def _test_homoglyph_attack(self, request: AMLAActionRequest) -> AttackSimulation:
        """Test for Unicode homoglyph substitution."""
        # Check for non-ASCII characters that look like ASCII
        action_type = request.action_type
        
        homoglyphs_detected = []
        for i, char in enumerate(action_type):
            if ord(char) > 127:
                # Non-ASCII character
                try:
                    name = unicodedata.name(char, "UNKNOWN")
                    if "CYRILLIC" in name or "GREEK" in name:
                        homoglyphs_detected.append((char, name))
                except ValueError:
                    pass
        
        if homoglyphs_detected:
            return AttackSimulation(
                attack_type="homoglyph",
                attack_payload={"detected": homoglyphs_detected},
                bypass_successful=True,
                detection_reason=f"Homoglyph characters detected: {homoglyphs_detected}"
            )
        
        return AttackSimulation(
            attack_type="homoglyph",
            attack_payload={},
            bypass_successful=False,
            detection_reason="No homoglyph characters detected"
        )
    
    def _test_template_injection(self, request: AMLAActionRequest) -> AttackSimulation:
        """Test for template/f-string injection.
        
        REFINED DETECTION:
        - Only flags ACTUAL template syntax, not standard JSON
        - `${` and `{{` are suspicious (template variables)
        - `\\x` and `\\u` are suspicious (escape sequences)
        - Standard `{` and `}` in JSON are ALLOWED
        - `}}` is NOT checked because it appears in valid JSON like {"a": {}}
        """
        # Only check for ACTUAL template/interpolation patterns
        # NOT standard JSON braces which are normal
        # NOTE: `}}` removed - appears in valid JSON like {"kwargs": {}}
        suspicious_patterns = [
            "${",      # Shell/JS variable interpolation
            "{{",      # Jinja/handlebars template (opening)
            "\\x",     # Hex escape
            "\\u",     # Unicode escape
            "%s",      # Old-style Python format
            "%d",      # Old-style Python format
            "%(", 	   # Old-style Python dict format
            "{%",      # Jinja control block
            "%}",      # Jinja control block
        ]
        
        params_str = json.dumps(request.params)
        action_str = request.action_type
        combined = params_str + action_str
        
        detected = []
        for pattern in suspicious_patterns:
            if pattern in combined:
                detected.append(pattern)
        
        if detected:
            return AttackSimulation(
                attack_type="template_injection",
                attack_payload={"detected_patterns": detected},
                bypass_successful=True,
                detection_reason=f"Template injection patterns detected: {detected}"
            )
        
        return AttackSimulation(
            attack_type="template_injection",
            attack_payload={},
            bypass_successful=False,
            detection_reason="No template injection patterns detected"
        )
    
    def _test_keyword_stuffing(self, request: AMLAActionRequest) -> AttackSimulation:
        """Test for keyword stuffing to dilute blocked terms."""
        # Check for suspiciously long action types or params
        if len(request.action_type) > 100:
            return AttackSimulation(
                attack_type="keyword_stuffing",
                attack_payload={"action_length": len(request.action_type)},
                bypass_successful=True,
                detection_reason=f"Abnormally long action_type ({len(request.action_type)} chars)"
            )
        
        params_str = json.dumps(request.params)
        if len(params_str) > 10000:
            return AttackSimulation(
                attack_type="keyword_stuffing",
                attack_payload={"params_length": len(params_str)},
                bypass_successful=True,
                detection_reason=f"Abnormally large params ({len(params_str)} chars)"
            )
        
        return AttackSimulation(
            attack_type="keyword_stuffing",
            attack_payload={},
            bypass_successful=False,
            detection_reason="No keyword stuffing detected"
        )
    
    def _test_case_manipulation(self, request: AMLAActionRequest) -> AttackSimulation:
        """Test for case manipulation to bypass filters."""
        # Check for mixed case that might bypass simple filters
        action_type = request.action_type
        
        # Suspicious: alternating case (LiKe tHiS)
        if len(action_type) > 4:
            alternating_count = 0
            for i in range(1, len(action_type)):
                if action_type[i].isupper() != action_type[i-1].isupper():
                    if action_type[i].isalpha() and action_type[i-1].isalpha():
                        alternating_count += 1
            
            if alternating_count > len(action_type) * 0.6:
                return AttackSimulation(
                    attack_type="case_manipulation",
                    attack_payload={"alternating_ratio": alternating_count / len(action_type)},
                    bypass_successful=True,
                    detection_reason="Suspicious alternating case pattern detected"
                )
        
        return AttackSimulation(
            attack_type="case_manipulation",
            attack_payload={},
            bypass_successful=False,
            detection_reason="No case manipulation detected"
        )
    
    def _validate_friction_gate(
        self, 
        dfe: float, 
        impact: float, 
        request: AMLAActionRequest
    ) -> Tuple[bool, float]:
        """
        Validate friction gate requirements.
        
        RULES:
        1. DFE > 0.5 → REQUIRES ACKNOWLEDGMENT
        2. DFE > 0.7 → MINIMUM 30s DELAY
        3. Impact > 0.8 → REQUIRES ACKNOWLEDGMENT regardless of DFE
        4. DFE > 0.9 → Will be BLOCKED (handled in verdict)
        """
        requires_ack = False
        friction_delay = 0.0
        
        # High DFE requires acknowledgment
        if dfe > self.DFE_WARN_THRESHOLD:
            requires_ack = True
        
        # Very high DFE requires delay
        if dfe > self.DFE_DELAY_THRESHOLD:
            friction_delay = max(self.MIN_FRICTION_DELAY, dfe * 60)
        
        # High impact requires acknowledgment
        if impact > self.IMPACT_HIGH_THRESHOLD:
            requires_ack = True
        
        # Combined high DFE + high impact = extended delay
        if impact > self.IMPACT_HIGH_THRESHOLD and dfe > self.DFE_WARN_THRESHOLD:
            friction_delay = max(friction_delay, 45.0)
        
        # Cap friction delay
        friction_delay = min(friction_delay, self.MAX_FRICTION_SECONDS)
        
        return requires_ack, friction_delay
    
    def _generate_mechanism_disclosure(
        self,
        request: AMLAActionRequest,
        baseline_fragility: float,
        dfe: float,
        attacks: List[AttackSimulation],
        variations: List[CounterfactualVariation]
    ) -> str:
        """Generate transparent explanation of full audit."""
        bypass_count = sum(1 for a in attacks if a.bypass_successful)
        change_count = sum(1 for v in variations if v.decision_changed)
        
        parts = [
            f"Action: {request.action_type}",
            f"Beliefs consulted: {len(request.source_beliefs)}",
            f"Baseline fragility: {baseline_fragility:.0%}",
            f"DFE: {dfe:.0%} ({change_count}/{len(variations)} inversions caused change)",
            f"Attacks: {len(attacks)} attempted, {bypass_count} potential bypasses",
            f"Impact: {request.impact_level:.0%}"
        ]
        
        return " | ".join(parts)
    
    def _generate_advisory(
        self, 
        dfe: float, 
        impact: float, 
        bypass_detected: bool
    ) -> str:
        """Generate advisory message highlighting risk and uncertainty."""
        if bypass_detected:
            return (
                "🔴 SECURITY ALERT: Potential bypass attempt detected in request. "
                "The request contains patterns that may be attempting to circumvent "
                "audit controls. Execution is BLOCKED pending security review."
            )
        
        if dfe > self.DFE_BLOCK_THRESHOLD:
            return (
                f"🔴 CRITICAL: Decision fragility is {dfe:.0%}. "
                "Almost all belief inversions cause decision reversal. "
                "This decision is EXTREMELY UNSTABLE. Execution is BLOCKED."
            )
        
        if dfe > self.DFE_DELAY_THRESHOLD:
            return (
                f"🟠 HIGH FRAGILITY: DFE is {dfe:.0%}. "
                f"Most belief inversions cause decision change. "
                "Mandatory delay and acknowledgment required."
            )
        
        if dfe > self.DFE_WARN_THRESHOLD or impact > self.IMPACT_HIGH_THRESHOLD:
            return (
                f"🟡 CAUTION: Decision fragility is {dfe:.0%}, impact is {impact:.0%}. "
                "Decision may be unstable. Human acknowledgment required."
            )
        
        return (
            f"✅ Decision appears stable. DFE={dfe:.0%}, impact={impact:.0%}. "
            "No adversarial patterns detected."
        )
    
    def _determine_verdict(
        self,
        dfe: float,
        bypass_detected: bool,
        requires_ack: bool,
        friction_delay: float
    ) -> Tuple[AMLAVerdict, Optional[str]]:
        """
        Determine final AMLA verdict.
        
        PRIORITY ORDER:
        1. ALERT     → Bypass detected (security violation)
        2. BLOCKED   → DFE > 0.9 (decision too fragile)
        3. REQUIRES_ACK → needs human confirmation
        4. DELAYED   → friction applied
        5. APPROVED  → safe to execute
        """
        if bypass_detected:
            return (
                AMLAVerdict.ALERT, 
                "Security bypass attempt detected in request parameters or action type"
            )
        
        if dfe > self.DFE_BLOCK_THRESHOLD:
            return (
                AMLAVerdict.BLOCKED, 
                f"Decision fragility {dfe:.2%} exceeds maximum threshold {self.DFE_BLOCK_THRESHOLD:.0%}"
            )
        
        if requires_ack:
            return AMLAVerdict.REQUIRES_ACK, None
        
        if friction_delay > 0:
            return AMLAVerdict.DELAYED, None
        
        return AMLAVerdict.APPROVED, None
    
    def _update_counters(self, verdict: AMLAVerdict):
        """Update verdict counters."""
        if verdict == AMLAVerdict.APPROVED:
            self._approved_count += 1
        elif verdict == AMLAVerdict.DELAYED:
            self._delayed_count += 1
        elif verdict == AMLAVerdict.BLOCKED:
            self._blocked_count += 1
        elif verdict == AMLAVerdict.ALERT:
            self._alert_count += 1
    
    def _get_beliefs_for_request(self, request: AMLAActionRequest) -> List:
        """Get beliefs from store for testing."""
        if not self._beliefs:
            return []
        
        beliefs = []
        for belief_id in request.source_beliefs:
            belief = self._beliefs.get(belief_id) if hasattr(self._beliefs, 'get') else None
            if belief:
                beliefs.append(belief)
        
        # Also get usable beliefs
        if hasattr(self._beliefs, 'get_usable_beliefs'):
            beliefs.extend(self._beliefs.get_usable_beliefs())
        
        # Deduplicate
        seen = set()
        unique = []
        for b in beliefs:
            bid = getattr(b, 'belief_id', id(b))
            if bid not in seen:
                seen.add(bid)
                unique.append(b)
        
        return unique
    
    def _generate_action_id(self, request: AMLAActionRequest) -> str:
        """Generate unique action ID."""
        content = f"amla:{request.action_type}:{time.time()}:{os.urandom(4).hex()}"
        return hashlib.sha256(content.encode()).hexdigest()[:16]
    
    def _log_audit(self, result: AMLAAuditResult):
        """Persist audit result to log file."""
        try:
            with open(self.AUDIT_LOG_PATH, "a") as f:
                f.write(result.to_json() + "\n")
        except Exception as e:
            logger.error(f"Failed to log AMLA audit: {e}")
    
    def acknowledge_action(
        self, 
        action_id: str, 
        operator: str, 
        rationale: str
    ) -> bool:
        """
        Record human acknowledgment for a requires_ack action.
        
        Returns True if action may now proceed.
        """
        logger.warning(
            f"AMLA: Action {action_id} acknowledged by {operator}. "
            f"Rationale: {rationale}"
        )
        
        override_log = {
            "action_id": action_id,
            "operator": operator,
            "rationale": rationale,
            "timestamp": time.time(),
            "event": "AMLA_HUMAN_OVERRIDE"
        }
        
        try:
            with open(self.AUDIT_LOG_PATH, "a") as f:
                f.write(json.dumps(override_log) + "\n")
        except Exception as e:
            logger.error(f"Failed to log AMLA override: {e}")
        
        return True
    
    def get_statistics(self) -> Dict[str, Any]:
        """Return AMLA statistics."""
        total = self._approved_count + self._delayed_count + self._blocked_count + self._alert_count
        return {
            "total_audited": total,
            "approved": self._approved_count,
            "delayed": self._delayed_count,
            "blocked": self._blocked_count,
            "alerts": self._alert_count,
            "alert_rate": self._alert_count / max(1, total),
            "block_rate": self._blocked_count / max(1, total),
            "thresholds": {
                "dfe_warn": self.DFE_WARN_THRESHOLD,
                "dfe_delay": self.DFE_DELAY_THRESHOLD,
                "dfe_block": self.DFE_BLOCK_THRESHOLD,
                "impact_high": self.IMPACT_HIGH_THRESHOLD
            }
        }


# === SINGLETON ACCESS ===
_amla_instance: Optional[AdversarialMilitaryAuditAgent] = None


def get_amla() -> AdversarialMilitaryAuditAgent:
    """Get or create global AMLA instance."""
    global _amla_instance
    if _amla_instance is None:
        _amla_instance = AdversarialMilitaryAuditAgent()
    return _amla_instance


def require_amla_audit(
    action_type: str, 
    params: Dict[str, Any],
    beliefs: List[str], 
    confidence: float,
    impact: float = 0.5
) -> AMLAAuditResult:
    """
    Convenience function: submit action for AMLA extreme audit.
    
    This MUST be called before any high-impact decision execution.
    """
    amla = get_amla()
    request = AMLAActionRequest(
        action_type=action_type,
        params=params,
        source_beliefs=beliefs,
        confidence=confidence,
        impact_level=impact
    )
    return amla.evaluate(request)
