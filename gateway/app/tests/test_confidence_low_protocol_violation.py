
from gateway.app.core.confidence import ConfidenceScorer


class TestConfidenceLowProtocolViolation:
    def test_low_confidence_protocol_violation(self):
        """
        Verify that ANY protocol violation forces LOW confidence (or lower).
        Reference: "أي ProtocolViolation ⇒ LOW"
        """
        score = ConfidenceScorer.evaluate(
            success=True,
            iterations=2,
            has_protocol_violation=True,  # VIOLATION!
            is_unsupported=False,
            executed_sandbox=True,
            mode="EXECUTE",
        )

        assert score is not None
        assert score.level == "LOW"
        assert score.value <= 0.6  # Penalty is 0.4, so max 0.6
        assert "Protocol violation detected" in str(score.reasons)
