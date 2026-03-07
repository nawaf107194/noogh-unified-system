import pytest

def test_get_fabric_happy_path(mocker):
    from unified_core.core.neuron_fabric import get_neuron_fabric
    mock_fabric = mocker.patch('unified_core.core.neuron_fabric.get_neuron_fabric')
    mock_fabric.return_value = {'_neurons': [1, 2, 3]}
    
    neuron_learning_instance = NeuronLearning()
    fabric = neuron_learning_instance._get_fabric()
    
    assert fabric == {'_neurons': [1, 2, 3]}
    logger.info.assert_called_once_with("🧬 NeuronFabric connected: 3 neurons")
    mock_fabric.assert_called_once()

def test_get_fabric_empty_neuron_fabric(mocker):
    from unified_core.core.neuron_fabric import get_neuron_fabric
    mock_fabric = mocker.patch('unified_core.core.neuron_fabric.get_neuron_fabric')
    mock_fabric.return_value = {'_neurons': []}
    
    neuron_learning_instance = NeuronLearning()
    fabric = neuron_learning_instance._get_fabric()
    
    assert fabric == {'_neurons': []}
    logger.info.assert_called_once_with("🧬 NeuronFabric connected: 0 neurons")
    mock_fabric.assert_called_once()

def test_get_fabric_exception(mocker):
    from unified_core.core.neuron_fabric import get_neuron_fabric
    mock_fabric = mocker.patch('unified_core.core.neuron_fabric.get_neuron_fabric')
    mock_fabric.side_effect = Exception("Some error occurred")
    
    neuron_learning_instance = NeuronLearning()
    fabric = neuron_learning_instance._get_fabric()
    
    assert fabric is None
    logger.warning.assert_called_once_with("NeuronFabric not available: Some error occurred")
    mock_fabric.assert_called_once()

class NeuronLearning:
    def __init__(self):
        self._fabric = None
    
    def _get_fabric(self):
        """Lazy-load NeuronFabric to avoid circular imports."""
        if self._fabric is None:
            try:
                from unified_core.core.neuron_fabric import get_neuron_fabric
                self._fabric = get_neuron_fabric()
                logger.info(f"🧬 NeuronFabric connected: {len(self._fabric._neurons)} neurons")
            except Exception as e:
                logger.warning(f"NeuronFabric not available: {e}")
        return self._fabric

# Mock the logger
logger = mocker.patch('unified_core.evolution.neuron_learning.logger')