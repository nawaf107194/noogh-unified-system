

from gateway.app.core.confidence import ConfidenceScorer


class TestConfidenceHighSimpleExec:
    def test_high_confidence_simple_exec(self):
        """
        Verify that a simple successful execution with sandbox usage yields HIGH confidence.
        Rules: Success=True, Iterations <= 3, Sandbox=True, Violations=False.
        """
        score = ConfidenceScorer.evaluate(
            success=True,
            iterations=2,
            has_protocol_violation=False,
            is_unsupported=False,
            executed_sandbox=True,
            mode="EXECUTE",
        )

        assert score is not None
        assert score.level == "HIGH"
        assert score.value >= 0.8
        assert "UNSAFE" not in score.level
