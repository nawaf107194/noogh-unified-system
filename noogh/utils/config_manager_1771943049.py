# noogh/utils/tests/test_config_manager.py

import unittest
from noogh.utils.config_manager import ConfigManager

class TestConfigManager(unittest.TestCase):
    def test_load_config(self):
        config_manager = ConfigManager.get_instance()
        self.assertTrue(config_manager.config_data)

    def test_update_config(self):
        config_manager = ConfigManager.get_instance()
        old_value = config_manager.config_data['key']
        new_value = 'new_value'
        config_manager.update_config('key', new_value)
        updated_value = config_manager.get_config()['key']
        self.assertEqual(updated_value, new_value)
        config_manager.update_config('key', old_value)  # Reset to original value

if __name__ == '__main__':
    unittest.main()