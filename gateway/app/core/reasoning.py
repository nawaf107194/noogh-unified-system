"""
NOOGH Reasoning Evolution - Advanced reasoning capabilities.

Features:
- Self-Correction Protocol
- Capability Boundaries
- Confidence Scoring
- Memory-Aware Reasoning
"""

import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional

from gateway.app.core.logging import get_logger

logger = get_logger("reasoning")


# =============================================================================
# Capability Boundaries
# =============================================================================


class CapabilityCategory(Enum):
    """Categories of agent capabilities."""

    CAN_DO = "can_do"
    CANNOT_DO = "cannot_do"
    REQUIRES_NEURAL = "requires_neural"
    REQUIRES_APPROVAL = "requires_approval"


CAPABILITY_BOUNDARIES = {
    CapabilityCategory.CAN_DO: [
        "Execute Python code in sandbox",
        "Read files within workspace",
        "Write files within workspace",
        "List directory contents",
        "Search code with grep patterns",
        "Run pytest tests",
        "Git status and diff",
        "Mathematical calculations",
        "Data processing and analysis",
        "JSON/CSV parsing",
        "String manipulation",
        "Algorithm implementation",
    ],
    CapabilityCategory.CANNOT_DO: [
        "Access internet freely",
        "Execute system shell commands",
        "Access files outside workspace",
        "Long-running background processes",
        "Interactive user input",
        "GUI operations",
        "Network scanning",
        "System configuration changes",
        "Package installation",
        "Database server access",
        "Email/messaging",
        "Cryptocurrency operations",
    ],
    CapabilityCategory.REQUIRES_NEURAL: [
        "Image/vision analysis",
        "Long-term memory storage",
        "Semantic search/recall",
        "Advanced NLP processing",
    ],
    CapabilityCategory.REQUIRES_APPROVAL: [
        "File deletion",
        "Large file writes (>100KB)",
        "Batch file operations",
        "Running external scripts",
    ],
}

# Keywords that indicate out-of-scope requests
OUT_OF_SCOPE_KEYWORDS = {
    "hack",
    "bypass",
    "steal",
    "password",
    "credit card",
    "exploit",
    "vulnerability",
    "attack",
    "crack",
    "inject",
    "malware",
    "virus",
    "ransomware",
    "phishing",
    "keylogger",
    "backdoor",
    "rootkit",
    "delete system",
    "format disk",
    "rm -rf /",
    "sudo rm",
}

# Keywords that suggest neural service is needed
NEURAL_KEYWORDS = {
    "image",
    "picture",
    "photo",
    "vision",
    "see",
    "look at",
    "remember",
    "recall",
    "what did",
    "previously",
    "before",
    "semantic",
    "meaning",
    "understand context",
}


@dataclass
class CapabilityAssessment:
    """Result of capability assessment."""

    can_handle: bool
    category: CapabilityCategory
    confidence: float
    reason: str
    suggestion: Optional[str] = None
    requires_approval: bool = False


def assess_capability(task: str) -> CapabilityAssessment:
    """
    Assess whether task is within agent capabilities.

    Args:
        task: The task description

    Returns:
        CapabilityAssessment with verdict
    """
    task_lower = task.lower()

    # Check for out-of-scope keywords
    for keyword in OUT_OF_SCOPE_KEYWORDS:
        if keyword in task_lower:
            return CapabilityAssessment(
                can_handle=False,
                category=CapabilityCategory.CANNOT_DO,
                confidence=0.95,
                reason=f"Request contains security-sensitive keyword: '{keyword}'",
                suggestion="Please rephrase without security-sensitive terms",
            )

    # Check for neural-required tasks
    needs_neural = any(k in task_lower for k in NEURAL_KEYWORDS)
    if needs_neural:
        return CapabilityAssessment(
            can_handle=True,
            category=CapabilityCategory.REQUIRES_NEURAL,
            confidence=0.7,
            reason="Task may require neural services for optimal results",
            suggestion="Neural services will be used if available",
        )

    # Check for approval-required tasks
    approval_keywords = {"delete", "remove", "batch", "all files", "recursive"}
    needs_approval = any(k in task_lower for k in approval_keywords)
    if needs_approval:
        return CapabilityAssessment(
            can_handle=True,
            category=CapabilityCategory.REQUIRES_APPROVAL,
            confidence=0.8,
            reason="Task involves potentially destructive operations",
            requires_approval=True,
        )

    # Default: can handle
    return CapabilityAssessment(
        can_handle=True,
        category=CapabilityCategory.CAN_DO,
        confidence=0.85,
        reason="Task appears within standard capabilities",
    )


