import pytest
from unified_core.orchestration.risk_policy import RiskPolicy, RiskLevel

class TestRiskPolicy:

    def test_classify_tool_happy_path(self):
        assert RiskPolicy.classify_tool('git') == RiskLevel.SAFE
        assert RiskPolicy.classify_tool('aws-cli') == RiskLevel.RESTRICTED
        assert RiskPolicy.classify_tool('rm') == RiskLevel.DANGEROUS

    def test_classify_tool_edge_cases(self):
        assert RiskPolicy.classify_tool(None) == RiskLevel.DANGEROUS
        assert RiskPolicy.classify_tool('') == RiskLevel.DANGEROUS
        assert RiskPolicy.classify_tool('unknown_tool') == RiskLevel.DANGEROUS

    def test_classify_tool_error_cases(self):
        # This function does not raise exceptions, so no need to test for errors here.
        pass

    async def test_classify_tool_async_behavior(self):
        # Since the classify_tool method is synchronous, there's no async behavior to test here.
        pass