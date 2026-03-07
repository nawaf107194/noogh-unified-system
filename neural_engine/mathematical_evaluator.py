"""
Mathematical Evaluator with Auto-Fail Rules
Verifies mathematical correctness and enforces strict standards
"""

import re
from dataclasses import dataclass
from typing import Any, Dict, List


@dataclass
class EvaluationResult:
    """Result of mathematical evaluation"""

    score: int  # 0-100
    issues: List[str]
    auto_fail: bool
    evaluation: str  # PASS or FAIL
    details: Dict[str, Any]


class MathematicalEvaluator:
    """
    Evaluates mathematical reasoning for correctness
    Enforces auto-fail rules for critical violations
    """

    def __init__(self):
        self.auto_fail_threshold = 0

        # Red flags that trigger auto-fail
        self.red_flags = [
            "approximately",
            "roughly",
            "about",
            "around",
            "unclear",
            "unsure",
            "maybe",
            "probably",
            "i think",
            "i believe",
            "seems like",
            "تقريباً",
            "حوالي",
            "ربما",
            "غير واضح",
        ]

        # Vague language patterns
        self.vague_patterns = [
            r"about\s+\d+",
            r"roughly\s+\d+",
            r"approximately\s+\d+",
        ]

    def evaluate(self, response: Dict[str, Any]) -> EvaluationResult:
        """
        Evaluate mathematical reasoning response

        Args:
            response: Structured response from StrictReasoningEngine

        Returns:
            Evaluation result with score and issues
        """
        score = 100
        issues = []
        details = {}

        # Auto-Fail Check 1: N/A response
        if response.get("final_answer") == "N/A" or not response.get("is_valid", True):
            return EvaluationResult(
                score=0,
                issues=["RESPONSE_IS_NA"],
                auto_fail=True,
                evaluation="FAIL",
                details={"reason": "System returned N/A"},
            )

        # Auto-Fail Check 2: Red flags in response
        red_flag_check = self._check_red_flags(response)
        if red_flag_check["has_red_flags"]:
            score = 0
            issues.append("RED_FLAGS_DETECTED")
            details["red_flags"] = red_flag_check["flags_found"]

        # Auto-Fail Check 3: Missing assumptions
        if not response.get("assumptions"):
            score = min(score, 50)
            issues.append("NO_ASSUMPTIONS_STATED")

        # Auto-Fail Check 4: Missing steps
        steps = response.get("steps", [])
        if len(steps) == 0:
            score = 0
            issues.append("NO_REASONING_STEPS")

        # Auto-Fail Check 5: Unverified steps
        unverified_check = self._check_step_verification(steps)
        if not unverified_check["all_verified"]:
            score = 0
            issues.append("UNVERIFIED_STEPS")
            details["unverified_steps"] = unverified_check["unverified"]

        # Auto-Fail Check 6: Dimensional inconsistency
        dimensional_check = self._check_dimensional_consistency(response)
        if not dimensional_check["consistent"]:
            score = 0
            issues.append("DIMENSIONAL_INCONSISTENCY")
            details["dimensional_issues"] = dimensional_check["issues"]

        # Auto-Fail Check 7: Formula without derivation
        formula_check = self._check_formula_derivation(response)
        if not formula_check["all_derived"]:
            score = 0
            issues.append("FORMULA_MEMORIZATION")
            details["underived_formulas"] = formula_check["underived"]

        # Determine auto-fail
        auto_fail = score <= self.auto_fail_threshold
        evaluation = "FAIL" if auto_fail else "PASS"

        return EvaluationResult(score=score, issues=issues, auto_fail=auto_fail, evaluation=evaluation, details=details)

    def _check_red_flags(self, response: Dict[str, Any]) -> Dict[str, Any]:
        """Check for red flag language"""
        raw_text = response.get("raw_response", "").lower()

        flags_found = []
        for flag in self.red_flags:
            if flag in raw_text:
                flags_found.append(flag)

        # Check vague patterns
        for pattern in self.vague_patterns:
            if re.search(pattern, raw_text, re.IGNORECASE):
                flags_found.append(f"vague_pattern: {pattern}")

        return {"has_red_flags": len(flags_found) > 0, "flags_found": flags_found}

    def _check_step_verification(self, steps: List) -> Dict[str, Any]:
        """Check if all steps have verification"""
        unverified = []

        for step in steps:
            if not hasattr(step, "verification") or not step.verification:
                unverified.append(step.step_number)

        return {"all_verified": len(unverified) == 0, "unverified": unverified}

    def _check_dimensional_consistency(self, response: Dict[str, Any]) -> Dict[str, Any]:
        """
        Check dimensional consistency

        Note: This is a simplified check. Full implementation would require
        parsing equations and tracking dimensions through calculations.
        """
        issues = []

        # Check if verification mentions dimensions
        steps = response.get("steps", [])
        has_dimensional_checks = False

        for step in steps:
            if hasattr(step, "verification") and step.verification:
                if any(word in step.verification.lower() for word in ["dimension", "unit", "بعد", "وحدة"]):
                    has_dimensional_checks = True
                    break

        # If mathematical query involves units, dimensional checks are required
        raw_text = response.get("raw_response", "")
        has_units = any(unit in raw_text.lower() for unit in ["meter", "second", "kg", "متر", "ثانية"])

        if has_units and not has_dimensional_checks:
            issues.append("Missing dimensional verification for query with units")

        return {"consistent": len(issues) == 0, "issues": issues}

    def _check_formula_derivation(self, response: Dict[str, Any]) -> Dict[str, Any]:
        """
        Check if formulas are derived rather than memorized

        Note: This is a heuristic check. Full implementation would require
        formula database and derivation validation.
        """
        underived = []

        # Check if response uses formulas without derivation
        raw_text = response.get("raw_response", "")

        # Common formulas that should be derived
        formula_keywords = [
            "determinant formula",
            "inverse formula",
            "derivative formula",
            "integral formula",
            "صيغة المحدد",
            "صيغة المعكوس",
        ]

        for keyword in formula_keywords:
            if keyword in raw_text.lower():
                # Check if there's a derivation nearby
                if "derive" not in raw_text.lower() and "اشتق" not in raw_text.lower():
                    underived.append(keyword)

        return {"all_derived": len(underived) == 0, "underived": underived}

    def get_evaluation_summary(self, result: EvaluationResult) -> str:
            """Get human-readable evaluation summary"""
            if not isinstance(result, EvaluationResult):
                raise TypeError("The 'result' parameter must be an instance of EvaluationResult.")

            try:
                summary = f"Evaluation: {result.evaluation}\n"
                summary += f"Score: {result.score}/100\n"

                if result.auto_fail:
                    summary += "⚠️ AUTO-FAIL TRIGGERED\n"

                if result.issues:
                    summary += "\nIssues Found:\n"
                    for issue in result.issues:
                        if not isinstance(issue, str):
                            raise ValueError("Each issue must be a string.")
                        summary += f"  - {issue}\n"

                if result.details:
                    summary += "\nDetails:\n"
                    for key, value in result.details.items():
                        if not isinstance(key, str) or not isinstance(value, (str, int, float)):
                            raise ValueError("Key and value must be strings, integers, or floats.")
                        summary += f"  {key}: {value}\n"

            except Exception as e:
                self.logger.error(f"Error generating evaluation summary: {e}")
                raise

            return summary


if __name__ == "__main__":
    # Test evaluator
    evaluator = MathematicalEvaluator()

    # Test case 1: Good response
    good_response = {
        "query": "Calculate determinant",
        "raw_response": "STEP 1: Define matrix\nVERIFICATION: Dimensions consistent",
        "assumptions": ["Matrix is 2x2"],
        "steps": [
            type(
                "Step",
                (),
                {
                    "step_number": 1,
                    "statement": "Define matrix",
                    "justification": "Clear definition",
                    "verification": "Dimensions are consistent",
                },
            )()
        ],
        "final_answer": "ad - bc",
        "is_valid": True,
    }

    result = evaluator.evaluate(good_response)
    print("Test Case 1: Good Response")
    print(evaluator.get_evaluation_summary(result))
    print("-" * 60)

    # Test case 2: Bad response with red flags
    bad_response = {
        "query": "Calculate determinant",
        "raw_response": "The answer is approximately 5",
        "assumptions": [],
        "steps": [],
        "final_answer": "approximately 5",
        "is_valid": True,
    }

    result = evaluator.evaluate(bad_response)
    print("\nTest Case 2: Bad Response (Red Flags)")
    print(evaluator.get_evaluation_summary(result))
