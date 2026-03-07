import pytest
from noogh_unified_system.src.agents.noogh_orchestrator import NooghOrchestrator
from noogh_unified_system.src.systems.learning_system import LearningSystem
from noogh_unified_system.src.systems.monitoring_system import MonitoringSystem
from noogh_unified_system.src.systems.knowledge_synthesizer import KnowledgeSynthesizer

# Mock the DecisionEngine and StrategicGoalsSupervisor imports
class MockDecisionEngine:
    pass

class MockStrategicGoalsSupervisor:
    pass

def test_noogh_orchestrator_happy_path(mocker):
    # Mock the imports for DecisionEngine and StrategicGoalsSupervisor
    mocker.patch('noogh_unified_system.src.agents.noogh_orchestrator.DecisionEngine', new=MockDecisionEngine)
    mocker.patch('noogh_unified_system.src.agents.noogh_orchestrator.StrategicGoalsSupervisor', new=MockStrategicGoalsSupervisor)

    # Create an instance of NooghOrchestrator
    orchestrator = NooghOrchestrator()

    # Assert that the internal attributes are initialized correctly
    assert isinstance(orchestrator.learner, LearningSystem)
    assert isinstance(orchestrator.monitor, MonitoringSystem)
    assert isinstance(orchestrator.synthesizer, KnowledgeSynthesizer)
    assert isinstance(orchestrator.decision_engine, MockDecisionEngine)
    assert isinstance(orchestrator.strategy, MockStrategicGoalsSupervisor)

    # Assert that the cycle is initialized to 0
    assert orchestrator._cycle == 0

    # Assert that the logger calls are made
    mock_logger = mocker.patch('noogh_unified_system.src.agents.noogh_orchestrator.logger')
    mock_logger.info.assert_called_once_with("🤖 NOOGH Orchestrator initialized")
    mock_logger.info.assert_any_call("   Learn ←→ Monitor ←→ Agents ←→ Synthesis ←→ Strategy ←→ Action")

def test_noogh_orchestrator_decision_engine_not_found(mocker):
    # Mock the import for DecisionEngine to cause an ImportError
    mocker.patch('noogh_unified_system.src.agents.noogh_orchestrator.DecisionEngine', side_effect=ImportError)

    # Create an instance of NooghOrchestrator
    orchestrator = NooghOrchestrator()

    # Assert that the decision_engine is None
    assert orchestrator.decision_engine is None

    # Assert that the logger warning is made
    mock_logger = mocker.patch('noogh_unified_system.src.agents.noogh_orchestrator.logger')
    mock_logger.warning.assert_called_once_with("  ⚠️ DecisionEngine not found. Actions will not be executed.")

def test_noogh_orchestrator_strategic_goals_supervisor_not_found(mocker):
    # Mock the import for StrategicGoalsSupervisor to cause an ImportError
    mocker.patch('noogh_unified_system.src.agents.noogh_orchestrator.StrategicGoalsSupervisor', side_effect=ImportError)

    # Create an instance of NooghOrchestrator
    orchestrator = NooghOrchestrator()

    # Assert that the strategy is None
    assert orchestrator.strategy is None

    # Assert that the logger warning is made
    mock_logger = mocker.patch('noogh_unified_system.src.agents.noogh_orchestrator.logger')
    mock_logger.warning.assert_called_once_with("  ⚠️ StrategicGoalsSupervisor not found.")