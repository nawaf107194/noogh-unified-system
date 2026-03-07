import pytest
from docs.architecture import Architecture
from docs.config import Config

class TestArchitectureBase:
    @pytest.fixture
    def architecture(self):
        """Create a standard architecture instance for testing"""
        return Architecture()

    @pytest.fixture
    def config(self):
        """Provide access to configuration settings"""
        return Config.get_instance()

    def setup_class(self):
        """Setup any shared state before tests run"""
        pass  # Intentionally empty for now

    def teardown_class(self):
        """Cleanup after all tests have run"""
        pass  # Intentionally empty for now

    def test_basic_init(self, architecture):
        """Verify architecture initializes properly"""
        assert architecture is not None
        assert hasattr(architecture, 'components')