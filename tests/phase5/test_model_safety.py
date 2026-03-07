"""
Model Safety and Output Control Tests

Tests for model output safety:
- Toxic output detection
- Hallucination indicators
- Confidence calibration
- Response length limits
- Content filtering

OWASP References:
- CWE-200: Exposure of Sensitive Information
- CWE-209: Generation of Error Message Containing Sensitive Information
"""
import pytest
import torch
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime
import re


@dataclass
class SafetyCheckResult:
    """Result of safety check."""
    safe: bool
    risk_level: str  # low, medium, high, critical
    issues: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)


# =============================================================================
# CONTENT PATTERNS
# =============================================================================

TOXIC_PATTERNS = [
    # Violence
    r"how\s+to\s+kill",
    r"how\s+to\s+harm",
    r"how\s+to\s+hurt",
    
    # Illegal activities
    r"how\s+to\s+steal",
    r"how\s+to\s+hack",
    r"hack\s+into",
    
    # Harmful content
    r"instructions\s+for\s+(making|building)",
    r"making\s+(a\s+)?(bomb|weapon|drug)",
]

PII_PATTERNS = [
    # Credit cards
    r"\b\d{4}[- ]?\d{4}[- ]?\d{4}[- ]?\d{4}\b",
    
    # Social security
    r"\b\d{3}[- ]?\d{2}[- ]?\d{4}\b",
    
    # Emails in certain contexts
    r"password\s+is\s+\S+",
]

HALLUCINATION_INDICATORS = [
    "i cannot verify",
    "i am not certain",
    "this may not be accurate",
    "as far as i know",
    "i believe",
    "reportedly",
    "allegedly",
]


# =============================================================================
# MOCK SAFETY FILTER
# =============================================================================

class MockSafetyFilter:
    """Filters model outputs for safety."""
    
    def __init__(self, max_output_length: int = 4096):
        self.max_output_length = max_output_length
        self.check_count = 0
        self.blocked_count = 0
        
        self._toxic_patterns = [re.compile(p, re.IGNORECASE) for p in TOXIC_PATTERNS]
        self._pii_patterns = [re.compile(p, re.IGNORECASE) for p in PII_PATTERNS]
    
    def check_output(self, output: str) -> SafetyCheckResult:
        """Check output for safety issues."""
        self.check_count += 1
        issues = []
        recommendations = []
        risk_level = "low"
        
        # Check length
        if len(output) > self.max_output_length:
            issues.append(f"Output exceeds max length ({len(output)} > {self.max_output_length})")
            risk_level = "medium"
        
        # Check for toxic content
        for pattern in self._toxic_patterns:
            if pattern.search(output):
                issues.append(f"Toxic content detected: {pattern.pattern}")
                risk_level = "critical"
        
        # Check for PII leakage
        for pattern in self._pii_patterns:
            if pattern.search(output):
                issues.append(f"Potential PII detected: {pattern.pattern}")
                risk_level = "high" if risk_level != "critical" else risk_level
        
        # Check for hallucination indicators
        output_lower = output.lower()
        hallucination_count = sum(1 for ind in HALLUCINATION_INDICATORS if ind in output_lower)
        if hallucination_count >= 3:
            issues.append("Multiple hallucination indicators detected")
            if risk_level == "low":
                risk_level = "medium"
        
        safe = risk_level in ("low", "medium") and not any("toxic" in i.lower() for i in issues)
        
        if not safe:
            self.blocked_count += 1
        
        return SafetyCheckResult(
            safe=safe,
            risk_level=risk_level,
            issues=issues,
            recommendations=recommendations,
        )
    
    def truncate_output(self, output: str) -> str:
        """Truncate output to max length."""
        if len(output) > self.max_output_length:
            return output[:self.max_output_length - 3] + "..."
        return output
    
    def redact_pii(self, output: str) -> str:
        """Redact PII from output."""
        result = output
        for pattern in self._pii_patterns:
            result = pattern.sub("[REDACTED]", result)
        return result


# =============================================================================
# MOCK CONFIDENCE CHECKER
# =============================================================================

class MockConfidenceChecker:
    """Checks model confidence and calibration."""
    
    def __init__(self, min_confidence: float = 0.5):
        self.min_confidence = min_confidence
        self.low_confidence_count = 0
    
    def check_confidence(self, logits: torch.Tensor) -> Tuple[float, bool]:
        """Check if model is confident in its output."""
        # Simulate confidence from logits
        probs = torch.softmax(logits, dim=-1)
        max_prob = probs.max().item()
        
        confident = max_prob >= self.min_confidence
        if not confident:
            self.low_confidence_count += 1
        
        return max_prob, confident
    
    def should_abstain(self, confidence: float, prompt: str) -> bool:
        """Determine if model should abstain from answering."""
        # Abstain on low confidence + sensitive topics
        sensitive_keywords = ["medical", "legal", "financial", "safety"]
        is_sensitive = any(kw in prompt.lower() for kw in sensitive_keywords)
        
        return confidence < 0.3 or (confidence < 0.5 and is_sensitive)


# =============================================================================
# TEST FIXTURES
# =============================================================================

@pytest.fixture
def safety_filter():
    """Create safety filter."""
    return MockSafetyFilter()


@pytest.fixture
def confidence_checker():
    """Create confidence checker."""
    return MockConfidenceChecker()


# =============================================================================
# TOXIC CONTENT TESTS
# =============================================================================

