
from gateway.app.core.confidence import ConfidenceScorer


class TestConfidenceDeterministicRepeatability:
    def test_confidence_deterministic_repeatability(self):
        """
        Verify that the scoring function is 100% deterministic (Pure Function).
        Same inputs => Same outputs.
        """

        args = {
            "success": True,
            "iterations": 4,  # Just above threshold
            "has_protocol_violation": False,
            "is_unsupported": False,
            "executed_sandbox": True,
            "mode": "EXECUTE",
        }

        score1 = ConfidenceScorer.evaluate(**args)

        for _ in range(10):
            score_n = ConfidenceScorer.evaluate(**args)
            assert score_n == score1
            assert score_n.value == score1.value
            assert score_n.level == score1.level
