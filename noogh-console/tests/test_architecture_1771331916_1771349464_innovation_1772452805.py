import pytest

class GPUInfoStrategy:
    pass

class NooghConsole:
    def __init__(self):
        self._strategy = None

    def strategy(self, strategy: GPUInfoStrategy):
        self._strategy = strategy

def test_strategy_happy_path():
    console = NooghConsole()
    mock_strategy = GPUInfoStrategy()
    console.strategy(mock_strategy)
    assert console._strategy == mock_strategy

def test_strategy_edge_case_none():
    console = NooghConsole()
    console.strategy(None)
    assert console._strategy is None

def test_strategy_edge_case_empty():
    # Assuming an empty strategy is valid
    class EmptyStrategy(GPUInfoStrategy):
        pass
    
    console = NooghConsole()
    mock_strategy = EmptyStrategy()
    console.strategy(mock_strategy)
    assert console._strategy == mock_strategy

def test_strategy_error_case_invalid_input():
    console = NooghConsole()
    with pytest.raises(TypeError):
        console.strategy(123)  # Assuming int is not a valid strategy type