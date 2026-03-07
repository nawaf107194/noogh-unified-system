"""
Strict Reasoning Engine for Mathematical and Logical Queries
Enforces rigorous step-by-step reasoning with verification
"""

import re
from dataclasses import dataclass
from typing import Any, Dict, List, Optional


@dataclass
class ReasoningStep:
    """Represents a single reasoning step"""

    step_number: int
    statement: str
    justification: str
    verification: Optional[str] = None
    assumptions: List[str] = None

    def __post_init__(self):
            if self.assumptions is not None:
                return
            self.assumptions = []


class StrictReasoningEngine:
    """
    Strict mathematical reasoning engine with verification
    Enforces step-by-step derivation and dimensional consistency
    """

    def __init__(self, base_model=None):
        """
        Initialize strict reasoning engine

        Args:
            base_model: Base LLM model for generation
        """
        self.model = base_model
        self.strict_prompt = self._create_strict_prompt()

    def _create_strict_prompt(self) -> str:
        """Create strict reasoning prompt — XML-structured with adaptive depth"""
        return """<identity>
أنت محرك الاستدلال الصارم في نظام NOOGH. متخصص في الرياضيات والمنطق.
</identity>

<rules>
1. أجب بالعربية دائماً
2. لا تخترع معادلات أو ثوابت — استخدم فقط ما هو معطى
3. لا تتخطى خطوات — كل خطوة يجب أن تبني على سابقتها
4. إذا اكتشفت خطأ في خطوة سابقة، صححه فوراً واشرح التصحيح
5. تحقق من تجانس الوحدات (dimensional consistency) في كل خطوة
6. لا تقل "أعتقد" أو "ربما" — كن حاسماً أو اعترف بعدم اليقين
</rules>

<adaptive_depth>
- سؤال بسيط (حساب مباشر): خطوة واحدة + الإجابة
- سؤال متوسط (معادلة): 2-3 خطوات + تحقق
- سؤال معقد (برهان/تحليل): خطوات كاملة + تحقق + مراجعة
</adaptive_depth>

<format>
ASSUMPTIONS:
- [اذكر الافتراضات فقط إذا وُجدت]

STEP 1: [الخطوة الأولى مع المبرر]
VERIFICATION: [تحقق من صحة هذه الخطوة]

STEP N: [الخطوة الأخيرة]
VERIFICATION: [تحقق نهائي]

FINAL ANSWER: [الإجابة النهائية — رقم أو تعبير واضح]
</format>

<error_protocol>
إذا اكتشفت خطأ أثناء التحقق:
1. اكتب: "⚠️ تصحيح: [وصف الخطأ]"
2. أعد الخطوة بالشكل الصحيح
3. تابع من الخطوة المصححة
</error_protocol>"""

    def process(self, query: str, context: List[str] = None) -> Dict[str, Any]:
        """
        Process query with strict reasoning

        Args:
            query: Mathematical/logical query
            context: Optional context

        Returns:
            Structured reasoning response
        """
        if context is None:
            context = []

        # Build full prompt
        full_prompt = f"{self.strict_prompt}\n\nQUERY: {query}\n\nREASONING:"

        # Generate response (using base model if available)
        if self.model:
            raw_response = self._generate_with_model(full_prompt)
        else:
            # Fallback: structured template
            raw_response = self._generate_structured_template(query)

        # Parse response into structured format
        parsed = self._parse_response(raw_response)

        return {
            "query": query,
            "raw_response": raw_response,
            "assumptions": parsed["assumptions"],
            "steps": parsed["steps"],
            "final_answer": parsed["final_answer"],
            "is_valid": parsed["is_valid"],
            "failure_reason": parsed.get("failure_reason"),
        }

    def _generate_with_model(self, prompt: str) -> str:
        """Generate response using base model"""
        try:
            # Use model's generate method
            if hasattr(self.model, "process"):
                return self.model.process(prompt, context=[])
            elif hasattr(self.model, "generate"):
                return self.model.generate(prompt)
            else:
                return self._generate_structured_template(prompt)
        except Exception as e:
            return f"N/A - Model generation failed: {e}"

    def _generate_structured_template(self, query: str) -> str:
        """Generate structured template response"""
        return """ASSUMPTIONS:
- Query requires mathematical reasoning
- Standard mathematical definitions apply

STEP 1: Analyze the query
JUSTIFICATION: Understanding the problem is the first step
VERIFICATION: Query is well-formed

STEP 2: [Specific to query]
JUSTIFICATION: [Would be derived from query]
VERIFICATION: [Would check consistency]

FINAL ANSWER: [Would be computed based on query]

NOTE: This is a template. Actual implementation requires integration with reasoning model.
"""

    def _parse_response(self, response: str) -> Dict[str, Any]:
        """
        Parse structured response

        Args:
            response: Raw response text

        Returns:
            Parsed structure
        """
        # Check for N/A (failure case)
        if response.strip().startswith("N/A"):
            return {
                "assumptions": [],
                "steps": [],
                "final_answer": "N/A",
                "is_valid": False,
                "failure_reason": response.replace("N/A", "").strip(),
            }

        # Extract assumptions
        assumptions = self._extract_assumptions(response)

        # Extract steps
        steps = self._extract_steps(response)

        # Extract final answer
        final_answer = self._extract_final_answer(response)

        return {"assumptions": assumptions, "steps": steps, "final_answer": final_answer, "is_valid": True}

    def _extract_assumptions(self, text: str) -> List[str]:
            """Extract assumptions from response"""
            if not isinstance(text, str):
                raise TypeError("Input 'text' must be a string.")

            assumptions = []
            try:
                # Find ASSUMPTIONS section
                match = re.search(r"ASSUMPTIONS?:(.*?)(?:STEP|$)", text, re.DOTALL | re.IGNORECASE)
                if match:
                    assumptions_text = match.group(1).strip()
                    # Extract bullet points
                    assumptions = [
                        line.strip("- ").strip() for line in assumptions_text.split("\n") if line.strip().startswith("-")
                    ]
                    if not assumptions:
                        logging.warning("Found ASSUMPTIONS section but no valid bullet points extracted.")
                else:
                    logging.warning("No ASSUMPTIONS section found in the provided text.")
            except re.error as e:
                logging.error(f"Regular expression error occurred while searching for assumptions: {e}")
                raise
            except Exception as e:
                logging.error(f"An unexpected error occurred while extracting assumptions: {e}")
                raise

            return assumptions

    def _extract_steps(self, text: str) -> List[ReasoningStep]:
        """Extract reasoning steps from response"""
        steps = []

        # Find all STEP sections
        step_pattern = r"STEP\s+(\d+):(.*?)(?=STEP\s+\d+:|FINAL ANSWER:|$)"
        matches = re.finditer(step_pattern, text, re.DOTALL | re.IGNORECASE)

        for match in matches:
            step_num = int(match.group(1))
            step_content = match.group(2)

            # Extract components
            statement = self._extract_field(step_content, "statement")
            justification = self._extract_field(step_content, "JUSTIFICATION")
            verification = self._extract_field(step_content, "VERIFICATION")

            steps.append(
                ReasoningStep(
                    step_number=step_num, statement=statement, justification=justification, verification=verification
                )
            )

        return steps

    def _extract_field(self, text: str, field_name: str) -> str:
        """Extract a specific field from text"""
        if field_name == "statement":
            # Statement is the first line before JUSTIFICATION
            lines = text.split("\n")
            for line in lines:
                line = line.strip()
                if line and not line.startswith(("JUSTIFICATION", "VERIFICATION")):
                    return line
            return ""

        # Extract other fields
        pattern = f"{field_name}:(.*?)(?=JUSTIFICATION:|VERIFICATION:|STEP|$)"
        match = re.search(pattern, text, re.DOTALL | re.IGNORECASE)
        if match:
            return match.group(1).strip()
        return ""

    def _extract_final_answer(self, text: str) -> str:
            """Extract final answer from response"""
            if not isinstance(text, str):
                raise TypeError("Input 'text' must be a string")

            try:
                match = re.search(r"FINAL ANSWER:(.*?)(?:$|\n\n)", text, re.DOTALL | re.IGNORECASE)
                if match:
                    return match.group(1).strip()
                else:
                    self.logger.warning("No match found in the provided text.")
                    return "Not found"
            except Exception as e:
                self.logger.error(f"An error occurred while extracting the final answer: {e}")
                raise


if __name__ == "__main__":
    # Test strict reasoning engine
    engine = StrictReasoningEngine()

    test_query = "Calculate the determinant of the 2x2 matrix [[a, b], [c, d]]"

    result = engine.process(test_query)

    print("Strict Reasoning Engine Test\n")
    print(f"Query: {result['query']}")
    print(f"\nAssumptions: {result['assumptions']}")
    print(f"\nSteps: {len(result['steps'])}")
    for step in result["steps"]:
        print(f"  Step {step.step_number}: {step.statement}")
    print(f"\nFinal Answer: {result['final_answer']}")
    print(f"Valid: {result['is_valid']}")
