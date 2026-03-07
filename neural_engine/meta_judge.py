"""
Meta-Judge for Final Validation
Has override authority over evaluator decisions
"""

from dataclasses import dataclass
from typing import Any, Dict, Optional


@dataclass
class Judgment:
    """Final judgment from meta-judge"""

    judgment: str  # ACCEPT or REJECT
    output: str  # Final output to user
    reason: Optional[str] = None
    override_applied: bool = False


class MetaJudge:
    """
    Meta-judge with final authority over mathematical reasoning
    Can override evaluator and enforce format requirements
    """

    def __init__(self):
        self.acceptance_threshold = 80
        self.required_evaluation_keys = ["score", "issues", "auto_fail", "evaluation"]

    def judge(self, response: Dict[str, Any], evaluation: Dict[str, Any]) -> Judgment:
        """
        Make final judgment on mathematical reasoning

        Args:
            response: Original response from StrictReasoningEngine
            evaluation: Evaluation from MathematicalEvaluator

        Returns:
            Final judgment
        """
        # Validation Step 1: Validate evaluation object
        if not self._validate_evaluation(evaluation):
            return Judgment(judgment="REJECT", output="N/A", reason="INVALID_EVALUATION_OBJECT", override_applied=True)

        # Validation Step 2: Check auto-fail
        if evaluation.get("auto_fail", False):
            return Judgment(judgment="REJECT", output="N/A", reason="AUTO_FAIL_TRIGGERED", override_applied=False)

        # Validation Step 3: Check format violations
        format_check = self._check_format_violations(response)
        if format_check["has_violations"]:
            return Judgment(judgment="REJECT", output="N/A", reason="FORMAT_VIOLATION", override_applied=True)

        # Validation Step 4: Check score threshold
        score = evaluation.get("score", 0)
        if score < self.acceptance_threshold:
            return Judgment(
                judgment="REJECT",
                output="N/A",
                reason=f"SCORE_BELOW_THRESHOLD ({score} < {self.acceptance_threshold})",
                override_applied=False,
            )

        # Validation Step 5: Final safety checks
        safety_check = self._final_safety_check(response, evaluation)
        if not safety_check["safe"]:
            return Judgment(
                judgment="REJECT",
                output="N/A",
                reason=f"SAFETY_CHECK_FAILED: {safety_check['reason']}",
                override_applied=True,
            )

        # All checks passed - ACCEPT
        return Judgment(
            judgment="ACCEPT",
            output=response.get("raw_response", response.get("final_answer", "No response")),
            reason="ALL_CHECKS_PASSED",
            override_applied=False,
        )

    def _validate_evaluation(self, evaluation: Dict[str, Any]) -> bool:
        """
        Validate evaluation object structure

        Args:
            evaluation: Evaluation object to validate

        Returns:
            True if valid
        """
        # Check if it's a dict or dataclass
        if hasattr(evaluation, "__dict__"):
            evaluation = evaluation.__dict__

        # Check required keys
        for key in self.required_evaluation_keys:
            if key not in evaluation:
                return False

        # Check score is in valid range
        score = evaluation.get("score")
        if not isinstance(score, (int, float)) or score < 0 or score > 100:
            return False

        return True

    def _check_format_violations(self, response: Dict[str, Any]) -> Dict[str, Any]:
        """
        Check for format violations in response

        Args:
            response: Response to check

        Returns:
            Format violation details
        """
        violations = []

        # Check 1: Must have assumptions
        if not response.get("assumptions"):
            violations.append("Missing ASSUMPTIONS section")

        # Check 2: Must have steps
        steps = response.get("steps", [])
        if len(steps) == 0:
            violations.append("Missing STEP sections")

        # Check 3: Must have final answer
        if not response.get("final_answer"):
            violations.append("Missing FINAL ANSWER")

        # Check 4: Steps must have required fields
        for step in steps:
            if not hasattr(step, "justification") or not step.justification:
                violations.append(f"Step {step.step_number} missing JUSTIFICATION")
            if not hasattr(step, "verification") or not step.verification:
                violations.append(f"Step {step.step_number} missing VERIFICATION")

        return {"has_violations": len(violations) > 0, "violations": violations}

    def _final_safety_check(self, response: Dict[str, Any], evaluation: Dict[str, Any]) -> Dict[str, Any]:
        """
        Final safety check before acceptance

        Args:
            response: Response to check
            evaluation: Evaluation result

        Returns:
            Safety check result
        """
        # Check 1: No critical issues
        if hasattr(evaluation, "issues"):
            issues = evaluation.issues
        else:
            issues = evaluation.get("issues", [])

        critical_issues = ["DIMENSIONAL_INCONSISTENCY", "FORMULA_MEMORIZATION", "UNVERIFIED_STEPS"]

        for issue in issues:
            if issue in critical_issues:
                return {"safe": False, "reason": f"Critical issue present: {issue}"}

        # Check 2: Response is not N/A
        if response.get("final_answer") == "N/A":
            return {"safe": False, "reason": "Response is N/A"}

        # All safety checks passed
        return {"safe": True, "reason": None}

    def get_judgment_summary(self, judgment: Judgment) -> str:
        """Get human-readable judgment summary"""
        summary = f"Judgment: {judgment.judgment}\n"

        if judgment.reason:
            summary += f"Reason: {judgment.reason}\n"

        if judgment.override_applied:
            summary += "⚠️ META-JUDGE OVERRIDE APPLIED\n"

        if judgment.judgment == "ACCEPT":
            summary += f"\nOutput:\n{judgment.output}\n"
        else:
            summary += f"\nOutput: {judgment.output}\n"

        return summary


if __name__ == "__main__":
    # Test meta-judge
    from mathematical_evaluator import EvaluationResult

    meta_judge = MetaJudge()

    # Test case 1: Valid evaluation, good score
    good_response = {
        "assumptions": ["Matrix is 2x2"],
        "steps": [
            type(
                "Step",
                (),
                {"step_number": 1, "statement": "Define", "justification": "Clear", "verification": "Checked"},
            )()
        ],
        "final_answer": "ad - bc",
        "raw_response": "Complete response",
    }

    good_evaluation = EvaluationResult(score=90, issues=[], auto_fail=False, evaluation="PASS", details={})

    judgment = meta_judge.judge(good_response, good_evaluation.__dict__)
    print("Test Case 1: Good Response")
    print(meta_judge.get_judgment_summary(judgment))
    print("-" * 60)

    # Test case 2: Auto-fail triggered
    bad_evaluation = EvaluationResult(
        score=0, issues=["RED_FLAGS_DETECTED"], auto_fail=True, evaluation="FAIL", details={}
    )

    judgment = meta_judge.judge(good_response, bad_evaluation.__dict__)
    print("\nTest Case 2: Auto-Fail")
    print(meta_judge.get_judgment_summary(judgment))
