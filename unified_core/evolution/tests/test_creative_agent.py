import pytest

class TestCreativeAgentInit:

    @pytest.fixture
    def creative_agent(self):
        from unified_core.evolution.creative_agent import CreativeAgent
        return CreativeAgent

    def test_happy_path(self, creative_agent):
        """Test with normal inputs."""
        agent = creative_agent(world_model="some_model")
        assert agent._world_model == "some_model"
        assert agent._cooldown == 600.0

    def test_none_world_model(self, creative_agent):
        """Test with None as world model input."""
        agent = creative_agent(world_model=None)
        assert agent._world_model is None
        assert agent._cooldown == 600.0

    def test_empty_world_model(self, creative_agent):
        """Test with an empty string as world model input."""
        agent = creative_agent(world_model="")
        assert agent._world_model == ""
        assert agent._cooldown == 600.0

    def test_invalid_world_model_type(self, creative_agent):
        """Test with invalid type for world model input."""
        with pytest.raises(TypeError):
            creative_agent(world_model=123)

    def test_cooldown_override(self, creative_agent):
        """Test if cooldown can be overridden through inheritance or class method."""
        class CustomAgent(creative_agent):
            def __init__(self, *args, **kwargs):
                super().__init__(*args, **kwargs)
                self._cooldown = 300.0  # Override cooldown

        custom_agent = CustomAgent(world_model="some_model")
        assert custom_agent._cooldown == 300.0

    def test_async_behavior(self, creative_agent):
        """Test asynchronous behavior if applicable (assuming no async behavior in init)."""
        assert hasattr(creative_agent.__init__, "__await__") is False