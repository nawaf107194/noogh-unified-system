import pytest

from gateway.app.core.capabilities import Capability, CapabilityRequirement
from gateway.app.core.policy_engine import PolicyEngine
from gateway.app.core.refusal import RefusalResponse


@pytest.fixture
def policy_engine():
    return PolicyEngine()


class TestPolicyRejectsInternet:
    def test_policy_rejects_internet(self, policy_engine):
        """Verify strict rejection of internet usage requests."""
        tasks = [
            "Execute download file from https://google.com",
            "Execute curl example.com",
            "Execute fetch data from api",
            "Execute scrape this website",
        ]

        for task in tasks:
            decision = PolicyEngine.decide(task)
            # PolicyEngine returns CapabilityRequirement with forbidden capabilities
            # instead of RefusalResponse for these cases
            assert isinstance(decision, (RefusalResponse, CapabilityRequirement))

            if isinstance(decision, CapabilityRequirement):
                # Should have INTERNET capability forbidden
                assert Capability.INTERNET in decision.forbidden
            elif isinstance(decision, RefusalResponse):
                assert decision.code == "ForbiddenRequest"
                assert "internet" in decision.message.lower() or "forbidden" in decision.message.lower()
