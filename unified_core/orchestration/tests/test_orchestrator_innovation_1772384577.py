import pytest

def test_register_agent_happy_path():
    from unified_core.agent import AgentRole
    from unified_core.orchestration.orchestrator import Orchestrator
    logger = mock.MagicMock()
    orchestrator = Orchestrator(logger)
    
    def callback():
        pass
    
    orchestrator.register_agent(AgentRole.WORKER, callback)
    assert orchestrator._agents == {AgentRole.WORKER: callback}
    orchestrator.bus.subscribe.assert_called_once_with("agent:WORKER", callback)
    logger.info.assert_called_once_with("Registered agent: WORKER")

def test_register_agent_none_role():
    from unified_core.agent import AgentRole
    from unified_core.orchestration.orchestrator import Orchestrator
    logger = mock.MagicMock()
    orchestrator = Orchestrator(logger)
    
    def callback():
        pass
    
    orchestrator.register_agent(None, callback)
    assert orchestrator._agents == {}
    orchestrator.bus.subscribe.assert_not_called()
    logger.info.assert_not_called()

def test_register_agent_empty_role():
    from unified_core.agent import AgentRole
    from unified_core.orchestration.orchestrator import Orchestrator
    logger = mock.MagicMock()
    orchestrator = Orchestrator(logger)
    
    def callback():
        pass
    
    with pytest.raises(ValueError):
        orchestrator.register_agent("", callback)

def test_register_agent_invalid_role():
    from unified_core.agent import AgentRole
    from unified_core.orchestration.orchestrator import Orchestrator
    logger = mock.MagicMock()
    orchestrator = Orchestrator(logger)
    
    def callback():
        pass
    
    with pytest.raises(ValueError):
        orchestrator.register_agent(AgentRole("INVALID"), callback)

def test_register_agent_none_callback():
    from unified_core.agent import AgentRole
    from unified_core.orchestration.orchestrator import Orchestrator
    logger = mock.MagicMock()
    orchestrator = Orchestrator(logger)
    
    with pytest.raises(ValueError):
        orchestrator.register_agent(AgentRole.WORKER, None)

def test_register_agent_empty_callback():
    from unified_core.agent import AgentRole
    from unified_core.orchestration.orchestrator import Orchestrator
    logger = mock.MagicMock()
    orchestrator = Orchestrator(logger)
    
    def callback():
        pass
    
    with pytest.raises(ValueError):
        orchestrator.register_agent(AgentRole.WORKER, "")

def test_register_agent_async_behavior():
    from unified_core.agent import AgentRole
    from unified_core.orchestration.orchestrator import Orchestrator
    logger = mock.MagicMock()
    orchestrator = Orchestrator(logger)
    
    async def callback():
        pass
    
    with pytest.raises(TypeError):
        orchestrator.register_agent(AgentRole.WORKER, callback)

if __name__ == "__main__":
    pytest.main()