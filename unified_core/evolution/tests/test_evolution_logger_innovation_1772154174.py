import pytest

class EvolutionLogger:
    def __init__(self, component: str = "evolution"):
        super().__init__()
        self.component = component

def test_init_happy_path():
    logger = EvolutionLogger("test_component")
    assert logger.component == "test_component"

def test_init_default_value():
    logger = EvolutionLogger()
    assert logger.component == "evolution"

def test_init_none_value():
    logger = EvolutionLogger(None)
    assert logger.component is None

def test_init_empty_string():
    logger = EvolutionLogger("")
    assert logger.component == ""

# Note: This test assumes that the code does not raise an exception for these cases.
# If it were to raise an exception, we would need to adjust the test accordingly.

if __name__ == "__main__":
    pytest.main()