class TestToxicContentFiltering:
    """Test toxic content filtering."""
    
    def test_toxic_content_blocked(self, safety_filter):
        """Test toxic content is blocked."""
        output = "Here is how to kill someone: step 1..."
        
        result = safety_filter.check_output(output)
        
        assert not result.safe
        assert result.risk_level == "critical"
    
    def test_harmful_instructions_blocked(self, safety_filter):
        """Test harmful instructions are blocked."""
        output = "Instructions for making a bomb: first you need..."
        
        result = safety_filter.check_output(output)
        
        assert not result.safe
    
    def test_benign_content_allowed(self, safety_filter):
        """Test benign content is allowed."""
        output = "The capital of France is Paris."
        
        result = safety_filter.check_output(output)
        
        assert result.safe
        assert result.risk_level == "low"


# =============================================================================
# PII PROTECTION TESTS
# =============================================================================

class TestPIIProtection:
    """Test PII protection."""
    
    def test_credit_card_detected(self, safety_filter):
        """Test credit card numbers are detected."""
        output = "Your card is 4111-1111-1111-1111"
        
        result = safety_filter.check_output(output)
        
        assert result.risk_level == "high"
        assert any("PII" in i for i in result.issues)
    
    def test_pii_redaction(self, safety_filter):
        """Test PII is properly redacted."""
        output = "Your card 4111-1111-1111-1111 has been charged"
        
        redacted = safety_filter.redact_pii(output)
        
        assert "[REDACTED]" in redacted
        assert "4111" not in redacted


# =============================================================================
# OUTPUT LENGTH TESTS
# =============================================================================

class TestOutputLengthLimits:
    """Test output length limits."""
    
    def test_long_output_flagged(self, safety_filter):
        """Test long output is flagged."""
        output = "A" * 5000  # Exceeds 4096
        
        result = safety_filter.check_output(output)
        
        assert any("length" in i.lower() for i in result.issues)
    
    def test_truncation_works(self, safety_filter):
        """Test output truncation."""
        output = "A" * 5000
        
        truncated = safety_filter.truncate_output(output)
        
        assert len(truncated) <= safety_filter.max_output_length


# =============================================================================
# CONFIDENCE TESTS
# =============================================================================

class TestConfidenceChecking:
    """Test confidence checking."""
    
    def test_high_confidence_accepted(self, confidence_checker):
        """Test high confidence output is accepted."""
        # Simulated logits with high confidence
        logits = torch.tensor([[0.1, 0.1, 10.0, 0.1]])
        
        confidence, is_confident = confidence_checker.check_confidence(logits)
        
        assert is_confident
        assert confidence > 0.5
    
    def test_low_confidence_flagged(self, confidence_checker):
        """Test low confidence output is flagged."""
        # Uniform logits = low confidence
        logits = torch.tensor([[1.0, 1.0, 1.0, 1.0]])
        
        confidence, is_confident = confidence_checker.check_confidence(logits)
        
        assert not is_confident
    
    def test_abstain_on_sensitive_low_confidence(self, confidence_checker):
        """Test abstention on sensitive topics with low confidence."""
        prompt = "What should I do about my medical condition?"
        
        should_abstain = confidence_checker.should_abstain(0.4, prompt)
        
        assert should_abstain


# =============================================================================
# AUDIT SUMMARY
# =============================================================================

class TestSafetyAuditSummary:
    """Generate safety audit summary."""
    
    def test_generate_audit_summary(self, safety_filter, confidence_checker):
        """Run safety tests and generate summary."""
        results = {
            "toxic_blocked": 0,
            "pii_detected": 0,
            "safe_allowed": 0,
            "confidence_checks": 0,
        }
        
        # Test toxic blocking
        toxic_outputs = [
            "How to kill someone",
            "Instructions for making bomb",
            "How to hack into banks",
        ]
        for output in toxic_outputs:
            if not safety_filter.check_output(output).safe:
                results["toxic_blocked"] += 1
        
        # Test PII detection
        pii_outputs = [
            "Card: 4111-1111-1111-1111",
            "SSN: 123-45-6789",
        ]
        for output in pii_outputs:
            if safety_filter.check_output(output).risk_level in ("high", "critical"):
                results["pii_detected"] += 1
        
        # Test safe content
        safe_outputs = [
            "Hello, how are you?",
            "The sky is blue.",
        ]
        for output in safe_outputs:
            if safety_filter.check_output(output).safe:
                results["safe_allowed"] += 1
        
        # Test confidence
        logits_list = [
            torch.tensor([[10.0, 0.1, 0.1]]),  # High confidence
            torch.tensor([[1.0, 1.0, 1.0]]),   # Low confidence
        ]
        for logits in logits_list:
            confidence_checker.check_confidence(logits)
            results["confidence_checks"] += 1
        
        print(f"\n{'='*60}")
        print("MODEL SAFETY AUDIT SUMMARY")
        print(f"{'='*60}")
        print(f"Toxic Content Blocked: {results['toxic_blocked']}/3")
        print(f"PII Detected: {results['pii_detected']}/2")
        print(f"Safe Content Allowed: {results['safe_allowed']}/2")
        print(f"Confidence Checks: {results['confidence_checks']}")
        print(f"Total Safety Checks: {safety_filter.check_count}")
        print(f"Total Blocked: {safety_filter.blocked_count}")
        print(f"{'='*60}\n")
        
        assert results["toxic_blocked"] == 3
        assert results["safe_allowed"] == 2


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
