import unittest
import sys
from unified_core.core.config_manager import ConfigManager

class TestHarness:
    def __init__(self):
        self.tests = []
        self.config = ConfigManager.get_instance()
        
    def discover_tests(self, start_dir=None):
        """Discover all test cases in the module"""
        if not start_dir:
            start_dir = 'trading'
        loader = unittest.TestLoader()
        self.tests = loader.discover(start_dir, pattern='test_*.py')
        
    def run_tests(self):
        """Run all discovered tests"""
        runner = unittest.TextTestRunner(verbosity=2)
        result = runner.run(self.tests)
        return result
        
    def verify_real_data_connections(self):
        """Ensure tests are using real data sources"""
        # This could be expanded to check environment variables or config settings
        assert self.config.get('use_real_data'), "Tests must use real data connections"
        
if __name__ == '__main__':
    harness = TestHarness()
    harness.discover_tests()
    harness.verify_real_data_connections()
    result = harness.run_tests()
    sys.exit(0 if result.wasSuccessful() else 1)