import pytest

from src.scripts.agent_health_checker import AgentHealthChecker, main

class MockAgentHealthChecker(AgentHealthChecker):
    def check_all_agents(self):
        return {"agent1": "healthy", "agent2": "healthy"}

    def print_summary(self):
        pass

    def save_report(self):
        pass

def test_main_happy_path(mocker, capsys):
    # Create a mock instance of AgentHealthChecker
    mocker.patch('src.scripts.agent_health_checker.AgentHealthChecker', new=MockAgentHealthChecker)

    main()

    captured = capsys.readouterr()
    assert "🔧 NOOGH Agent Health Checker" in captured.out
    assert "agent1: healthy" in captured.out
    assert "agent2: healthy" in captured.out

def test_main_edge_case(mocker, capsys):
    # Mock an edge case where check_all_agents returns empty results
    class EdgeCaseMockAgentHealthChecker(AgentHealthChecker):
        def check_all_agents(self):
            return {}

    mocker.patch('src.scripts.agent_health_checker.AgentHealthChecker', new=EdgeCaseMockAgentHealthChecker)

    main()

    captured = capsys.readouterr()
    assert "🔧 NOOGH Agent Health Checker" in captured.out
    assert "No agents to check." in captured.out

def test_main_error_case(mocker):
    # Mock an error case where check_all_agents raises an exception
    class ErrorCaseMockAgentHealthChecker(AgentHealthChecker):
        def check_all_agents(self):
            raise ValueError("Failed to check agents")

    mocker.patch('src.scripts.agent_health_checker.AgentHealthChecker', new=ErrorCaseMockAgentHealthChecker)

    with pytest.raises(SystemExit) as exc_info:
        main()

    assert exc_info.type is SystemExit
    assert exc_info.value.code != 0

def test_main_async_behavior(mocker):
    # Mock an async behavior where check_all_agents returns a coroutine
    class AsyncMockAgentHealthChecker(AgentHealthChecker):
        async def check_all_agents(self):
            return {"agent1": "healthy", "agent2": "healthy"}

    mocker.patch('src.scripts.agent_health_checker.AgentHealthChecker', new=AsyncMockAgentHealthChecker)

    with pytest.raises(NotImplementedError) as exc_info:
        main()

    assert str(exc_info.value) == "Async behavior not supported in this test setup."