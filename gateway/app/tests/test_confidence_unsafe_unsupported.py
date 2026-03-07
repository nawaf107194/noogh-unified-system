
from gateway.app.core.confidence import ConfidenceScorer


class TestConfidenceUnsafeUnsupported:
    def test_unsafe_unsupported(self):
        """
        Verify that UNSUPPORTED result forces UNSAFE level.
        Reference: "أي UNSUPPORTED ⇒ UNSAFE"
        """
        score = ConfidenceScorer.evaluate(
            success=False,
            iterations=1,
            has_protocol_violation=False,
            is_unsupported=True,
            executed_sandbox=False,
            mode="EXECUTE",
        )

        assert score is not None
        assert score.level == "UNSAFE"
        assert score.value == 0.0
