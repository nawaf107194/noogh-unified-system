from dataclasses import dataclass, field
from typing import Any, Dict, List, Literal, Optional


@dataclass
class ConfidenceScore:
    value: float
    level: Literal["HIGH", "MEDIUM", "LOW", "UNSAFE"]
    reasons: List[str] = field(default_factory=list)


class ConfidenceScorer:
    """
    Deterministic confidence scorer for NOOGH.
    Relies ONLY on execution metrics, not LLM judgement.
    """

    @staticmethod
    def evaluate(
        success: bool,
        iterations: int,
        has_protocol_violation: bool,
        is_unsupported: bool,
        executed_sandbox: bool,
        error: Optional[str] = None,
        mode: str = "EXECUTE",
    ) -> Optional[ConfidenceScore]:
        """
        Calculate confidence score based on strict rules.
        Returns None if mode is PLAN (No confidence without execution).
        """

        # Rule: No Confidence Without Execution
        if mode == "PLAN":
            return None

        reasons = []
        value = 1.0
        level = "HIGH"

        # 1. Critical Failure Check
        if is_unsupported or (error and "UNSUPPORTED" in str(error)):
            return ConfidenceScore(
                value=0.0, level="UNSAFE", reasons=["Task result is UNSUPPORTED or Capability Violation"]
            )

        if not success:
            return ConfidenceScore(value=0.0, level="LOW", reasons=[f"Task failed: {error}"])

        # 2. Penalty: Protocol Violations
        if has_protocol_violation:
            value -= 0.4
            reasons.append("Protocol violation detected during execution")
            level = "LOW"  # Strict rule from requirements

        # 3. Penalty: Iterations
        if iterations > 3:
            penalty = 0.2 * (iterations - 3)
            value -= penalty
            reasons.append(f"High iteration count ({iterations})")
            if level == "HIGH":
                level = "MEDIUM"

        # 4. Bonus/Requirement: Sandbox
        if executed_sandbox:
            # If code ran cleanly, it verifies the logic somewhat.
            # But if iterations were high, we already penalized.
            pass
        else:
            # If no code was executed in EXECUTE mode (e.g. just chat), confidence is lower for engineering tasks?
            # Requirement says: "Sandbox execution clean + 1 iteration => HIGH"
            # Does not explicitly penalize no-sandbox, but implies it's the gold standard.
            pass

        # 5. Iterations constraint for HIGH
        if iterations > 3 and level == "HIGH":
            level = "MEDIUM"  # Fallback if not already lowered

        # Clamp value
        value = max(0.0, min(1.0, value))

        # Final Level Determination (if not forced yet)
        if level not in ["LOW", "UNSAFE"]:
            if value >= 0.8:
                level = "HIGH"
            elif value >= 0.5:
                level = "MEDIUM"
            else:
                level = "LOW"

        return ConfidenceScore(value=round(value, 2), level=level, reasons=reasons)

    def score(self, task: str, answer: str, thought: str) -> Dict[str, Any]:
        """
        V2.0 Semantic Confidence Scoring (Placeholder).
        In the future, this will use the Estimator LLM.
        For now, returns a default high confidence.
        """
        return {"score": 0.9, "level": "HIGH", "reason": "Default semantic confidence"}
