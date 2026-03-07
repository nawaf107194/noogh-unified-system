# tools/tests/test_base.py

import pytest
from tools.utils import UtilityFacade, UtilityManager

@pytest.fixture
def utility_facade():
    """Fixture providing configured utility facade"""
    return UtilityFacade()

@pytest.fixture
def utility_manager():
    """Fixture providing configured utility manager"""
    return UtilityManager()

class BaseUtilsTest:
    """Base test class with common fixtures and setup"""
    
    @pytest.fixture(autouse=True)
    def setup(self, utility_facade, utility_manager):
        """Setup common resources"""
        self.facade = utility_facade
        self.manager = utility_manager
        
    def teardown_method(self, method):
        """Clean up resources after each test"""
        # Add any necessary cleanup logic here
        pass