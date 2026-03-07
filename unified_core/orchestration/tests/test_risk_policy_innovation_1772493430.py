import pytest

from unified_core.orchestration.risk_policy import classify_tool, RiskLevel

class TestClassifyTool:

    def test_happy_path(self):
        assert classify_tool("git") == RiskLevel.SAFE
        assert classify_tool("kubectl") == RiskLevel.RESTRICTED
        assert classify_tool("rm") == RiskLevel.DANGEROUS

    @pytest.mark.parametrize(
        "tool_name",
        [
            "",
            None,
            [],
            {},
            (),
            set(),
            123,
            True,
            False,
        ],
    )
    def test_edge_cases(self, tool_name):
        assert classify_tool(tool_name) == RiskLevel.DANGEROUS

    @pytest.mark.parametrize(
        "tool_name",
        [
            "unknown_tool",
            "not_a_real_command",
        ],
    )
    def test_error_cases(self, tool_name):
        assert classify_tool(tool_name) == RiskLevel.DANGEROUS