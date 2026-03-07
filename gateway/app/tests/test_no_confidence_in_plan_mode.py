
from gateway.app.core.confidence import ConfidenceScorer


class TestNoConfidenceInPlanMode:
    def test_no_confidence_in_plan_mode(self):
        """
        Verify that Planning Mode returns NO confidence score.
        Reference: "Planning Mode: ❌ لا Confidence"
        """
        score = ConfidenceScorer.evaluate(
            success=True,
            iterations=1,
            has_protocol_violation=False,
            is_unsupported=False,
            executed_sandbox=False,  # Plans don't execute
            mode="PLAN",
        )

        assert score is None
