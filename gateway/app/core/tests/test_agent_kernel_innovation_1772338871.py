import pytest
from unittest.mock import Mock, defaultdict

class KernelConfig:
    pass  # Mock class for KernelConfig

@pytest.fixture
def mock_brain():
    return Mock()

@pytest.fixture
def mock_sandbox_service():
    return Mock()

def test_init_happy_path(mock_brain, mock_sandbox_service):
    config = KernelConfig()
    agent_kernel = AgentKernel(config=config, brain=mock_brain, sandbox_service=mock_sandbox_service)
    
    assert agent_kernel.config is config
    assert agent_kernel.brain is mock_brain
    assert agent_kernel.sandbox_service is mock_sandbox_service
    assert isinstance(agent_kernel.rate_limits, defaultdict)

def test_init_default_config(mock_brain, mock_sandbox_service):
    agent_kernel = AgentKernel(brain=mock_brain, sandbox_service=mock_sandbox_service)
    
    assert isinstance(agent_kernel.config, KernelConfig)
    assert agent_kernel.brain is mock_brain
    assert agent_kernel.sandbox_service is mock_sandbox_service
    assert isinstance(agent_kernel.rate_limits, defaultdict)

def test_init_empty_config(mock_brain, mock_sandbox_service):
    agent_kernel = AgentKernel(config=None, brain=mock_brain, sandbox_service=mock_sandbox_service)
    
    assert isinstance(agent_kernel.config, KernelConfig)
    assert agent_kernel.brain is mock_brain
    assert agent_kernel.sandbox_service is mock_sandbox_service
    assert isinstance(agent_kernel.rate_limits, defaultdict)

def test_init_none_config(mock_brain, mock_sandbox_service):
    agent_kernel = AgentKernel(config=None, brain=mock_brain, sandbox_service=mock_sandbox_service)
    
    assert isinstance(agent_kernel.config, KernelConfig)
    assert agent_kernel.brain is mock_brain
    assert agent_kernel.sandbox_service is mock_sandbox_service
    assert isinstance(agent_kernel.rate_limits, defaultdict)

def test_init_rate_limits(mock_brain, mock_sandbox_service):
    config = KernelConfig()
    agent_kernel = AgentKernel(config=config, brain=mock_brain, sandbox_service=mock_sandbox_service)
    
    assert len(agent_kernel.rate_limits) == 1
    assert 'default' in agent_kernel.rate_limits
    assert isinstance(agent_kernel.rate_limits['default'], dict)
    assert agent_kernel.rate_limits['default'] == {"count": 0, "reset": time.time() + 60}

def test_init_brain_none(mock_brain, mock_sandbox_service):
    config = KernelConfig()
    agent_kernel = AgentKernel(config=config, brain=None, sandbox_service=mock_sandbox_service)
    
    assert agent_kernel.brain is None
    assert isinstance(agent_kernel.rate_limits, defaultdict)

def test_init_sandbox_service_none(mock_brain, mock_sandbox_service):
    config = KernelConfig()
    agent_kernel = AgentKernel(config=config, brain=mock_brain, sandbox_service=None)
    
    assert agent_kernel.sandbox_service is None
    assert isinstance(agent_kernel.rate_limits, defaultdict)