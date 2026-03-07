
from gateway.app.core.policy_engine import PolicyEngine
from gateway.app.core.refusal import RefusalResponse


class TestRefusalAlternatives:
    def test_refusal_contains_alternatives(self):
        """Verify refusal response includes helpful alternatives."""
        task = "run shell command"
        decision = PolicyEngine.decide(task)
        assert isinstance(decision, RefusalResponse)
        assert decision.allowed_alternatives is not None
        assert len(decision.allowed_alternatives) > 0
        assert isinstance(decision.allowed_alternatives[0], str)
