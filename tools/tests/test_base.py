# tools/tests/test_base.py
class BaseTestUtils:
    def setup_method(self):
        # Common setup logic
        self.test_config = {
            "db_connection": "test_db",
            "api_key": "test_key"
        }
        
    def teardown_method(self):
        # Common teardown logic
        pass
    
    def get_test_config(self):
        return self.test_config.copy()