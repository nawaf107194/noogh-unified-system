import pytest
from unittest.mock import patch, MagicMock

from unified_core.tools_hub import ToolsHub

class TestToolsHub:
    @pytest.fixture
    def tools_hub(self):
        return ToolsHub()

    @pytest.mark.parametrize("platform_dir", [None, "", "nonexistent"])
    def test_get_architecture_insights_empty_platform_dir(self, tools_hub, platform_dir):
        with patch.object(tools_hub, "_platform_dir", platform_dir):
            insights = tools_hub.get_architecture_insights()
            assert isinstance(insights, dict)
            assert "goal_decomposition" in insights
            assert "memory_management" in insights
            assert "self_feedback" in insights
            assert "plugin_system" in insights
            assert "command_registry" in insights
            assert "platform_components" not in insights

    @pytest.mark.parametrize("platform_dir", ["/tmp/platform"])
    def test_get_architecture_insights_with_platform_dir(self, tools_hub, platform_dir):
        with patch.object(tools_hub, "_platform_dir", MagicMock(return_value=MagicMock(exists=True))):
            with patch.object(platform_dir, "iterdir", return_value=[MagicMock(name="component1"), MagicMock(name="component2")]):
                insights = tools_hub.get_architecture_insights()
                assert isinstance(insights, dict)
                assert "goal_decomposition" in insights
                assert "memory_management" in insights
                assert "self_feedback" in insights
                assert "plugin_system" in insights
                assert "command_registry" in insights
                assert "platform_components" in insights
                assert insights["platform_components"] == ["component1", "component2"]

    def test_get_architecture_insights_no_platform_dir(self, tools_hub):
        with patch.object(tools_hub, "_platform_dir", MagicMock(return_value=None)):
            insights = tools_hub.get_architecture_insights()
            assert isinstance(insights, dict)
            assert "goal_decomposition" in insights
            assert "memory_management" in insights
            assert "self_feedback" in insights
            assert "plugin_system" in insights
            assert "command_registry" in insights
            assert "platform_components" not in insights

    def test_get_architecture_insights_empty_platform_dir_with_no_components(self, tools_hub):
        with patch.object(tools_hub, "_platform_dir", MagicMock(return_value=MagicMock(exists=True))):
            with patch.object(platform_dir, "iterdir", return_value=[]):
                insights = tools_hub.get_architecture_insights()
                assert isinstance(insights, dict)
                assert "goal_decomposition" in insights
                assert "memory_management" in insights
                assert "self_feedback" in insights
                assert "plugin_system" in insights
                assert "command_registry" in insights
                assert "platform_components" in insights
                assert insights["platform_components"] == []

    def test_get_architecture_insights_with_async_behavior(self, tools_hub):
        async def mock_platform_dir_exists():
            return True

        async def mock_iterdir():
            yield MagicMock(name="component1")
            yield MagicMock(name="component2")

        with patch.object(tools_hub, "_platform_dir", new_callable=MagicMock):
            tools_hub._platform_dir.exists = mock_platform_dir_exists
            tools_hub._platform_dir.iterdir = mock_iterdir

        insights = tools_hub.get_architecture_insights()
        assert isinstance(insights, dict)
        assert "goal_decomposition" in insights
        assert "memory_management" in insights
        assert "self_feedback" in insights
        assert "plugin_system" in insights
        assert "command_registry" in insights
        assert "platform_components" in insights
        assert insights["platform_components"] == ["component1", "component2"]

    def test_get_architecture_insights_with_invalid_inputs(self, tools_hub):
        invalid_inputs = [None, {}, [], 123]
        for input_value in invalid_inputs:
            with patch.object(tools_hub, "_platform_dir", new=input_value):
                insights = tools_hub.get_architecture_insights()
                assert isinstance(insights, dict)
                assert "goal_decomposition" in insights
                assert "memory_management" in insights
                assert "self_feedback" in insights
                assert "plugin_system" in insights
                assert "command_registry" in insights
                assert "platform_components" not in insights