# =============================================================================
# Self-Correction Protocol
# =============================================================================

SELF_CORRECTION_TEMPLATE = """ERROR ANALYSIS REQUIRED.

═══════════════════════════════════════════════════════════════
PREVIOUS ATTEMPT FAILED
═══════════════════════════════════════════════════════════════

ERROR:
{error}

CODE THAT FAILED:
```python
{code}
```

═══════════════════════════════════════════════════════════════
SELF-CORRECTION PROTOCOL
═══════════════════════════════════════════════════════════════

You MUST follow this exact format:

ANALYSIS:
<Describe specifically what went wrong - be precise>

ROOT_CAUSE:
<Identify the actual underlying problem, not just the symptom>

ALTERNATIVE_APPROACH:
<Describe a DIFFERENT way to solve this - don't just fix syntax>

LESSONS:
<What should you remember for future similar tasks?>

CORRECTED_CODE:
```python
<New code using the alternative approach>
```

═══════════════════════════════════════════════════════════════
RULES:
- Do NOT simply add try/except around failing code
- Do NOT repeat the same approach with minor changes
- THINK about WHY it failed before writing new code
═══════════════════════════════════════════════════════════════
"""


@dataclass
class ErrorAnalysis:
    """Parsed self-correction response."""

    analysis: str
    root_cause: str
    alternative_approach: str
    lessons: str
    corrected_code: str
    is_valid: bool = True


def generate_self_correction_prompt(error: str, code: str) -> str:
    """
    Generate self-correction prompt that forces deep analysis.

    Args:
        error: The error message
        code: The code that produced the error

    Returns:
        Formatted correction prompt
    """
    # Truncate if too long
    error = error[:2000] if len(error) > 2000 else error
    code = code[:3000] if len(code) > 3000 else code

    return SELF_CORRECTION_TEMPLATE.format(error=error, code=code)


def parse_self_correction(response: str) -> ErrorAnalysis:
    """
    Parse self-correction response.

    Args:
        response: LLM response to correction prompt

    Returns:
        Parsed ErrorAnalysis
    """
    analysis = ErrorAnalysis(
        analysis="", root_cause="", alternative_approach="", lessons="", corrected_code="", is_valid=False
    )

    # Extract sections
    sections = {
        "ANALYSIS:": "analysis",
        "ROOT_CAUSE:": "root_cause",
        "ALTERNATIVE_APPROACH:": "alternative_approach",
        "LESSONS:": "lessons",
    }

    for marker, field in sections.items():
        pattern = rf"{marker}\s*(.*?)(?=(?:ANALYSIS:|ROOT_CAUSE:|ALTERNATIVE_APPROACH:|LESSONS:|CORRECTED_CODE:|$))"
        match = re.search(pattern, response, re.DOTALL | re.IGNORECASE)
        if match:
            setattr(analysis, field, match.group(1).strip())

    # Extract corrected code
    code_pattern = r"CORRECTED_CODE:.*?```(?:python)?\s*(.*?)```"
    code_match = re.search(code_pattern, response, re.DOTALL | re.IGNORECASE)
    if code_match:
        analysis.corrected_code = code_match.group(1).strip()
        analysis.is_valid = True

    return analysis


# =============================================================================
# Confidence Scoring
# =============================================================================


@dataclass
class ConfidenceScore:
    """Confidence score with breakdown."""

    overall: float  # 0.0 - 1.0
    reasoning_quality: float
    evidence_strength: float
    uncertainty_awareness: float
    factors: Dict[str, float] = field(default_factory=dict)


