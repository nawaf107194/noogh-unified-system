import pytest

from unified_core.evolution.agent_factory import AgentFactory

@pytest.fixture
def agent_factory():
    return AgentFactory()

def test_analyze_system_gaps_happy_path(agent_factory):
    # Arrange
    agent_factory._generated_agents = [
        {"role": "performance_profiler", "capabilities": ["PROFILE_CODE"]}
    ]
    
    # Act
    gaps = agent_factory.analyze_system_gaps()
    
    # Assert
    assert len(gaps) == 3
    assert any(need["role"] == "dependency_auditor" for need in gaps)
    assert any(need["role"] == "test_runner" for need in gaps)
    assert any(need["role"] == "backup_agent" for need in gaps)

def test_analyze_system_gaps_empty_generated_agents(agent_factory):
    # Arrange
    agent_factory._generated_agents = []
    
    # Act
    gaps = agent_factory.analyze_system_gaps()
    
    # Assert
    assert len(gaps) == 4

def test_analyze_system_gaps_existing_role(agent_factory):
    # Arrange
    agent_factory._generated_agents = [
        {"role": "performance_profiler", "capabilities": ["PROFILE_CODE"]}
    ]
    
    # Act
    gaps = agent_factory.analyze_system_gaps()
    
    # Assert
    assert len(gaps) == 3

def test_analyze_system_gaps_agent_file_exists(agent_factory, tmp_path):
    # Arrange
    agent_factory.agents_dir = tmp_path
    (tmp_path / "performance_profiler_agent.py").touch()
    agent_factory._generated_agents = []
    
    # Act
    gaps = agent_factory.analyze_system_gaps()
    
    # Assert
    assert len(gaps) == 3

def test_analyze_system_gaps_builtin_blueprint(agent_factory):
    # Arrange
    agent_factory.BUILTIN_BLUEPRINTS = {"performance_profiler"}
    agent_factory._generated_agents = []
    
    # Act
    gaps = agent_factory.analyze_system_gaps()
    
    # Assert
    assert len(gaps) == 3

def test_analyze_system_gaps_empty_system_needs(agent_factory):
    # Arrange
    agent_factory.system_needs = []
    agent_factory._generated_agents = []
    
    # Act
    gaps = agent_factory.analyze_system_gaps()
    
    # Assert
    assert len(gaps) == 0

def test_analyze_system_gaps_no_gaps(agent_factory):
    # Arrange
    agent_factory._generated_agents = [
        {"role": "performance_profiler", "capabilities": ["PROFILE_CODE"]},
        {"role": "dependency_auditor", "capabilities": ["AUDIT_DEPS"]},
        {"role": "test_runner", "capabilities": ["RUN_TESTS"]},
        {"role": "backup_agent", "capabilities": ["CREATE_BACKUP"]}
    ]
    
    # Act
    gaps = agent_factory.analyze_system_gaps()
    
    # Assert
    assert len(gaps) == 0

def test_analyze_system_gaps_no_agents_dir(agent_factory, monkeypatch):
    # Arrange
    monkeypatch.delattr(agent_factory, "agents_dir")
    agent_factory._generated_agents = []
    
    # Act
    gaps = agent_factory.analyze_system_gaps()
    
    # Assert
    assert len(gaps) == 0

def test_analyze_system_gaps_no_builtin_blueprints(agent_factory):
    # Arrange
    del agent_factory.BUILTIN_BLUEPRINTS
    agent_factory._generated_agents = []
    
    # Act
    gaps = agent_factory.analyze_system_gaps()
    
    # Assert
    assert len(gaps) == 4