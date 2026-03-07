import pytest

from agents.web_researcher_agent import WebResearcherAgent

class TestWebResearcherAgentHandleEndtag:

    @pytest.fixture
    def agent(self):
        return WebResearcherAgent()

    def test_happy_path(self, agent):
        agent.SKIP_TAGS = {'a', 'p'}
        agent._skip_depth = 2
        
        agent.handle_endtag('A')
        
        assert agent._skip_depth == 1

    def test_edge_case_empty_tag(self, agent):
        agent.SKIP_TAGS = {'a', 'p'}
        agent._skip_depth = 2
        
        agent.handle_endtag('')
        
        assert agent._skip_depth == 0

    def test_edge_case_none_tag(self, agent):
        agent.SKIP_TAGS = {'a', 'p'}
        agent._skip_depth = 2
        
        agent.handle_endtag(None)
        
        assert agent._skip_depth == 0

    def test_edge_case_boundary_skip_depth_zero(self, agent):
        agent.SKIP_TAGS = {'a', 'p'}
        agent._skip_depth = 1
        
        agent.handle_endtag('A')
        
        assert agent._skip_depth == 0

    def test_error_case_invalid_tag_type(self, agent):
        with pytest.raises(TypeError):
            agent.handle_endtag(123)

    async def test_async_behavior_no_change(self, agent):
        agent.SKIP_TAGS = {'a', 'p'}
        agent._skip_depth = 2
        
        await agent.handle_endtag('A')
        
        assert agent._skip_depth == 1