class ConfidenceScorer:
    """
    Score agent confidence based on reasoning quality.

    Factors:
    - Specificity: Are claims specific or vague?
    - Evidence: Does reasoning cite observations?
    - Uncertainty: Does agent acknowledge limits?
    - Verification: Did agent verify claims?
    """

    # Positive indicators (add to score)
    POSITIVE_MARKERS = {
        "because": 0.05,
        "since": 0.05,
        "therefore": 0.05,
        "based on": 0.08,
        "verified": 0.15,
        "confirmed": 0.12,
        "tested": 0.12,
        "output shows": 0.10,
        "result is": 0.08,
        "successfully": 0.10,
    }

    # Uncertainty markers (add small amount - self-awareness is good)
    UNCERTAINTY_MARKERS = {
        "might": 0.02,
        "possibly": 0.02,
        "uncertain": 0.03,
        "not sure": 0.02,
        "could be": 0.02,
        "appears to": 0.03,
    }

    # Overconfidence markers (subtract from score)
    OVERCONFIDENCE_MARKERS = {
        "definitely": -0.05,
        "absolutely": -0.05,
        "certainly": -0.03,
        "obviously": -0.05,
        "trivial": -0.08,
        "easy": -0.03,
    }

    def score(self, thought: str, observation: Optional[str] = None, code_executed: bool = False) -> ConfidenceScore:
        """
        Score confidence of a reasoning step.

        Args:
            thought: The agent's thinking/reflection
            observation: Execution observation if any
            code_executed: Whether code was executed

        Returns:
            ConfidenceScore with breakdown
        """
        thought_lower = thought.lower()
        factors = {}

        # Base score
        base = 0.5

        # Reasoning quality
        reasoning_score = 0.0
        for marker, value in self.POSITIVE_MARKERS.items():
            if marker in thought_lower:
                reasoning_score += value
                factors[f"positive_{marker}"] = value

        # Uncertainty awareness (self-awareness is valuable)
        uncertainty_score = 0.0
        for marker, value in self.UNCERTAINTY_MARKERS.items():
            if marker in thought_lower:
                uncertainty_score += value
                factors[f"uncertainty_{marker}"] = value

        # Overconfidence penalty
        for marker, value in self.OVERCONFIDENCE_MARKERS.items():
            if marker in thought_lower:
                reasoning_score += value  # value is negative
                factors[f"overconfidence_{marker}"] = value

        # Evidence from observation
        evidence_score = 0.0
        if observation:
            evidence_score += 0.15
            factors["has_observation"] = 0.15

            if "error" not in observation.lower():
                evidence_score += 0.10
                factors["no_error"] = 0.10

        # Code execution bonus
        if code_executed:
            evidence_score += 0.05
            factors["code_executed"] = 0.05

        # Calculate overall
        overall = base + reasoning_score + uncertainty_score + evidence_score
        overall = max(0.0, min(1.0, overall))

        return ConfidenceScore(
            overall=round(overall, 2),
            reasoning_quality=round(min(1.0, 0.5 + reasoning_score), 2),
            evidence_strength=round(min(1.0, evidence_score), 2),
            uncertainty_awareness=round(min(1.0, 0.5 + uncertainty_score), 2),
            factors=factors,
        )


# =============================================================================
# Planning Mode
# =============================================================================

PLANNING_MODE_TEMPLATE = """═══════════════════════════════════════════════════════════════
PLANNING MODE ACTIVE - DO NOT EXECUTE CODE
═══════════════════════════════════════════════════════════════

Task: {task}

═══════════════════════════════════════════════════════════════
REQUIRED OUTPUT FORMAT:
═══════════════════════════════════════════════════════════════

UNDERSTANDING:
<Restate the task in your own words to confirm understanding>

PLAN:
1. [Step 1 description]
   - Difficulty: Easy/Medium/Hard
   - Estimated time: Xs
   - Dependencies: None / Step N

2. [Step 2 description]
   - Difficulty: Easy/Medium/Hard
   - Estimated time: Xs
   - Dependencies: None / Step N

(Continue for all steps)

RISKS:
- [Risk 1]: [Mitigation strategy]
- [Risk 2]: [Mitigation strategy]

PREREQUISITES:
- [What must be true before starting]

SUCCESS_CRITERIA:
- [How to verify task is complete]

READY_TO_EXECUTE: YES / NO / NEED_CLARIFICATION

═══════════════════════════════════════════════════════════════
"""


@dataclass
class PlanStep:
    """Single step in execution plan."""

    number: int
    description: str
    difficulty: str  # Easy/Medium/Hard
    estimated_seconds: int
    dependencies: List[int]


@dataclass
class ExecutionPlan:
    """Parsed execution plan."""

    understanding: str
    steps: List[PlanStep]
    risks: List[Dict[str, str]]
    prerequisites: List[str]
    success_criteria: List[str]
    ready_to_execute: bool
    needs_clarification: bool = False


def generate_planning_prompt(task: str) -> str:
    """Generate planning mode prompt."""
    return PLANNING_MODE_TEMPLATE.format(task=task)


# =============================================================================
# Global instances
# =============================================================================

confidence_scorer = ConfidenceScorer()


def get_confidence_scorer() -> ConfidenceScorer:
    """Get global confidence scorer instance."""
    return confidence_scorer
