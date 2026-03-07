import pytest

class TestCreativeAgent:
    def test_set_evolution_memory_happy_path(self):
        agent = CreativeAgent()
        memory = "Test Memory"
        result = agent.set_evolution_memory(memory)
        assert agent._evolution_memory == memory
        assert result is None

    def test_set_evolution_memory_edge_case_none(self):
        agent = CreativeAgent()
        memory = None
        result = agent.set_evolution_memory(memory)
        assert agent._evolution_memory is None
        assert result is None

    def test_set_evolution_memory_edge_case_empty_string(self):
        agent = CreativeAgent()
        memory = ""
        result = agent.set_evolution_memory(memory)
        assert agent._evolution_memory == memory
        assert result is None

    def test_set_evolution_memory_error_case_invalid_type(self):
        agent = CreativeAgent()
        with pytest.raises(TypeError):
            agent.set_evolution_memory(123)

class CreativeAgent:
    def __init__(self):
        self._evolution_memory = None

    def set_evolution_memory(self, mem):
        if not isinstance(mem, str):
            raise TypeError("Expected a string for memory")
        self._evolution_memory = mem