"""
Execution Enforcer - Forces execution, prevents conversational evasion
"""

import re
from typing import Dict


class ExecutionEnforcer:
    """
    Enforces execution mode and prevents conversational fallback
    """

    def __init__(self):
        self.mode = "STRICT_EXECUTION"
        self.role_locked = True

    def enforce_role(self, query: str) -> Dict:
        """
        Enforce execution role based on query type
        """
        query_type = self._classify_query(query)

        if query_type == "MATHEMATICAL_DERIVATION":
            return {
                "mode": "EXECUTE",
                "allowed_outputs": ["DERIVATION", "N/A"],
                "forbidden_outputs": ["EXPLANATION", "DESCRIPTION", "COMMENTARY"],
                "role": "EXECUTOR",
                "fallback": "FORBIDDEN",
            }

        return {"mode": "CONVERSATIONAL"}

    def _classify_query(self, query: str) -> str:
        """Classify query type"""
        math_keywords = [
            "derive",
            "prove",
            "calculate",
            "determinant",
            "matrix",
            "اشتق",
            "أثبت",
            "احسب",
            "محدد",
            "مصفوفة",
        ]

        query_lower = query.lower()
        if any(kw in query_lower for kw in math_keywords):
            return "MATHEMATICAL_DERIVATION"

        return "GENERAL"

    def validate_execution(self, query: str, response: str) -> Dict:
        """
        Validate that response is execution, not conversation
        """
        # Check for evasion markers
        evasion_markers = [
            "this is a",
            "the given test",
            "performance evaluation",
            "not an assistance",
            "هذا اختبار",
            "تقييم أداء",
        ]

        for marker in evasion_markers:
            if marker.lower() in response.lower():
                return {"valid": False, "reason": "CONVERSATIONAL_EVASION", "action": "REJECT_AND_ENFORCE_N/A"}

        # Check for execution markers
        execution_markers = [
            "step 1:",
            "step 2:",
            "therefore",
            "since",
            "خطوة 1:",
            "خطوة 2:",
            "إذن",
            "بما أن",
            "cannot be concluded",
        ]

        has_execution = any(marker.lower() in response.lower() for marker in execution_markers)

        if not has_execution:
            return {"valid": False, "reason": "NO_EXECUTION_DETECTED", "action": "FORCE_FAILURE_GATE"}

        return {"valid": True}


class StrictModeValidator:
    """
    Validates that output matches strict mode requirements
    """

    def validate_output(self, query: str, response: str) -> Dict:
        """
        Strict validation of output
        """
        # Rule 1: Either derivation or N/A
        has_derivation = self._has_derivation(response)
        has_failure_gate = "cannot be concluded" in response.lower()

        if not (has_derivation or has_failure_gate):
            return {"valid": False, "reason": "NEITHER_DERIVATION_NOR_FAILURE_GATE", "required_action": "OUTPUT_N/A"}

        # Rule 2: No linguistic description
        if self._is_description(response):
            return {"valid": False, "reason": "DESCRIPTION_NOT_DERIVATION", "required_action": "OUTPUT_N/A"}

        # Rule 3: No role reinterpretation
        if self._reinterprets_role(response):
            return {"valid": False, "reason": "ROLE_REINTERPRETATION", "required_action": "OUTPUT_N/A"}

        return {"valid": True}

    def _has_derivation(self, response: str) -> bool:
        """Check for actual derivation"""
        derivation_indicators = ["step", "therefore", "since", "خطوة", "إذن", "بما أن"]
        return any(ind in response.lower() for ind in derivation_indicators)

    def _is_description(self, response: str) -> bool:
        """Detect linguistic description"""
        description_markers = ["is a", "represents", "denotes", "هو", "يمثل", "يشير"]
        return any(marker in response.lower() for marker in description_markers)

    def _reinterprets_role(self, response: str) -> bool:
        """Detect role reinterpretation"""
        role_reinterpretation = [
            "this is a test",
            "performance evaluation",
            "not an assistance question",
            "هذا اختبار",
            "تقييم",
        ]
        return any(phrase in response.lower() for phrase in role_reinterpretation)


class OutputVerifier:
    """
    Verifies output is execution, not conversation
    """

    def verify_and_enforce(self, query: str, response: str) -> str:
        """
        Verify output and enforce N/A if needed
        """
        # Check 1: Is it execution?
        if not self._is_execution(response):
            return "Cannot be concluded with certainty."

        # Check 2: Is it derivation?
        if not self._is_derivation(response):
            return "Cannot be concluded with certainty."

        # Check 3: Does it have steps?
        if not self._has_steps(response):
            return "Cannot be concluded with certainty."

        # All checks passed
        return response

    def _is_execution(self, response: str) -> bool:
        """Is response execution?"""
        forbidden = ["is a", "represents", "this test", "evaluation"]
        return not any(f in response.lower() for f in forbidden)

    def _is_derivation(self, response: str) -> bool:
        """Is response derivation?"""
        required = ["step", "therefore", "since", "خطوة", "إذن"]
        return any(r in response.lower() for r in required)

    def _has_steps(self, response: str) -> bool:
        """Does it have steps?"""
        steps = re.findall(r"step \d+|خطوة \d+", response.lower())
        return len(steps) >= 2  # At least 2 steps


if __name__ == "__main__":
    # Test
    enforcer = ExecutionEnforcer()
    validator = StrictModeValidator()
    verifier = OutputVerifier()

    # Test query
    query = "Derive the determinant of matrix A"

    # Test evasive response
    bad_response = "The given test is a performance evaluation..."

    enforcement = enforcer.enforce_role(query)
    print(f"Enforcement: {enforcement}")

    validation = enforcer.validate_execution(query, bad_response)
    print(f"Validation: {validation}")

    if not validation["valid"]:
        print("❌ REJECTED - Conversational evasion detected")
        print("✅ ENFORCING: Cannot be concluded with certainty.")
