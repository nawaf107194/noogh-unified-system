import pytest
import re

class ReasoningStep:
    def __init__(self, step_number: int, statement: str, justification: str, verification: str):
        self.step_number = step_number
        self.statement = statement
        self.justification = justification
        self.verification = verification

def _extract_steps(text: str) -> List[ReasoningStep]:
    """Extract reasoning steps from response"""
    steps = []

    # Find all STEP sections
    step_pattern = r"STEP\s+(\d+):(.*?)(?=STEP\s+\d+:|FINAL ANSWER:|$)"
    matches = re.finditer(step_pattern, text, re.DOTALL | re.IGNORECASE)

    for match in matches:
        step_num = int(match.group(1))
        step_content = match.group(2)

        # Extract components
        statement = _extract_field(step_content, "statement")
        justification = _extract_field(step_content, "JUSTIFICATION")
        verification = _extract_field(step_content, "VERIFICATION")

        steps.append(
            ReasoningStep(
                step_number=step_num, statement=statement, justification=justification, verification=verification
            )
        )

    return steps

def _extract_field(content: str, field_name: str) -> str:
    """Extract a specific field from the content"""
    pattern = fr"{field_name.upper()}\s*:\s*(.*?)(?:\n\s*STEP|\nFINAL ANSWER|$)"
    match = re.search(pattern, content, re.DOTALL)
    return match.group(1).strip() if match else ""

# Test cases
def test_extract_steps_happy_path():
    text = """
STEP 1: statement = This is step one. justification = Justified because it's the first step.
statement = This is another line in the step content.
VERIFICATION: Verified that this is correct.

STEP 2: statement = This is step two. justification = Justified because it follows step one.
VERIFICATION: Verified that this is also correct.
"""
    expected_steps = [
        ReasoningStep(
            step_number=1,
            statement="This is step one. statement = This is another line in the step content.",
            justification="Justified because it's the first step.",
            verification="Verified that this is correct."
        ),
        ReasoningStep(
            step_number=2,
            statement="This is step two.",
            justification="Justified because it follows step one.",
            verification="Verified that this is also correct."
        )
    ]
    assert _extract_steps(text) == expected_steps

def test_extract_steps_empty():
    text = ""
    assert _extract_steps(text) == []

def test_extract_steps_none():
    text = None
    assert _extract_steps(text) == []

def test_extract_steps_boundary():
    text = """
STEP 1: statement = This is step one.
"""
    expected_step = ReasoningStep(
        step_number=1,
        statement="This is step one.",
        justification=None,
        verification=None
    )
    assert _extract_steps(text) == [expected_step]

def test_extract_steps_invalid_format():
    text = """
STEP 1: statement = This is step one.
INVALID_FIELD: Invalid value
"""
    expected_steps = [
        ReasoningStep(
            step_number=1,
            statement="This is step one.",
            justification=None,
            verification=None
        )
    ]
    assert _extract_steps(text) == expected_steps